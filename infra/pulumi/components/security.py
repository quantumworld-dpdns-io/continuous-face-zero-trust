from __future__ import annotations

from typing import Any

import pulumi
import pulumi_kubernetes as k8s

from ..config import Config
from ..utils import get_tag, resource_name


class SecurityPolicies(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        k8s_provider: k8s.Provider,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:SecurityPolicies", name, {}, opts)
        self._config = config
        self._k8s_provider = k8s_provider
        self._tags = get_tag(config.project_name, config.environment, {"Component": "security"})
        self._namespace = config.environment

        self._create_network_policies(config, opts)
        self._create_pod_security_policies(config, opts)
        self._create_waf_rules(config, opts)
        self._create_rbac(config, opts)
        self._create_secrets(config, opts)

    def _create_network_policies(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.default_deny = k8s.networking.v1.NetworkPolicy(
            "default-deny-all",
            metadata={
                "name": "default-deny-all",
                "namespace": self._namespace,
                "labels": self._tags,
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

        self.allow_dns = k8s.networking.v1.NetworkPolicy(
            "allow-dns",
            metadata={
                "name": "allow-dns",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            spec={
                "pod_selector": {},
                "policy_types": ["Egress"],
                "egress": [{
                    "to": [{"namespace_selector": {}}],
                    "ports": [{"protocol": "UDP", "port": 53}],
                }],
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.allow_api_server = k8s.networking.v1.NetworkPolicy(
            "allow-api-server",
            metadata={
                "name": "allow-api-server",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            spec={
                "pod_selector": {
                    "match_labels": {"app": "api-server"},
                },
                "policy_types": ["Ingress", "Egress"],
                "ingress": [{
                    "from": [
                        {
                            "namespace_selector": {
                                "match_labels": {"name": "istio-system"},
                            },
                        },
                    ],
                    "ports": [{"protocol": "TCP", "port": 8443}],
                }],
                "egress": [
                    {
                        "to": [{"namespace_selector": {}}],
                        "ports": [{"protocol": "TCP", "port": 443}],
                    },
                    {
                        "to": [{"namespace_selector": {"match_labels": {"name": "data"}}}],
                        "ports": [{"protocol": "TCP", "port": 6379}, {"protocol": "TCP", "port": 6333}],
                    },
                ],
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.allow_auth_server = k8s.networking.v1.NetworkPolicy(
            "allow-auth-server",
            metadata={
                "name": "allow-auth-server",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            spec={
                "pod_selector": {
                    "match_labels": {"app": "auth-server"},
                },
                "policy_types": ["Ingress", "Egress"],
                "ingress": [{
                    "from": [
                        {
                            "namespace_selector": {
                                "match_labels": {"name": "istio-system"},
                            },
                        },
                    ],
                    "ports": [{"protocol": "TCP", "port": 8443}],
                }],
                "egress": [
                    {
                        "to": [{"namespace_selector": {}}],
                        "ports": [{"protocol": "TCP", "port": 443}],
                    },
                ],
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.allow_face_ml = k8s.networking.v1.NetworkPolicy(
            "allow-face-ml",
            metadata={
                "name": "allow-face-ml",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            spec={
                "pod_selector": {
                    "match_labels": {"app": "face-ml"},
                },
                "policy_types": ["Ingress", "Egress"],
                "ingress": [{
                    "from": [
                        {
                            "namespace_selector": {
                                "match_labels": {"name": "istio-system"},
                            },
                        },
                    ],
                    "ports": [{"protocol": "TCP", "port": 8443}],
                }],
                "egress": [
                    {
                        "to": [{"namespace_selector": {}}],
                        "ports": [{"protocol": "TCP", "port": 443}],
                    },
                    {
                        "to": [{"namespace_selector": {"match_labels": {"name": "data"}}}],
                        "ports": [{"protocol": "TCP", "port": 6333}],
                    },
                ],
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.allow_monitoring = k8s.networking.v1.NetworkPolicy(
            "allow-monitoring",
            metadata={
                "name": "allow-monitoring",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            spec={
                "pod_selector": {
                    "match_labels": {"app.kubernetes.io/name": "prometheus"},
                },
                "policy_types": ["Ingress", "Egress"],
                "ingress": [{
                    "from": [{"namespace_selector": {}}],
                    "ports": [{"protocol": "TCP", "port": 9090}],
                }],
                "egress": [{
                    "from": [{"namespace_selector": {}}],
                    "ports": [{"protocol": "TCP", "port": 8080}],
                }],
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

    def _create_pod_security_policies(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.restricted_psa = k8s.core.v1.Namespace(
            "restricted-psa",
            metadata={
                "name": self._namespace,
                "labels": {
                    **self._tags,
                    "pod-security.kubernetes.io/enforce": "restricted",
                    "pod-security.kubernetes.io/audit": "restricted",
                    "pod-security.kubernetes.io/warn": "restricted",
                },
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

    def _create_waf_rules(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.waf_config = {
            "enabled": config.security.waf_enabled,
            "rules": [
                {
                    "name": "block-sql-injection",
                    "action": "block",
                    "priority": 1,
                    "expression": "contains(lower(request.uri.path), 'union select') or contains(lower(request.uri.path), 'drop table')",
                },
                {
                    "name": "block-xss",
                    "action": "block",
                    "priority": 2,
                    "expression": "contains(request.uri.path, '<script') or contains(request.uri.query, '<script')",
                },
                {
                    "name": "rate-limit-auth",
                    "action": "challenge",
                    "priority": 3,
                    "expression": "http.request.uri.path eq '/api/auth/login' and http.request.method eq 'POST'",
                    "rate_limit": {
                        "requests": config.security.max_failed_auth_attempts or 5,
                        "period": "60s",
                    },
                },
                {
                    "name": "block-scrapers",
                    "action": "block",
                    "priority": 4,
                    "expression": "cf.bot_management.score lt 30",
                },
                {
                    "name": "geo-block",
                    "action": "block",
                    "priority": 5,
                    "expression": "not ip.geoip.country in {'US' 'CA' 'GB' 'DE' 'FR' 'JP' 'AU'}",
                },
                {
                    "name": "block-bad-bots",
                    "action": "block",
                    "priority": 6,
                    "expression": "cf.bot_management.verified_bot eq false and cf.bot_management.score lt 20",
                },
                {
                    "name": "protect-biometric-endpoints",
                    "action": "managed_challenge",
                    "priority": 7,
                    "expression": "http.request.uri.path contains '/api/face/' or http.request.uri.path contains '/api/biometric/'",
                },
            ],
        }

    def _create_rbac(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.service_account = k8s.core.v1.ServiceAccount(
            "cfzt-service-account",
            metadata={
                "name": "cfzt-sa",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.cluster_role = k8s.rbac.v1.ClusterRole(
            "cfzt-cluster-role",
            metadata={
                "name": f"cfzt-{config.environment}-role",
                "labels": self._tags,
            },
            rules=[
                {
                    "apiGroups": [""],
                    "resources": ["pods", "services", "configmaps", "secrets"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["deployments", "replicasets"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["networking.k8s.io"],
                    "resources": ["networkpolicies"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.role_binding = k8s.rbac.v1.RoleBinding(
            "cfzt-role-binding",
            metadata={
                "name": f"cfzt-{config.environment}-binding",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            role_ref={
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": f"cfzt-{config.environment}-role",
            },
            subjects=[{
                "kind": "ServiceAccount",
                "name": "cfzt-sa",
                "namespace": self._namespace,
            }],
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

    def _create_secrets(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.jwt_secret = k8s.core.v1.Secret(
            "jwt-secret",
            metadata={
                "name": "jwt-secret",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            type="Opaque",
            string_data={
                "jwt-secret": "change-me-in-production",
                "jwt-algorithm": "HS256",
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.db_secret = k8s.core.v1.Secret(
            "db-secret",
            metadata={
                "name": "db-secret",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            type="Opaque",
            string_data={
                "db-host": "postgres.cfzt-data.svc.cluster.local",
                "db-port": "5432",
                "db-name": "cfzt",
                "db-user": "cfzt_app",
                "db-password": "change-me-in-production",
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

        self.redis_secret = k8s.core.v1.Secret(
            "redis-secret",
            metadata={
                "name": "redis-secret",
                "namespace": self._namespace,
                "labels": self._tags,
            },
            type="Opaque",
            string_data={
                "redis-host": "redis.cfzt-data.svc.cluster.local",
                "redis-port": "6379",
                "redis-password": "change-me-in-production",
            },
            opts=pulumi.ResourceOptions(
                provider=self._k8s_provider,
                parent=self,
            ),
        )

    @property
    def network_policies(self) -> dict:
        return {
            "default_deny": self.default_deny,
            "allow_dns": self.allow_dns,
            "allow_api": self.allow_api_server,
            "allow_auth": self.allow_auth_server,
            "allow_face_ml": self.allow_face_ml,
            "allow_monitoring": self.allow_monitoring,
        }
