from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
from constructs import Construct

from sabhyakriti_infra.config import SERVICES, VPC_CIDR


class NetworkStack(cdk.Stack):
    """VPC, subnets (2 AZs), NAT gateway, and all security groups."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── VPC ──────────────────────────────────────────────────────────────
        self.vpc = ec2.Vpc(
            self, "SabhyakritiVpc",
            ip_addresses=ec2.IpAddresses.cidr(VPC_CIDR),
            max_azs=2,
            nat_gateways=1,  # single NAT to save cost for MVP
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24
                ),
            ],
        )

        # ── Security Groups ───────────────────────────────────────────────────

        # ALB: public-facing, accepts HTTPS from anywhere
        self.sg_alb = ec2.SecurityGroup(
            self, "SgAlb",
            vpc=self.vpc,
            description="ALB — public HTTPS inbound",
            allow_all_outbound=False,
        )
        self.sg_alb.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "HTTPS from internet")
        self.sg_alb.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP redirect")

        # Per-service security groups (EC2 instances — private subnet)
        self.sg_services: dict[str, ec2.SecurityGroup] = {}
        for svc in SERVICES:
            sg = ec2.SecurityGroup(
                self, f"Sg{svc.name.replace('-', '').title()}",
                vpc=self.vpc,
                description=f"{svc.name} EC2 instances",
                allow_all_outbound=True,  # services call external APIs
            )
            # Allow ALB → service port (all services, even internal-only — ALB doesn't route but SSM does)
            sg.add_ingress_rule(self.sg_alb, ec2.Port.tcp(svc.port), f"ALB → {svc.name}")
            # Allow service → service (internal VPC communication)
            sg.add_ingress_rule(ec2.Peer.ipv4(VPC_CIDR), ec2.Port.tcp(svc.port), "VPC internal")
            self.sg_services[svc.name] = sg

        # RDS: accepts connections from all service security groups
        self.sg_rds = ec2.SecurityGroup(
            self, "SgRds",
            vpc=self.vpc,
            description="RDS PostgreSQL",
            allow_all_outbound=False,
        )
        for svc in SERVICES:
            self.sg_rds.add_ingress_rule(
                self.sg_services[svc.name],
                ec2.Port.tcp(5432),
                f"{svc.name} → RDS",
            )

        # ElastiCache Redis: accepts from all service security groups
        self.sg_redis = ec2.SecurityGroup(
            self, "SgRedis",
            vpc=self.vpc,
            description="ElastiCache Redis",
            allow_all_outbound=False,
        )
        for svc in SERVICES:
            self.sg_redis.add_ingress_rule(
                self.sg_services[svc.name],
                ec2.Port.tcp(6379),
                f"{svc.name} → Redis",
            )

        # ALB outbound to each service
        for svc in SERVICES:
            if not svc.is_internal_only:
                self.sg_alb.add_egress_rule(
                    self.sg_services[svc.name],
                    ec2.Port.tcp(svc.port),
                    f"ALB → {svc.name}",
                )

        # SSM VPC endpoint (allows SSM-based deployment without internet)
        ec2.InterfaceVpcEndpoint(
            self, "SsmEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )
        ec2.InterfaceVpcEndpoint(
            self, "SsmMessagesEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )
        ec2.InterfaceVpcEndpoint(
            self, "Ec2MessagesEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
