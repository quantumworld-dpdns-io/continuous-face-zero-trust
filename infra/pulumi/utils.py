from __future__ import annotations

import pulumi


def get_provider_config(cloud: str, region: str) -> dict[str, pulumi.Config]:
    config = pulumi.Config()
    return {
        "cloud": cloud,
        "region": region,
        "project": config.get("project") or "continuous-face-zero-trust",
        "stack": config.full_name,
    }


def validate_tags(tags: dict[str, str]) -> bool:
    for key, value in tags.items():
        if not key or not isinstance(value, str):
            return False
        if len(key) > 128 or len(value) > 256:
            return False
    return True


def create_eks_cluster_config(
    cluster_name: str,
    k8s_version: str,
    node_groups: list[dict],
    vpc_id: str,
    subnet_ids: list[str],
    security_group_ids: list[str] | None = None,
) -> dict:
    return {
        "name": cluster_name,
        "version": k8s_version,
        "role_arn": f"arn:aws:iam::role/{cluster_name}-cluster-role",
        "vpc_config": {
            "subnet_ids": subnet_ids,
            "security_group_ids": security_group_ids or [],
            "endpoint_private_access": True,
            "endpoint_public_access": True,
        },
        "node_groups": node_groups,
        "enabled_cluster_log_types": ["api", "audit", "authenticator", "controllerManager", "scheduler"],
    }


def create_gke_cluster_config(
    cluster_name: str,
    k8s_version: str,
    node_pools: list[dict],
    network: str,
    subnetwork: str,
    region: str,
) -> dict:
    return {
        "name": cluster_name,
        "initial_node_count": 1,
        "min_master_version": k8s_version,
        "network": network,
        "subnetwork": subnetwork,
        "location": region,
        "node_pools": node_pools,
        "release_channel": {"channel": "REGULAR"},
        "logging_config": {
            "enable_components": ["SYSTEM_COMPONENTS", "WORKLOADS"],
        },
        "monitoring_config": {
            "enable_components": ["SYSTEM_COMPONENTS"],
        },
    }


def create_aks_cluster_config(
    cluster_name: str,
    k8s_version: str,
    node_pools: list[dict],
    resource_group: str,
    vnet_subnet_id: str,
) -> dict:
    return {
        "name": cluster_name,
        "kubernetes_version": k8s_version,
        "resource_group_name": resource_group,
        "dns_prefix": cluster_name,
        "network_profile": {
            "network_plugin": "azure",
            "network_policy": "calico",
            "load_balancer_sku": "standard",
        },
        "agent_pool_profiles": node_pools,
        "vnet_subnet_id": vnet_subnet_id,
        "enable_rbac": True,
        "enable_pod_security_policy": True,
    }


def create_elasticache_cluster_config(
    cluster_name: str,
    node_type: str,
    num_shards: int,
    num_replicas: int,
    engine_version: str,
    port: int,
    subnet_group_name: str,
    security_group_ids: list[str],
    parameter_group: str,
    at_rest_encryption: bool,
    transit_encryption: bool,
) -> dict:
    return {
        "cluster_id": cluster_name,
        "engine": "redis",
        "engine_version": engine_version,
        "node_type": node_type,
        "num_cache_nodes": num_replicas,
        "num_shards": num_shards,
        "port": port,
        "subnet_group_name": subnet_group_name,
        "security_group_ids": security_group_ids,
        "parameter_group_name": parameter_group,
        "at_rest_encryption_enabled": at_rest_encryption,
        "transit_encryption_enabled": transit_encryption,
        "automatic_failover_enabled": True,
        "multi_az_enabled": True,
        "snapshot_retention_limit": 7,
        "maintenance_window": "sun:05:00-sun:09:00",
        "notification_topic_arn": "",
        "auto_minor_version_upgrade": True,
    }


def create_monitoring_stack_config(
    prometheus_retention_days: int,
    grafana_admin_password: str,
    jaeger_agent_port: int,
    jaeger_collector_port: int,
    enable_loki: bool,
    enable_pyroscope: bool,
) -> dict:
    return {
        "prometheus": {
            "retention_days": prometheus_retention_days,
            "storage_class": "gp3",
            "scrape_interval": "15s",
            "evaluation_interval": "15s",
        },
        "grafana": {
            "admin_password": grafana_admin_password,
            "persistence_enabled": True,
            "persistence_size": "10Gi",
        },
        "jaeger": {
            "agent_port": jaeger_agent_port,
            "collector_port": jaeger_collector_port,
            "storage_type": "elasticsearch",
            "collector_replicas": 2,
        },
        "loki": {"enabled": enable_loki},
        "pyroscope": {"enabled": enable_pyroscope},
    }
