from __future__ import annotations

import pulumi

from .config import Config
from .components.kubernetes import KubernetesCluster
from .components.redis import RedisCluster
from .components.qdrant import QdrantCloud
from .components.istio import IstioMesh
from .components.monitoring import MonitoringStack
from .components.certs import CertificateManager
from .components.dns import DNSManager
from .components.quantum import QuantumBackend
from .components.security import SecurityPolicies
from .components.cloudflare import CloudflareResources


def main() -> None:
    config = Config.load()

    vpc_id = pulumi.Config().get("vpc:vpc_id") or "vpc-12345678"
    subnet_ids = [
        pulumi.Config().get("vpc:subnet_a") or "subnet-11111111",
        pulumi.Config().get("vpc:subnet_b") or "subnet-22222222",
        pulumi.Config().get("vpc:subnet_c") or "subnet-33333333",
    ]
    security_group_ids = [
        pulumi.Config().get("vpc:security_group") or "sg-12345678",
    ]

    k8s_cluster = KubernetesCluster(
        "kubernetes",
        config=config,
        vpc_id=vpc_id,
        subnet_ids=subnet_ids,
        opts=pulumi.ResourceOptions(depends_on=[]),
    )

    redis_cluster = RedisCluster(
        "redis",
        config=config,
        vpc_id=vpc_id,
        subnet_ids=subnet_ids,
        security_group_ids=security_group_ids,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster]),
    )

    qdrant_cluster = QdrantCloud(
        "qdrant",
        config=config,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster]),
    )

    cert_manager = CertificateManager(
        "cert-manager",
        config=config,
        k8s_provider=k8s_cluster.provider,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster]),
    )

    security_policies = SecurityPolicies(
        "security",
        config=config,
        k8s_provider=k8s_cluster.provider,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster]),
    )

    istio_mesh = IstioMesh(
        "istio",
        config=config,
        k8s_provider=k8s_cluster.provider,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster, cert_manager]),
    )

    monitoring_stack = MonitoringStack(
        "monitoring",
        config=config,
        k8s_provider=k8s_cluster.provider,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster, istio_mesh]),
    )

    quantum_backend = QuantumBackend(
        "quantum",
        config=config,
        vpc_id=vpc_id,
        subnet_ids=subnet_ids,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster]),
    )

    dns_manager = DNSManager(
        "dns",
        config=config,
        opts=pulumi.ResourceOptions(depends_on=[k8s_cluster, cert_manager]),
    )

    cloudflare_resources = CloudflareResources(
        "cloudflare",
        config=config,
        opts=pulumi.ResourceOptions(depends_on=[dns_manager]),
    )

    pulumi.export("cluster_name", k8s_cluster.cluster_name)
    pulumi.export("cluster_endpoint", k8s_cluster.cluster_endpoint)
    pulumi.export("redis_endpoint", redis_cluster.endpoint)
    pulumi.export("qdrant_endpoint", qdrant_cluster.endpoint)
    pulumi.export("prometheus_endpoint", monitoring_stack.prometheus_endpoint)
    pulumi.export("grafana_endpoint", monitoring_stack.grafana_endpoint)
    pulumi.export("jaeger_endpoint", monitoring_stack.jaeger_endpoint)
    pulumi.export("dns_nameservers", dns_manager.nameservers)
    pulumi.export("quantum_enabled", config.quantum.enabled)
    pulumi.export("environment", config.environment)


if __name__ == "__main__":
    main()
