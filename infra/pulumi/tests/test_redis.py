from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from infra.pulumi.components.redis import RedisCluster
from infra.pulumi.config import Config, RedisConfig, CloudConfig


class TestRedisCluster(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            environment="test",
            cloud=CloudConfig(provider="aws", region="us-west-2"),
            redis=RedisConfig(
                node_type="cache.r6g.large",
                num_shards=1,
                num_replicas=2,
                engine_version="7.0",
                port=6379,
                at_rest_encryption=True,
                transit_encryption=True,
            ),
        )

    def test_config_defaults(self):
        config = Config()
        self.assertEqual(config.redis.node_type, "cache.r6g.large")
        self.assertEqual(config.redis.num_replicas, 2)
        self.assertEqual(config.redis.engine_version, "7.0")
        self.assertTrue(config.redis.at_rest_encryption)

    def test_config_custom_values(self):
        config = Config(
            redis=RedisConfig(
                node_type="cache.m5.large",
                num_replicas=3,
                engine_version="6.2",
                port=6380,
            ),
        )
        self.assertEqual(config.redis.node_type, "cache.m5.large")
        self.assertEqual(config.redis.num_replicas, 3)
        self.assertEqual(config.redis.engine_version, "6.2")
        self.assertEqual(config.redis.port, 6380)

    def test_elasticache_cluster_config(self):
        from infra.pulumi.utils import create_elasticache_cluster_config

        cluster_config = create_elasticache_cluster_config(
            cluster_name="test-redis",
            node_type="cache.r6g.large",
            num_shards=1,
            num_replicas=2,
            engine_version="7.0",
            port=6379,
            subnet_group_name="test-subnet-group",
            security_group_ids=["sg-12345"],
            parameter_group="default.redis7",
            at_rest_encryption=True,
            transit_encryption=True,
        )

        self.assertEqual(cluster_config["cluster_id"], "test-redis")
        self.assertEqual(cluster_config["engine"], "redis")
        self.assertEqual(cluster_config["engine_version"], "7.0")
        self.assertTrue(cluster_config["at_rest_encryption_enabled"])
        self.assertTrue(cluster_config["transit_encryption_enabled"])
        self.assertTrue(cluster_config["automatic_failover_enabled"])
        self.assertTrue(cluster_config["multi_az_enabled"])

    def test_redis_encryption_config(self):
        config = Config(
            redis=RedisConfig(
                at_rest_encryption=False,
                transit_encryption=False,
            ),
        )
        self.assertFalse(config.redis.at_rest_encryption)
        self.assertFalse(config.redis.transit_encryption)

    def test_redis_maintenance_window(self):
        from infra.pulumi.utils import create_elasticache_cluster_config

        cluster_config = create_elasticache_cluster_config(
            cluster_name="test-redis",
            node_type="cache.r6g.large",
            num_shards=1,
            num_replicas=2,
            engine_version="7.0",
            port=6379,
            subnet_group_name="test-subnet-group",
            security_group_ids=["sg-12345"],
            parameter_group="default.redis7",
            at_rest_encryption=True,
            transit_encryption=True,
        )

        self.assertEqual(cluster_config["maintenance_window"], "sun:05:00-sun:09:00")
        self.assertEqual(cluster_config["snapshot_retention_limit"], 7)
        self.assertTrue(cluster_config["auto_minor_version_upgrade"])


if __name__ == "__main__":
    unittest.main()
