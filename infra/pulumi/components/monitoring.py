from __future__ import annotations

from typing import Any

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import helm, v3

from ..config import Config
from ..utils import get_tag, resource_name


class MonitoringStack(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        k8s_provider: k8s.Provider,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:MonitoringStack", name, {}, opts)
        self._config = config
        self._k8s_provider = k8s_provider
        self._tags = get_tag(config.project_name, config.environment, {"Component": "monitoring"})
        self._namespace = f"monitoring-{config.environment}"

        self._create_namespace(config, opts)
        self._install_prometheus(config, opts)
        self._install_grafana(config, opts)
        self._install_jaeger(config, opts)
        self._install_loki(config, opts)
        self._install_pyroscope(config, opts)
        self._create_alert_rules(config, opts)

    def _create_namespace(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.namespace = k8s.core.v1.Namespace(
            self._namespace,
            metadata={
                "name": self._namespace,
                "labels": self._tags,
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

    def _install_prometheus(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.prometheus = helm.v3.Release(
            "prometheus-server",
            chart="kube-prometheus-stack",
            version="56.6.2",
            namespace=self._namespace,
            repository_opts={
                "repo": "https://prometheus-community.github.io/helm-charts",
            },
            values={
                "prometheus": {
                    "retention": f"{config.monitoring.prometheus_retention_days}d",
                    "resources": {
                        "requests": {
                            "cpu": "500m",
                            "memory": "1Gi",
                        },
                        "limits": {
                            "cpu": "2000m",
                            "memory": "4Gi",
                        },
                    },
                    "storageSpec": {
                        "volumeClaimTemplate": {
                            "spec": {
                                "storageClassName": "gp3",
                                "accessModes": ["ReadWriteOnce"],
                                "resources": {
                                    "requests": {
                                        "storage": "50Gi",
                                    },
                                },
                            },
                        },
                    },
                    "additionalScrapeConfigs": [
                        {
                            "job_name": "face-ml-metrics",
                            "static_configs": [{"targets": ["face-ml-service:8080/metrics"]}],
                        },
                        {
                            "job_name": "quantum-metrics",
                            "static_configs": [{"targets": ["quantum-service:8080/metrics"]}],
                        },
                        {
                            "job_name": "istio-mesh",
                            "kubernetes_sd_configs": [{"role": "endpoints"}],
                            "relabel_configs": [
                                {
                                    "source_labels": ["__meta_kubernetes_service_annotation_prometheus_io_scrape"],
                                    "action": "keep",
                                    "regex": True,
                                },
                            ],
                        },
                    ],
                },
                "alertmanager": {
                    "enabled": True,
                    "replicaCount": 2,
                    "config": {
                        "global": {
                            "resolve_timeout": "5m",
                        },
                        "route": {
                            "group_by": ["alertname", "cluster", "service"],
                            "group_wait": "10s",
                            "group_interval": "10s",
                            "repeat_interval": "12h",
                            "receiver": "default",
                            "routes": [
                                {
                                    "match": {"severity": "critical"},
                                    "receiver": "critical",
                                },
                            ],
                        },
                        "receivers": [
                            {
                                "name": "default",
                                "webhook_configs": [
                                    {"url": "http://incident-responder:9095/webhook"},
                                ],
                            },
                            {
                                "name": "critical",
                                "webhook_configs": [
                                    {"url": "http://incident-responder:9095/webhook/critical"},
                                ],
                            },
                        ],
                    },
                },
                "nodeExporter": {"enabled": True},
                "kubeStateMetrics": {"enabled": True},
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.namespace],
            ),
        )

    def _install_grafana(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.grafana = helm.v3.Release(
            "grafana",
            chart="grafana",
            version="7.0.11",
            namespace=self._namespace,
            repository_opts={
                "repo": "https://grafana.github.io/helm-charts",
            },
            values={
                "adminPassword": config.monitoring.grafana_admin_password or "admin",
                "persistence": {
                    "enabled": True,
                    "size": "10Gi",
                },
                "resources": {
                    "requests": {
                        "cpu": "200m",
                        "memory": "512Mi",
                    },
                    "limits": {
                        "cpu": "1000m",
                        "memory": "2Gi",
                    },
                },
                "datasources": {
                    "datasources.yaml": {
                        "apiVersion": 1,
                        "datasources": [
                            {
                                "name": "Prometheus",
                                "type": "prometheus",
                                "url": f"http://prometheus-server.{self._namespace}.svc.cluster.local:9090",
                                "access": "proxy",
                                "isDefault": True,
                            },
                            {
                                "name": "Loki",
                                "type": "loki",
                                "url": f"http://loki.{self._namespace}.svc.cluster.local:3100",
                                "access": "proxy",
                            },
                            {
                                "name": "Jaeger",
                                "type": "jaeger",
                                "url": f"http://jaeger-query.{self._namespace}.svc.cluster.local:16686",
                                "access": "proxy",
                            },
                        ],
                    },
                },
                "dashboardProviders": {
                    "dashboardproviders.yaml": {
                        "apiVersion": 1,
                        "providers": [
                            {
                                "name": "default",
                                "orgId": 1,
                                "folder": "",
                                "type": "file",
                                "disableDeletion": False,
                                "editable": True,
                                "options": {"path": "/var/lib/grafana/dashboards/default"},
                            },
                        ],
                    },
                },
                "dashboards": {
                    "default": {
                        "face-ml": {
                            "json": self._get_face_ml_dashboard(),
                        },
                        "quantum-ml": {
                            "json": self._get_quantum_ml_dashboard(),
                        },
                        "zero-trust": {
                            "json": self._get_zero_trust_dashboard(),
                        },
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.namespace],
            ),
        )

    def _install_jaeger(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.jaeger = helm.v3.Release(
            "jaeger",
            chart="jaeger",
            version="1.55.0",
            namespace=self._namespace,
            repository_opts={
                "repo": "https://jaegertracing.github.io/helm-charts",
            },
            values={
                "collector": {
                    "replicaCount": 2,
                    "resources": {
                        "requests": {
                            "cpu": "500m",
                            "memory": "512Mi",
                        },
                    },
                    "service": {
                        "type": "ClusterIP",
                        "ports": [
                            {"name": "http-collector", "port": 14268, "targetPort": 14268},
                            {"name": "grpc-collector", "port": 14250, "targetPort": 14250},
                            {"name": "zipkin", "port": 9411, "targetPort": 9411},
                        ],
                    },
                },
                "query": {
                    "replicaCount": 2,
                    "resources": {
                        "requests": {
                            "cpu": "200m",
                            "memory": "256Mi",
                        },
                    },
                },
                "agent": {
                    "enabled": False,
                },
                "storage": {
                    "type": "elasticsearch",
                    "elasticsearch": {
                        "host": "elasticsearch-master",
                        "port": 9200,
                    },
                },
                "sparkDependenciesJob": {
                    "enabled": True,
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.namespace],
            ),
        )

    def _install_loki(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        if not config.monitoring.enable_loki:
            return

        self.loki = helm.v3.Release(
            "loki",
            chart="loki",
            version="5.42.0",
            namespace=self._namespace,
            repository_opts={
                "repo": "https://grafana.github.io/helm-charts",
            },
            values={
                "loki": {
                    "auth_enabled": False,
                    "commonConfig": {
                        "replication_factor": 3,
                    },
                    "storage": {
                        "type": "s3",
                        "s3": {
                            "endpoint": f"s3.{config.cloud.region}.amazonaws.com",
                            "region": config.cloud.region,
                            "bucket": f"cfzt-{config.environment}-loki",
                        },
                    },
                    "schema_config": {
                        "configs": [
                            {
                                "from": "2024-01-01",
                                "store": "tsdb",
                                "object_store": "s3",
                                "schema": "v13",
                                "index": {
                                    "prefix": "index_",
                                    "period": "24h",
                                },
                            },
                        ],
                    },
                    "compactor": {
                        "working_directory": "/var/loki/compactor",
                        "compaction_interval": "10m",
                        "retention_enabled": True,
                        "retention_delete_delay": "2h",
                    },
                    "ruler": {
                        "storage": {
                            "type": "s3",
                            "s3": {
                                "bucket": f"cfzt-{config.environment}-loki-ruler",
                            },
                        },
                        "rule_path": "/var/loki/ruler",
                    },
                },
                "monitoring": {
                    "dashboards": {
                        "enabled": True,
                    },
                    "serviceMonitor": {
                        "enabled": True,
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.namespace],
            ),
        )

    def _install_pyroscope(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        if not config.monitoring.enable_pyroscope:
            return

        self.pyroscope = helm.v3.Release(
            "pyroscope",
            chart="pyroscope",
            version="1.6.0",
            namespace=self._namespace,
            repository_opts={
                "repo": "https://pyroscope.io/helm-charts",
            },
            values={
                "pyroscope": {
                    "resources": {
                        "requests": {
                            "cpu": "500m",
                            "memory": "512Mi",
                        },
                    },
                    "persistence": {
                        "enabled": True,
                        "size": "20Gi",
                    },
                    "extraArgs": [
                        "--log-level=info",
                        "--auth-level=multi-tenant",
                    ],
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.namespace],
            ),
        )

    def _create_alert_rules(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.prometheus_rules = k8s.core.v1.ConfigMap(
            "cfzt-alert-rules",
            metadata={
                "name": "cfzt-alert-rules",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            data={
                "cfzt-rules.yaml": self._get_alert_rules(config),
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.prometheus],
            ),
        )

    def _get_face_ml_dashboard(self) -> dict:
        return {
            "annotations": {"list": []},
            "editable": True,
            "title": "Face ML Dashboard",
            "uid": "face-ml",
            "panels": [
                {
                    "title": "Detection Latency",
                    "type": "graph",
                    "targets": [{"expr": "histogram_quantile(0.99, face_detection_latency_seconds_bucket)"}],
                },
                {
                    "title": "Match Rate",
                    "type": "stat",
                    "targets": [{"expr": "rate(face_match_success_total[5m]) / rate(face_match_attempts_total[5m])"}],
                },
                {
                    "title": "Liveness Score",
                    "type": "gauge",
                    "targets": [{"expr": "avg(face_liveness_score)"}],
                },
            ],
        }

    def _get_quantum_ml_dashboard(self) -> dict:
        return {
            "annotations": {"list": []},
            "editable": True,
            "title": "Quantum ML Dashboard",
            "uid": "quantum-ml",
            "panels": [
                {
                    "title": "Circuit Depth",
                    "type": "graph",
                    "targets": [{"expr": "quantum_circuit_depth"}],
                },
                {
                    "title": "Fidelity",
                    "type": "stat",
                    "targets": [{"expr": "avg(quantum_fidelity)"}],
                },
                {
                    "title": "Qubit Count",
                    "type": "stat",
                    "targets": [{"expr": "quantum_qubit_count"}],
                },
            ],
        }

    def _get_zero_trust_dashboard(self) -> dict:
        return {
            "annotations": {"list": []},
            "editable": True,
            "title": "Zero Trust Dashboard",
            "uid": "zero-trust",
            "panels": [
                {
                    "title": "Auth Failures",
                    "type": "graph",
                    "targets": [{"expr": "rate(auth_failures_total[5m])"}],
                },
                {
                    "title": "Active Sessions",
                    "type": "stat",
                    "targets": [{"expr": "active_sessions_count"}],
                },
                {
                    "title": "Policy Violations",
                    "type": "stat",
                    "targets": [{"expr": "rate(policy_violations_total[5m])"}],
                },
            ],
        }

    def _get_alert_rules(self, config: Config) -> str:
        return """
groups:
  - name: cfzt-face-ml
    rules:
      - alert: FaceDetectionHighLatency
        expr: histogram_quantile(0.99, face_detection_latency_seconds_bucket) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Face detection latency is high"
      - alert: FaceMatchRateLow
        expr: rate(face_match_success_total[5m]) / rate(face_match_attempts_total[5m]) < 0.7
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Face match rate is below threshold"
  - name: cfzt-zero-trust
    rules:
      - alert: HighAuthFailures
        expr: rate(auth_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"
      - alert: PolicyViolationDetected
        expr: rate(policy_violations_total[5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Policy violations detected"
  - name: cfzt-quantum
    rules:
      - alert: QuantumCircuitFailure
        expr: quantum_circuit_failures_total > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Quantum circuit execution failed"
"""

    @property
    def prometheus_endpoint(self) -> pulumi.Output[str]:
        return pulumi.Output.format(
            "http://prometheus-server.{}.svc.cluster.local:9090",
            self._namespace,
        )

    @property
    def grafana_endpoint(self) -> pulumi.Output[str]:
        return pulumi.Output.format(
            "http://grafana.{}.svc.cluster.local:3000",
            self._namespace,
        )

    @property
    def jaeger_endpoint(self) -> pulumi.Output[str]:
        return pulumi.Output.format(
            "http://jaeger-query.{}.svc.cluster.local:16686",
            self._namespace,
        )

    @property
    def loki_endpoint(self) -> pulumi.Output[str]:
        return pulumi.Output.format(
            "http://loki.{}.svc.cluster.local:3100",
            self._namespace,
        )
