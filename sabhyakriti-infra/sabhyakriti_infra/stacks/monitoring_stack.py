from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_cloudwatch_actions as cw_actions
import aws_cdk.aws_logs as logs
import aws_cdk.aws_sns as sns
import aws_cdk.aws_sns_subscriptions as sns_subs
from constructs import Construct

from sabhyakriti_infra.config import LOG_RETENTION_DAYS, SERVICES
from sabhyakriti_infra.stacks.compute_stack import ComputeStack


class MonitoringStack(cdk.Stack):
    """CloudWatch log groups, alarms, and dashboard for all services."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        compute: ComputeStack,
        admin_email: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── SNS Alert Topic ───────────────────────────────────────────────────
        self.alert_topic = sns.Topic(
            self, "AlertTopic",
            topic_name="sabhyakriti-ops-alerts",
            display_name="Sabhyakriti Ops Alerts",
        )
        self.alert_topic.add_subscription(
            sns_subs.EmailSubscription(admin_email)
        )

        # ── CloudWatch Log Groups (per service, 90-day retention) ─────────────
        self.log_groups: dict[str, logs.LogGroup] = {}
        for svc in SERVICES:
            lg = logs.LogGroup(
                self, f"LogGroup{svc.name.replace('-','').title()}",
                log_group_name=f"/sabhyakriti/{svc.name}",
                retention=logs.RetentionDays.THREE_MONTHS,  # 90 days — SECURITY-14
                removal_policy=cdk.RemovalPolicy.RETAIN,
            )
            self.log_groups[svc.name] = lg

        # ── Alarms ────────────────────────────────────────────────────────────
        alarm_action = cw_actions.SnsAction(self.alert_topic)

        # ALB 5xx error alarm
        if compute.alb:
            alb_5xx = cloudwatch.Alarm(
                self, "Alb5xxAlarm",
                metric=compute.alb.metrics.http_code_elb(
                    code=cloudwatch.HttpCodeElb.ELB_5XX_COUNT,
                    period=cdk.Duration.minutes(5),
                    statistic="Sum",
                ),
                threshold=10,
                evaluation_periods=1,
                alarm_description="ALB 5xx errors > 10 in 5 minutes",
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            alb_5xx.add_alarm_action(alarm_action)

        # Per-service CPU alarms
        for svc in SERVICES:
            asg = compute.asgs.get(svc.name)
            if not asg:
                continue
            safe = svc.name.replace("-", "").title()
            cpu_alarm = cloudwatch.Alarm(
                self, f"CpuAlarm{safe}",
                metric=cloudwatch.Metric(
                    namespace="AWS/EC2",
                    metric_name="CPUUtilization",
                    dimensions_map={"AutoScalingGroupName": asg.auto_scaling_group_name},
                    period=cdk.Duration.minutes(10),
                    statistic="Average",
                ),
                threshold=80,
                evaluation_periods=2,
                alarm_description=f"{svc.name} CPU > 80% for 20 minutes",
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            cpu_alarm.add_alarm_action(alarm_action)

        # Auth service — login failure alarm
        auth_login_fail = cloudwatch.Alarm(
            self, "AuthLoginFailAlarm",
            metric=cloudwatch.Metric(
                namespace="Sabhyakriti/AuthService",
                metric_name="LoginFailure",
                period=cdk.Duration.minutes(1),
                statistic="Sum",
            ),
            threshold=50,
            evaluation_periods=1,
            alarm_description="Auth service: > 50 login failures per minute — possible attack",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        auth_login_fail.add_alarm_action(alarm_action)

        # ── CloudWatch Dashboard ──────────────────────────────────────────────
        dashboard = cloudwatch.Dashboard(
            self, "MainDashboard",
            dashboard_name="Sabhyakriti-Platform",
        )
        widgets: list[cloudwatch.IWidget] = []
        for svc in SERVICES:
            asg = compute.asgs.get(svc.name)
            if not asg:
                continue
            widgets.append(
                cloudwatch.GraphWidget(
                    title=f"{svc.name} CPU",
                    left=[cloudwatch.Metric(
                        namespace="AWS/EC2",
                        metric_name="CPUUtilization",
                        dimensions_map={"AutoScalingGroupName": asg.auto_scaling_group_name},
                        statistic="Average",
                    )],
                    width=8,
                )
            )
        if widgets:
            dashboard.add_widgets(*widgets)
