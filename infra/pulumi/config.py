from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import pulumi


@dataclass(frozen=True)
class CloudConfig:
    provider: str = "aws"
    region: str = "us-west-2"
    project: str = ""
    zone: str = ""


@dataclass(frozen=True)
class KubernetesConfig:
    cluster_name: str = "cfzt-cluster"
    version: str = "1.28"
    node_count: int = 3
    node_type: str = "t3.large"
    min_nodes: int = 2
    max_nodes: int = 10
    pod_cidr: str = "10.244.0.0/16"
    service_cidr: str = "10.96.0.0/16"


@dataclass(frozen=True)
class RedisConfig:
    node_type: str = "cache.r6g.large"
    num_shards: int = 1
    num_replicas: int = 2
    engine_version: str = "7.0"
    port: int = 6379
    parameter_group: str = "default.redis7"
    at_rest_encryption: bool = True
    transit_encryption: bool = True


@dataclass(frozen=True)
class QdrantConfig:
    cloud_api_key: str = ""
    cluster_name: str = "cfzt-qdrant"
    region: str = "aws-us-east-1"
    cloud_url: str = "https://api.qdrant.io:6333"
    collection_name: str = "face_embeddings"
    vector_size: int = 512
    distance_metric: str = "Cosine"


@dataclass(frozen=True)
class MonitoringConfig:
    prometheus_retention_days: int = 30
    grafana_admin_password: str = ""
    jaeger_agent_port: int = 6831
    jaeger_collector_port: int = 14268
    enable_loki: bool = True
    enable_pyroscope: bool = True
    log_level: str = "info"


@dataclass(frozen=True)
class SecurityConfig:
    waf_enabled: bool = True
    network_policy_enabled: bool = True
    mtls_enabled: bool = True
    cert_manager_enabled: bool = True
    intrusion_detection: bool = True
    max_failed_auth_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 15
    biometric_confidence_threshold: float = 0.85


@dataclass(frozen=True)
class DNSConfig:
    zone_name: str = "cfzt.example.com"
    provider: str = "cloudflare"
    cf_zone_id: str = ""
    cf_api_token: str = ""
    enable_dnssec: bool = True
    ttl_seconds: int = 300


@dataclass(frozen=True)
class CertificateConfig:
    issuer: str = "letsencrypt-prod"
    email: str = "admin@cfzt.example.com"
    renew_before_days: int = 30
    cert_duration_days: int = 90
    auto_renew: bool = True


@dataclass(frozen=True)
class QuantumConfig:
    enabled: bool = False
    provider: str = "braket"
    region: str = "us-east-1"
    s3_bucket: str = "cfzt-quantum-results"
    max_qubits: int = 32
    backend: str = "amazon-braket-arn:::provider/quantum-device/simulator"
    enable_hybrid: bool = True
    shot_count: int = 1000


@dataclass(frozen=True)
class VPCConfig:
    cidr: str = "10.0.0.0/16"
    enable_dns_hostnames: bool = True
    enable_dns_support: bool = True
    nat_gateway_count: int = 1
    single_nat_gateway: bool = False
    availability_zones: list[str] = field(default_factory=lambda: ["us-west-2a", "us-west-2b", "us-west-2c"])


@dataclass(frozen=True)
class IstioConfig:
    enabled: bool = True
    version: str = "1.20.0"
    mtls_strict: bool = True
    tracing_enabled: bool = True
    access_log_enabled: bool = True


@dataclass(frozen=True)
class CloudflareConfig:
    account_id: str = ""
    api_token: str = ""
    zone_id: ""
    workers_enabled: bool = True
    kv_namespace: str = "cfzt-kv"
    r2_bucket: str = "cfzt-r2"
    do_enabled: bool = True
    turnstile_enabled: bool = True
    dns_proxied: bool = True


@dataclass(frozen=True)
class Config:
    cloud: CloudConfig = field(default_factory=CloudConfig)
    kubernetes: KubernetesConfig = field(default_factory=KubernetesConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    dns: DNSConfig = field(default_factory=DNSConfig)
    certificates: CertificateConfig = field(default_factory=CertificateConfig)
    quantum: QuantumConfig = field(default_factory=QuantumConfig)
    vpc: VPCConfig = field(default_factory=VPCConfig)
    istio: IstioConfig = field(default_factory=IstioConfig)
    cloudflare: CloudflareConfig = field(default_factory=CloudflareConfig)
    environment: str = "development"
    project_name: str = "continuous-face-zero-trust"

    @classmethod
    def load(cls) -> Config:
        environment = pulumi.Config().get("environment") or os.environ.get("CFZT_ENVIRONMENT", "development")

        cloud_provider = os.environ.get("CFZT_CLOUD_PROVIDER", "aws")
        region = os.environ.get("CFZT_REGION", "us-west-2")

        k8s_config = pulumi.Config("kubernetes") if pulumi.Config("kubernetes") else None
        k8s_version = k8s_config.get("version") if k8s_config else os.environ.get("CFZT_K8S_VERSION", "1.28")

        redis_node_type = os.environ.get("CFZT_REDIS_NODE_TYPE", "cache.r6g.large")

        qdrant_api_key = os.environ.get("CFZT_QDRANT_API_KEY", "")

        enable_quantum = os.environ.get("CFZT_ENABLE_QUANTUM", "false").lower() == "true"

        grafana_password = os.environ.get("CFZT_GRAFANA_PASSWORD", "")
        cf_api_token = os.environ.get("CFZT_CF_API_TOKEN", "")
        cf_zone_id = os.environ.get("CFZT_CF_ZONE_ID", "")
        cf_account_id = os.environ.get("CFZT_CF_ACCOUNT_ID", "")
        dns_zone = os.environ.get("CFZT_DNS_ZONE", "cfzt.example.com")
        cert_email = os.environ.get("CFZT_CERT_EMAIL", "admin@cfzt.example.com")

        return cls(
            environment=environment,
            cloud=CloudConfig(provider=cloud_provider, region=region),
            kubernetes=KubernetesConfig(
                cluster_name=f"cfzt-{environment}-k8s",
                version=k8s_version,
            ),
            redis=RedisConfig(node_type=redis_node_type),
            qdrant=QdrantConfig(
                cloud_api_key=qdrant_api_key,
                cluster_name=f"cfzt-{environment}-qdrant",
            ),
            monitoring=MonitoringConfig(grafana_admin_password=grafana_password),
            quantum=QuantumConfig(enabled=enable_quantum),
            dns=DNSConfig(
                zone_name=dns_zone,
                cf_api_token=cf_api_token,
                cf_zone_id=cf_zone_id,
            ),
            certificates=CertificateConfig(email=cert_email),
            cloudflare=CloudflareConfig(
                account_id=cf_account_id,
                api_token=cf_api_token,
                zone_id=cf_zone_id,
            ),
        )
