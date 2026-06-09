from __future__ import annotations

from typing import Any

import pulumi

from ..config import Config
from ..utils import get_tag, resource_name


class QdrantCloud(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:QdrantCloud", name, {}, opts)
        self._config = config
        self._tags = get_tag(config.project_name, config.environment, {"Component": "qdrant"})

        self._create_cluster(name, config, opts)

    def _create_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "qdrant")

        self.cluster_config = pulumi.Config("qdrant")

        api_key = config.qdrant.cloud_api_key
        cloud_url = config.qdrant.cloud_url

        self.qdrant_endpoint = pulumi.Output.secret(
            pulumi.Config().get_secret("qdrant:cloud_api_key") or cloud_url
        )

        self.collection = self._create_collection(config)

        self._create_backup_policy(config, opts)

        self._create_monitoring(config, opts)

    def _create_collection(self, config: Config) -> dict:
        return {
            "name": config.qdrant.collection_name or "face_embeddings",
            "vectors": {
                "size": config.qdrant.vector_size or 512,
                "distance": config.qdrant.distance_metric or "Cosine",
            },
            "shard_number": 1,
            "replication_factor": 3,
            "on_disk_payload": True,
            "optimizers_config": {
                "indexing_threshold": 20000,
                "memmap_threshold": 20000,
            },
            "wal_config": {
                "wal_capacity_mb": 32,
                "wal_segments_ahead": 0,
            },
        }

    def _create_backup_policy(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.backup_config = {
            "enabled": True,
            "schedule": "0 2 * * *",
            "retention_days": 30,
            "storage": "s3",
            "bucket": f"cfzt-{config.environment}-qdrant-backups",
            "region": config.cloud.region,
        }

    def _create_monitoring(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.monitoring_config = {
            "enabled": True,
            "metrics_port": 6333,
            "health_check_interval": 30,
            "alert_rules": [
                {
                    "name": "high_memory_usage",
                    "condition": "memory_usage > 80%",
                    "severity": "warning",
                },
                {
                    "name": "high_latency",
                    "condition": "search_latency_p99 > 100ms",
                    "severity": "critical",
                },
            ],
        }

    @property
    def endpoint(self) -> pulumi.Output[str]:
        return self.qdrant_endpoint

    @property
    def collection_name(self) -> str:
        return self._config.qdrant.collection_name or "face_embeddings"

    @property
    def api_key(self) -> pulumi.Output[str]:
        return pulumi.Config().get_secret("qdrant:cloud_api_key") or pulumi.Output.secret("")
