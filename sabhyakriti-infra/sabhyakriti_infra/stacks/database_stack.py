from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_elasticache as elasticache
import aws_cdk.aws_rds as rds
import aws_cdk.aws_secretsmanager as secretsmanager
from constructs import Construct

from sabhyakriti_infra.config import DB_NAME, DB_PORT
from sabhyakriti_infra.stacks.network_stack import NetworkStack


class DatabaseStack(cdk.Stack):
    """RDS PostgreSQL 15 (Multi-AZ) + ElastiCache Redis."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network: NetworkStack,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── RDS Subnet Group ─────────────────────────────────────────────────
        db_subnet_group = rds.SubnetGroup(
            self, "DbSubnetGroup",
            vpc=network.vpc,
            description="Sabhyakriti RDS private subnets",
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        # ── RDS Credentials ──────────────────────────────────────────────────
        self.db_secret = rds.DatabaseSecret(
            self, "DbSecret",
            username="sabhyakriti_admin",
            secret_name="sabhyakriti/rds/master-credentials",
        )

        # ── RDS PostgreSQL 15 (Multi-AZ) ─────────────────────────────────────
        self.db_instance = rds.DatabaseInstance(
            self, "PostgresInstance",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_4
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.SMALL
            ),
            vpc=network.vpc,
            subnet_group=db_subnet_group,
            security_groups=[network.sg_rds],
            credentials=rds.Credentials.from_secret(self.db_secret),
            database_name=DB_NAME,
            multi_az=True,
            storage_encrypted=True,
            storage_type=rds.StorageType.GP3,
            allocated_storage=20,
            max_allocated_storage=100,
            deletion_protection=True,
            backup_retention=cdk.Duration.days(7),
            preferred_backup_window="02:00-03:00",
            preferred_maintenance_window="sun:03:00-sun:04:00",
            parameter_group=rds.ParameterGroup.from_parameter_group_name(
                self, "DbParamGroup", "default.postgres15"
            ),
            cloudwatch_logs_exports=["postgresql"],
            enable_performance_insights=True,
        )

        # ── RDS Read Replica ─────────────────────────────────────────────────
        self.db_replica = rds.DatabaseInstanceReadReplica(
            self, "PostgresReadReplica",
            source_database_instance=self.db_instance,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.SMALL
            ),
            vpc=network.vpc,
            subnet_group=db_subnet_group,
            security_groups=[network.sg_rds],
            storage_encrypted=True,
        )

        # ── ElastiCache Redis (single node for MVP) ───────────────────────────
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            description="Sabhyakriti Redis private subnets",
            subnet_ids=[
                subnet.subnet_id
                for subnet in network.vpc.private_subnets
            ],
            cache_subnet_group_name="sabhyakriti-redis-subnet-group",
        )

        self.redis_cluster = elasticache.CfnCacheCluster(
            self, "RedisCluster",
            cache_node_type="cache.t3.micro",
            engine="redis",
            engine_version="7.0",
            num_cache_nodes=1,
            cache_subnet_group_name=redis_subnet_group.cache_subnet_group_name,
            vpc_security_group_ids=[network.sg_redis.security_group_id],
            auto_minor_version_upgrade=True,
            snapshot_retention_limit=1,
            snapshot_window="01:00-02:00",
        )
        self.redis_cluster.add_dependency(redis_subnet_group)

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "DbEndpoint", value=self.db_instance.db_instance_endpoint_address)
        cdk.CfnOutput(self, "DbReplicaEndpoint", value=self.db_replica.db_instance_endpoint_address)
        cdk.CfnOutput(
            self, "RedisEndpoint",
            value=self.redis_cluster.attr_redis_endpoint_address,
        )
        cdk.CfnOutput(self, "DbSecretArn", value=self.db_secret.secret_arn)
