from __future__ import annotations

from typing import Any

import pulumi

from ..config import Config
from ..utils import get_tag, resource_name


class RedisCluster(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        vpc_id: str,
        subnet_ids: list[str],
        security_group_ids: list[str] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:RedisCluster", name, {}, opts)
        self._config = config
        self._vpc_id = vpc_id
        self._subnet_ids = subnet_ids
        self._security_group_ids = security_group_ids or []
        self._tags = get_tag(config.project_name, config.environment, {"Component": "redis"})

        self._create_cluster(name, config, opts)

    def _create_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        provider = config.cloud.provider
        if provider == "aws":
            self._create_elasticache_cluster(name, config, opts)
        elif provider == "gcp":
            self._create_memorystore_cluster(name, config, opts)
        elif provider == "azure":
            self._create_azure_redis_cluster(name, config, opts)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider}")

    def _create_elasticache_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "redis")

        subnet_group = aws.elasticache.SubnetGroup(
            f"{cluster_name}-subnet-group",
            subnet_ids=self._subnet_ids,
            description=f"Redis subnet group for {config.environment}",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        security_group = aws.ec2.SecurityGroup(
            f"{cluster_name}-sg",
            description="Redis security group",
            vpc_id=self._vpc_id,
            ingress=[{
                "from_port": config.redis.port or 6379,
                "to_port": config.redis.port or 6379,
                "protocol": "tcp",
                "security_groups": self._security_group_ids,
            }],
            egress=[{
                "from_port": 0,
                "to_port": 0,
                "protocol": "-1",
                "cidr_blocks": ["0.0.0.0/0"],
            }],
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        parameter_group = aws.elasticache.ParameterGroup(
            f"{cluster_name}-params",
            family="redis7",
            parameter=[
                {
                    "name": "maxmemory-policy",
                    "value": "allkeys-lru",
                },
                {
                    "name": "notify-keyspace-events",
                    "value": "Ex",
                },
            ],
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cluster = aws.elasticache.ReplicationGroup(
            f"{cluster_name}",
            replication_group_id=cluster_name,
            description=f"Redis cluster for {config.environment}",
            node_type=config.redis.node_type or "cache.r6g.large",
            num_cache_clusters=config.redis.num_replicas or 2,
            port=config.redis.port or 6379,
            subnet_group_name=subnet_group.name,
            security_group_ids=[security_group.id],
            parameter_group_name=parameter_group.name,
            at_rest_encryption_enabled=config.redis.at_rest_encryption,
            transit_encryption_enabled=config.redis.transit_encryption,
            automatic_failover_enabled=True,
            multi_az_enabled=True,
            snapshot_retention_limit=7,
            maintenance_window="sun:05:00-sun:09:00",
            auto_minor_version_upgrade=True,
            engine_version=config.redis.engine_version or "7.0",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_memorystore_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "redis")

        network = gcp.compute.Network(
            f"{cluster_name}-network",
            auto_create_subnetworks=False,
            opts=pulumi.ResourceOptions(parent=self),
        )

        subnet = gcp.compute.Subnetwork(
            f"{cluster_name}-subnet",
            ip_cidr_range="10.0.1.0/24",
            region=config.cloud.region,
            network=network.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.network = network

        self.cluster = gcp.memorystore.Instance(
            f"{cluster_name}",
            region=config.cloud.region,
            memory_size_gb=5,
            tier="STANDARD_HA",
            redis_version="REDIS_7_0",
            display_name=f"CFZT Redis {config.environment}",
            authorized_network=network.id,
            redis_configs={
                "maxmemory-policy": "allkeys-lru",
                "notify-keyspace-events": "Ex",
            },
            labels=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_azure_redis_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "redis")

        self.redis = azure.redis.Cache(
            f"{cluster_name}",
            resource_group_name=config.azure.resource_group_name if hasattr(config, 'azure') else f"cfzt-{config.environment}-rg",
            location=config.cloud.region or "West US 2",
            sku_name="Premium",
            family="P",
            capacity=1,
            enable_non_ssl_port=False,
            minimum_tls_version="1.2",
            redis_version="6",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

    @property
    def endpoint(self) -> pulumi.Output[str]:
        if hasattr(self, 'cluster') and self._config.cloud.provider == "aws":
            return self.cluster.primary_endpoint_address
        elif hasattr(self, 'cluster') and self._config.cloud.provider == "gcp":
            return self.cluster.host
        return pulumi.Output.secret("")

    @property
    def port(self) -> pulumi.Output[int]:
        if hasattr(self, 'cluster') and self._config.cloud.provider == "aws":
            return self.cluster.port
        elif hasattr(self, 'cluster') and self._config.cloud.provider == "gcp":
            return self.cluster.port
        return pulumi.Output.secret(6379)

    @property
    def auth_token(self) -> pulumi.Output[str]:
        if hasattr(self, 'cluster') and self._config.cloud.provider == "aws":
            return self.cluster.auth_token
        elif hasattr(self, 'cluster') and self._config.cloud.provider == "gcp":
            return self.cluster.auth_string
        return pulumi.Output.secret("")
