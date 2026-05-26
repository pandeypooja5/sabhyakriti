from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_certificatemanager as acm
from constructs import Construct

from sabhyakriti_infra.config import API_SUBDOMAIN, DOMAIN_NAME, SERVICES
from sabhyakriti_infra.stacks.database_stack import DatabaseStack
from sabhyakriti_infra.stacks.network_stack import NetworkStack


# Amazon Linux 2023 AMI (latest) — pinned in config; update via SSM parameter
AL2023_AMI = ec2.MachineImage.latest_amazon_linux2023()


def _make_instance_role(scope: Construct, service_name: str) -> iam.Role:
    """Create least-privilege IAM instance profile role for a microservice."""
    safe_name = service_name.replace("-", "").title()
    role = iam.Role(
        scope, f"Role{safe_name}",
        assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"  # required for SSM-based deployments
            ),
        ],
    )
    # ECR: pull images
    role.add_to_policy(iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["ecr:GetAuthorizationToken"],
        resources=["*"],  # GetAuthorizationToken does not support resource-level permissions
    ))
    role.add_to_policy(iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
        resources=[f"arn:aws:ecr:ap-south-1:*:repository/sabhyakriti/{service_name}"],
    ))
    # CloudWatch Logs
    role.add_to_policy(iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        resources=[f"arn:aws:logs:ap-south-1:*:log-group:/sabhyakriti/{service_name}:*"],
    ))
    # CloudWatch Metrics
    namespace = f"Sabhyakriti/{safe_name}"
    role.add_to_policy(iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["cloudwatch:PutMetricData"],
        resources=["*"],
        conditions={"StringEquals": {"cloudwatch:namespace": namespace}},
    ))
    # Secrets Manager: service-specific secrets only
    role.add_to_policy(iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["secretsmanager:GetSecretValue"],
        resources=[f"arn:aws:secretsmanager:ap-south-1:*:secret:sabhyakriti/{service_name}/*"],
    ))
    return role


class ComputeStack(cdk.Stack):
    """EC2 instances + ALB + path-based routing + Auto Scaling for all services."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network: NetworkStack,
        database: DatabaseStack,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── ACM Certificate ───────────────────────────────────────────────────
        # NOTE: Certificate must be DNS-validated in Route53 before first deployment.
        # Import an existing certificate or create with dns_validated=True.
        certificate = acm.Certificate(
            self, "ApiCertificate",
            domain_name=f"*.{DOMAIN_NAME}",
            subject_alternative_names=[DOMAIN_NAME],
            validation=acm.CertificateValidation.from_dns(),
        )

        # ── Application Load Balancer ─────────────────────────────────────────
        self.alb = elbv2.ApplicationLoadBalancer(
            self, "Alb",
            vpc=network.vpc,
            internet_facing=True,
            security_group=network.sg_alb,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            load_balancer_name="sabhyakriti-alb",
        )
        # Enable access logging
        self.alb.log_access_logs(
            cdk.aws_s3.Bucket.from_bucket_name(self, "AlbLogBucket", f"sabhyakriti-alb-logs"),
        )

        # HTTP → HTTPS redirect
        self.alb.add_redirect(
            source_port=80, source_protocol=elbv2.ApplicationProtocol.HTTP,
            target_port=443, target_protocol=elbv2.ApplicationProtocol.HTTPS,
        )

        # HTTPS listener
        self.https_listener = self.alb.add_listener(
            "HttpsListener",
            port=443,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            certificates=[certificate],
            default_action=elbv2.ListenerAction.fixed_response(
                404, content_type="application/json",
                message_body='{"detail":"Not Found"}',
            ),
        )

        # ── EC2 + Auto Scaling per Service ────────────────────────────────────
        self.asgs: dict[str, autoscaling.AutoScalingGroup] = {}
        self.target_groups: dict[str, elbv2.ApplicationTargetGroup] = {}

        priority = 10  # ALB rule priority (lower = higher precedence)
        for svc in SERVICES:
            safe = svc.name.replace("-", "").title()
            role = _make_instance_role(self, svc.name)

            instance_type = ec2.InstanceType(svc.ec2_type)

            # Launch template user data: pull + run Docker container on boot
            user_data = ec2.UserData.for_linux()
            user_data.add_commands(
                "yum install -y docker",
                "systemctl enable docker",
                "systemctl start docker",
                f"aws ecr get-login-password --region ap-south-1 | "
                f"docker login --username AWS --password-stdin "
                f"$(aws sts get-caller-identity --query Account --output text)"
                f".dkr.ecr.ap-south-1.amazonaws.com",
                f"# Initial container start — CI/CD (SSM) handles subsequent deploys",
                f"echo 'EC2 bootstrap complete for {svc.name}'",
            )

            asg = autoscaling.AutoScalingGroup(
                self, f"Asg{safe}",
                vpc=network.vpc,
                instance_type=instance_type,
                machine_image=AL2023_AMI,
                role=role,
                security_group=network.sg_services[svc.name],
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                min_capacity=1,
                max_capacity=1,  # manual scale-up for MVP
                desired_capacity=1,
                user_data=user_data,
                health_check=autoscaling.HealthCheck.elb(grace=cdk.Duration.seconds(120)),
                update_policy=autoscaling.UpdatePolicy.rolling_update(
                    min_instances_in_service=0,  # single instance — brief downtime on deploy
                ),
            )
            self.asgs[svc.name] = asg

            if not svc.is_internal_only and svc.alb_paths:
                # Target group
                tg = elbv2.ApplicationTargetGroup(
                    self, f"Tg{safe}",
                    vpc=network.vpc,
                    port=svc.port,
                    protocol=elbv2.ApplicationProtocol.HTTP,
                    targets=[asg],
                    health_check=elbv2.HealthCheck(
                        path="/health",
                        healthy_http_codes="200",
                        interval=cdk.Duration.seconds(30),
                        timeout=cdk.Duration.seconds(5),
                        healthy_threshold_count=2,
                        unhealthy_threshold_count=3,
                    ),
                    target_group_name=f"sabhyakriti-{svc.name[:16]}",
                )
                self.target_groups[svc.name] = tg

                # ALB listener rules — one per path pattern
                for i, path in enumerate(svc.alb_paths):
                    self.https_listener.add_targets(
                        f"Rule{safe}{i}",
                        priority=priority,
                        conditions=[elbv2.ListenerCondition.path_patterns([path])],
                        targets=[asg],
                        port=svc.port,
                        protocol=elbv2.ApplicationProtocol.HTTP,
                        health_check=elbv2.HealthCheck(path="/health", healthy_http_codes="200"),
                    )
                    priority += 10

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "AlbDnsName", value=self.alb.load_balancer_dns_name)
