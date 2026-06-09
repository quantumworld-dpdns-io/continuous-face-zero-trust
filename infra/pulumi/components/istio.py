from __future__ import annotations

from typing import Any

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import helm, v3

from ..config import Config
from ..utils import get_tag, resource_name


class IstioMesh(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        k8s_provider: k8s.Provider,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:IstioMesh", name, {}, opts)
        self._config = config
        self._k8s_provider = k8s_provider
        self._tags = get_tag(config.project_name, config.environment, {"Component": "istio"})

        self._install_istio(config, opts)
        self._configure_istio(config, opts)
        self._create_observability(config, opts)

    def _install_istio(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        istio_namespace = k8s.core.v1.Namespace(
            "istio-system",
            metadata={
                "name": "istio-system",
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        base_chart = helm.v3.Release(
            "istio-base",
            chart="base",
            version=config.istio.version or "1.20.0",
            namespace="istio-system",
            repository_opts={
                "repo": "https://istio-release.storage.googleapis.com/charts",
            },
            create_namespace=True,
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[istio_namespace],
            ),
        )

        self.pilot = helm.v3.Release(
            "istiod",
            chart="istiod",
            version=config.istio.version or "1.20.0",
            namespace="istio-system",
            repository_opts={
                "repo": "https://istio-release.storage.googleapis.com/charts",
            },
            values={
                "pilot": {
                    "resources": {
                        "requests": {
                            "cpu": "500m",
                            "memory": "2Gi",
                        },
                        "limits": {
                            "cpu": "1000m",
                            "memory": "4Gi",
                        },
                    },
                    "autoscaleEnabled": True,
                    "autoscaleMin": 2,
                    "autoscaleMax": 5,
                    "traceSampling": 100.0 if config.istio.tracing_enabled else 0.0,
                },
                "meshConfig": {
                    "enableTracing": config.istio.tracing_enabled,
                    "defaultConfig": {
                        "tracing": {
                            "zipkin": {
                                "address": f"jaeger-collector.{config.environment}.svc.cluster.local:9411",
                            },
                            "sampling": 100.0 if config.istio.tracing_enabled else 0.0,
                        },
                        "accessLogFile": "/dev/stdout" if config.istio.access_log_enabled else "",
                        "accessLogFormat": '[%START_TIME%] "%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%" %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION% "%REQ(X-FORWARDED-FOR)%" "%REQ(USER-AGENT)%" "%REQ(X-REQUEST-ID)%"',
                    },
                },
                "global": {
                    "mtls": {
                        "enabled": config.istio.mtls_strict,
                    },
                    "proxy": {
                        "resources": {
                            "requests": {
                                "cpu": "100m",
                                "memory": "128Mi",
                            },
                            "limits": {
                                "cpu": "500m",
                                "memory": "256Mi",
                            },
                        },
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[base_chart],
            ),
        )

        self.ingress_gateway = helm.v3.Release(
            "istio-ingressgateway",
            chart="gateway",
            version=config.istio.version or "1.20.0",
            namespace="istio-system",
            repository_opts={
                "repo": "https://istio-release.storage.googleapis.com/charts",
            },
            values={
                "service": {
                    "type": "LoadBalancer",
                    "ports": [
                        {"name": "http2", "port": 80, "targetPort": 8080},
                        {"name": "https", "port": 443, "targetPort": 8443},
                    ],
                },
                "autoscaling": {
                    "enabled": True,
                    "minReplicas": 2,
                    "maxReplicas": 10,
                },
                "resources": {
                    "requests": {
                        "cpu": "200m",
                        "memory": "256Mi",
                    },
                    "limits": {
                        "cpu": "1000m",
                        "memory": "1Gi",
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.pilot],
            ),
        )

        self.eastwest_gateway = helm.v3.Release(
            "istio-eastwestgateway",
            chart="gateway",
            version=config.istio.version or "1.20.0",
            namespace="istio-system",
            repository_opts={
                "repo": "https://istio-release.storage.googleapis.com/charts",
            },
            values={
                "service": {
                    "type": "LoadBalancer",
                    "ports": [
                        {"name": "status-port", "port": 15021, "targetPort": 15021},
                        {"name": "tls", "port": 15443, "targetPort": 15443},
                    ],
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.pilot],
            ),
        )

    def _configure_istio(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.peer_authentication = k8s.core.v1.ConfigMap(
            "istio-peer-authentication",
            metadata={
                "name": "default",
                "namespace": config.environment,
            },
            data={
                "mtls": "STRICT" if config.istio.mtls_strict else "PERMISSIVE",
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.network_policy = k8s.networking.v1.NetworkPolicy(
            "istio-deny-all",
            metadata={
                "name": "deny-all",
                "namespace": config.environment,
            },
            spec={
                "pod_selector": {},
                "policy_types": ["Ingress", "Egress"],
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

    def _create_observability(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        kibana_namespace = k8s.core.v1.Namespace(
            "istio-observability",
            metadata={
                "name": "observability",
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.kiali = helm.v3.Release(
            "kiali",
            chart="kiali-server",
            version="1.75.0",
            namespace="observability",
            repository_opts={
                "repo": "https://kiali.org/helm-charts",
            },
            values={
                "auth": {
                    "strategy": "anonymous",
                },
                "external_services": {
                    "prometheus": {
                        "url": "http://prometheus-server.observability.svc.cluster.local:9090",
                    },
                    "grafana": {
                        "url": "http://grafana.observability.svc.cluster.local:3000",
                    },
                    "tracing": {
                        "url": "http://jaeger-collector.observability.svc.cluster.local:16686",
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[kibana_namespace],
            ),
        )

        self.jaeger = helm.v3.Release(
            "jaeger",
            chart="jaeger",
            version="1.55.0",
            namespace="observability",
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
                },
                "agent": {
                    "enabled": False,
                },
                "storage": {
                    "type": "elasticsearch",
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[kibana_namespace],
            ),
        )

    @property
    def pilot_endpoint(self) -> pulumi.Output[str]:
        return self.pilot.status.apply(lambda s: f"istiod.istio-system.svc.cluster.local:15012")

    @property
    def ingress_endpoint(self) -> pulumi.Output[str]:
        return self.ingress_gateway.status.apply(lambda s: f"istio-ingressgateway.istio-system.svc.cluster.local")
