from __future__ import annotations

from typing import Any

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import helm, v3

from ..config import Config
from ..utils import get_tag, resource_name


class CertificateManager(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        k8s_provider: k8s.Provider,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:CertificateManager", name, {}, opts)
        self._config = config
        self._k8s_provider = k8s_provider
        self._tags = get_tag(config.project_name, config.environment, {"Component": "cert-manager"})
        self._namespace = "cert-manager"

        self._install_cert_manager(config, opts)
        self._create_issuer(config, opts)
        self._create_certificates(config, opts)

    def _install_cert_manager(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cert_manager_namespace = k8s.core.v1.Namespace(
            "cert-manager-namespace",
            metadata={
                "name": self._namespace,
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.cert_manager = helm.v3.Release(
            "cert-manager",
            chart="cert-manager",
            version="1.13.3",
            namespace=self._namespace,
            repository_opts={
                "repo": "https://charts.jetstack.io",
            },
            values={
                "installCRDs": True,
                "replicaCount": 2,
                "resources": {
                    "requests": {
                        "cpu": "50m",
                        "memory": "64Mi",
                    },
                    "limits": {
                        "cpu": "200m",
                        "memory": "256Mi",
                    },
                },
                "webhook": {
                    "replicaCount": 2,
                },
                "cainjector": {
                    "replicaCount": 2,
                    "resources": {
                        "requests": {
                            "cpu": "50m",
                            "memory": "64Mi",
                        },
                        "limits": {
                            "cpu": "200m",
                            "memory": "512Mi",
                        },
                    },
                },
                "prometheus": {
                    "enabled": True,
                    "servicemonitor": {
                        "enabled": True,
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[cert_manager_namespace],
            ),
        )

    def _create_issuer(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        issuer_name = config.certificates.issuer or "letsencrypt-prod"

        if "letsencrypt" in issuer_name:
            self.issuer = k8s.apiextensions.v1.CustomResourceDefinition(
                "letsencrypt-issuer",
                metadata={
                    "name": "clusterissuers.cert-manager.io",
                },
                spec={
                    "group": "cert-manager.io",
                    "names": {
                        "kind": "ClusterIssuer",
                        "listKind": "ClusterIssuerList",
                        "plural": "clusterissuers",
                        "singular": "clusterissuer",
                    },
                    "scope": "Cluster",
                    "versions": [{
                        "name": "v1",
                        "served": True,
                        "storage": True,
                        "schema": {
                            "openAPIV3Schema": {
                                "type": "object",
                                "properties": {
                                    "spec": {
                                        "type": "object",
                                        "properties": {
                                            "acme": {
                                                "type": "object",
                                                "properties": {
                                                    "server": {"type": "string"},
                                                    "email": {"type": "string"},
                                                    "privateKeySecretRef": {"type": "object"},
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    }],
                },
                opts=pulumi.ResourceOptions(
                    provider=self._k8s_provider,
                    parent=self,
                    depends_on=[self.cert_manager],
                ),
            )

            server_url = "https://acme-v02.api.letsencrypt.org/directory"
            if issuer_name == "letsencrypt-staging":
                server_url = "https://acme-staging-v02.api.letsencrypt.org/directory"

            self.cluster_issuer = pulumi.CustomResource(
                f"{issuer_name}-cluster-issuer",
                api_version="cert-manager.io/v1",
                kind="ClusterIssuer",
                metadata={
                    "name": issuer_name,
                },
                spec={
                    "acme": {
                        "server": server_url,
                        "email": config.certificates.email,
                        "privateKeySecretRef": {
                            "name": f"{issuer_name}-account-key",
                        },
                        "solvers": [
                            {
                                "http01": {
                                    "ingress": {
                                        "class": "istio",
                                    },
                                },
                            },
                        ],
                    },
                },
                opts=pulumi.ResourceOptions(
                    provider=self._k8s_provider,
                    parent=self,
                    depends_on=[self.cert_manager],
                ),
            )

    def _create_certificates(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        domain = config.dns.zone_name or "cfzt.example.com"

        self.frontend_cert = pulumi.CustomResource(
            "frontend-tls-cert",
            api_version="cert-manager.io/v1",
            kind="Certificate",
            metadata={
                "name": "frontend-tls",
                "namespace": config.environment,
            },
            spec={
                "secretName": "frontend-tls-secret",
                "issuerRef": {
                    "name": config.certificates.issuer,
                    "kind": "ClusterIssuer",
                },
                "commonName": f"*.{domain}",
                "dnsNames": [
                    domain,
                    f"*.{domain}",
                    f"api.{domain}",
                    f"auth.{domain}",
                    f"face.{domain}",
                ],
                "duration": f"{config.certificates.cert_days or 90}d",
                "renewBefore": f"{config.certificates.renew_days or 30}d",
                "privateKey": {
                    "algorithm": "ECDSA",
                    "size": 256,
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.cluster_issuer] if hasattr(self, 'cluster_issuer') else [self.cert_manager],
            ),
        )

        self.backend_cert = pulumi.CustomResource(
            "backend-tls-cert",
            api_version="cert-manager.io/v1",
            kind="Certificate",
            metadata={
                "name": "backend-tls",
                "namespace": config.environment,
            },
            spec={
                "secretName": "backend-tls-secret",
                "issuerRef": {
                    "name": config.certificates.issuer,
                    "kind": "ClusterIssuer",
                },
                "commonName": f"api.{domain}",
                "dnsNames": [
                    f"api.{domain}",
                    f"auth.{domain}",
                    f"face.{domain}",
                    f"grpc.{domain}",
                ],
                "duration": f"{config.certificates.cert_days or 90}d",
                "renewBefore": f"{config.certificates.renew_days or 30}d",
                "privateKey": {
                    "algorithm": "ECDSA",
                    "size": 256,
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.cluster_issuer] if hasattr(self, 'cluster_issuer') else [self.cert_manager],
            ),
        )

        self.monitoring_cert = pulumi.CustomResource(
            "monitoring-tls-cert",
            api_version="cert-manager.io/v1",
            kind="Certificate",
            metadata={
                "name": "monitoring-tls",
                "namespace": f"monitoring-{config.environment}",
            },
            spec={
                "secretName": "monitoring-tls-secret",
                "issuerRef": {
                    "name": config.certificates.issuer,
                    "kind": "ClusterIssuer",
                },
                "commonName": f"grafana.{domain}",
                "dnsNames": [
                    f"grafana.{domain}",
                    f"prometheus.{domain}",
                    f"jaeger.{domain}",
                ],
                "duration": f"{config.certificates.cert_days or 90}d",
                "renewBefore": f"{config.certificates.renew_days or 30}d",
                "privateKey": {
                    "algorithm": "ECDSA",
                    "size": 256,
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
                depends_on=[self.cluster_issuer] if hasattr(self, 'cluster_issuer') else [self.cert_manager],
            ),
        )

    @property
    def issuer_name(self) -> str:
        return self._config.certificates.issuer or "letsencrypt-prod"

    @property
    def namespace(self) -> str:
        return self._namespace
