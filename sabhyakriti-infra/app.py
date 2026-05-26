#!/usr/bin/env python3
"""Sabhyakriti AWS CDK Application — Production environment."""
from __future__ import annotations

import os

import aws_cdk as cdk

from sabhyakriti_infra.config import AWS_REGION
from sabhyakriti_infra.stacks.compute_stack import ComputeStack
from sabhyakriti_infra.stacks.database_stack import DatabaseStack
from sabhyakriti_infra.stacks.monitoring_stack import MonitoringStack
from sabhyakriti_infra.stacks.network_stack import NetworkStack
from sabhyakriti_infra.stacks.storage_stack import StorageStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=AWS_REGION,
)

ADMIN_EMAIL = os.environ.get("ADMIN_ALERT_EMAIL", "admin@sabhyakriti.com")

# ── Layered stack deployment (order matters for dependencies) ─────────────────

network = NetworkStack(app, "SabhyakritiNetwork", env=env,
    description="VPC, subnets, security groups")

database = DatabaseStack(app, "SabhyakritiDatabase", network=network, env=env,
    description="RDS PostgreSQL 15 + ElastiCache Redis")

storage = StorageStack(app, "SabhyakritiStorage", env=env,
    description="S3 product images + CloudFront + SES + SNS")

compute = ComputeStack(app, "SabhyakritiCompute", network=network, database=database, env=env,
    description="EC2 Auto Scaling + ALB for all 7 microservices")

MonitoringStack(app, "SabhyakritiMonitoring", compute=compute,
    admin_email=ADMIN_EMAIL, env=env,
    description="CloudWatch log groups, alarms, dashboard")

# Apply standard tags to all resources
cdk.Tags.of(app).add("Project", "Sabhyakriti")
cdk.Tags.of(app).add("Environment", "Production")
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
