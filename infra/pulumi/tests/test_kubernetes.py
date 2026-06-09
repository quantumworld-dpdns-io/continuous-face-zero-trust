from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from infra.pulumi.components.kubernetes import KubernetesCluster
from infra.pulumi.config import Config, KubernetesConfig, CloudConfig


class TestKubernetesCluster(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            environment="test",
            cloud=CloudConfig(provider="aws", region="us-west-2"),
            kubernetes=KubernetesConfig(
                cluster_name="test-k8s",
                version="1.28",
                node_count=2,
                node_type="t3.medium",
                min_nodes=1,
                max_nodes=5,
            ),
        )

    def test_config_defaults(self):
        config = Config()
        self.assertEqual(config.kubernetes.version, "1.28")
        self.assertEqual(config.kubernetes.node_count, 3)
        self.assertEqual(config.kubernetes.node_type, "t3.large")

    def test_config_custom_values(self):
        config = Config(
            kubernetes=KubernetesConfig(
                cluster_name="custom-cluster",
                version="1.29",
                node_count=5,
            ),
        )
        self.assertEqual(config.kubernetes.cluster_name, "custom-cluster")
        self.assertEqual(config.kubernetes.version, "1.29")
        self.assertEqual(config.kubernetes.node_count, 5)

    def test_eks_cluster_config(self):
        from infra.pulumi.utils import create_eks_cluster_config

        cluster_config = create_eks_cluster_config(
            cluster_name="test-cluster",
            k8s_version="1.28",
            node_groups=[{"instance_types": ["t3.medium"]}],
            vpc_id="vpc-12345",
            subnet_ids=["subnet-1", "subnet-2"],
        )

        self.assertEqual(cluster_config["name"], "test-cluster")
        self.assertEqual(cluster_config["version"], "1.28")
        self.assertIn("api", cluster_config["enabled_cluster_log_types"])

    def test_gke_cluster_config(self):
        from infra.pulumi.utils import create_gke_cluster_config

        cluster_config = create_gke_cluster_config(
            cluster_name="test-cluster",
            k8s_version="1.28",
            node_pools=[{"initial_node_count": 3}],
            network="default",
            subnetwork="default",
            region="us-west2-a",
        )

        self.assertEqual(cluster_config["name"], "test-cluster")
        self.assertEqual(cluster_config["min_master_version"], "1.28")
        self.assertIn("SYSTEM_COMPONENTS", cluster_config["logging_config"]["enable_components"])

    def test_aks_cluster_config(self):
        from infra.pulumi.utils import create_aks_cluster_config

        cluster_config = create_aks_cluster_config(
            cluster_name="test-cluster",
            k8s_version="1.28",
            node_pools=[{"name": "default", "count": 3}],
            resource_group="test-rg",
            vnet_subnet_id="subnet-12345",
        )

        self.assertEqual(cluster_config["name"], "test-cluster")
        self.assertEqual(cluster_config["kubernetes_version"], "1.28")
        self.assertTrue(cluster_config["enable_rbac"])

    def test_kubernetes_config_validation(self):
        config = Config(
            kubernetes=KubernetesConfig(
                node_count=0,
                min_nodes=0,
                max_nodes=0,
            ),
        )
        self.assertEqual(config.kubernetes.node_count, 0)
        self.assertEqual(config.kubernetes.min_nodes, 0)
        self.assertEqual(config.kubernetes.max_nodes, 0)

    def test_resource_name(self):
        from infra.pulumi.utils import resource_name

        self.assertEqual(resource_name("development", "k8s"), "cfzt-development-k8s")
        self.assertEqual(resource_name("production", "redis"), "cfzt-production-redis")
        self.assertEqual(resource_name("staging", "k8s", "_"), "cfzt_staging_k8s")


if __name__ == "__main__":
    unittest.main()
