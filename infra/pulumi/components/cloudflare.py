from __future__ import annotations

from typing import Any

import pulumi
import pulumi_cloudflare as cloudflare

from ..config import Config
from ..utils import get_tag, resource_name


class CloudflareResources(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:CloudflareResources", name, {}, opts)
        self._config = config
        self._tags = get_tag(config.project_name, config.environment, {"Component": "cloudflare"})

        self._create_workers(config, opts)
        self._create_kv(config, opts)
        self._create_r2(config, opts)
        self._create_durable_objects(config, opts)
        self._create_turnstile(config, opts)
        self._create_security_rules(config, opts)

    def _create_workers(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.auth_worker = cloudflare.WorkerScript(
            "cfzt-auth-worker",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-auth-{config.environment}",
            content="""
import { WorkerEntrypoint } from 'cloudflare:workers';

export default class AuthWorker extends WorkerEntrypoint {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);

        if (url.pathname === '/health') {
            return new Response(JSON.stringify({ status: 'healthy', service: 'auth' }), {
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (url.pathname === '/api/auth/validate-token') {
            const token = request.headers.get('Authorization')?.replace('Bearer ', '');
            if (!token) {
                return new Response(JSON.stringify({ error: 'No token provided' }), { status: 401 });
            }

            try {
                const payload = await this.validateJWT(token, env.JWT_SECRET);
                return new Response(JSON.stringify({ valid: true, user: payload }), {
                    headers: { 'Content-Type': 'application/json' }
                });
            } catch (e) {
                return new Response(JSON.stringify({ valid: false, error: e.message }), { status: 401 });
            }
        }

        return new Response('CFZT Auth Worker', { status: 200 });
    }

    async validateJWT(token, secret) {
        const [header, payload, signature] = token.split('.');
        const encoder = new TextEncoder();
        const key = await crypto.subtle.importKey(
            'raw',
            encoder.encode(secret),
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['verify']
        );
        const valid = await crypto.subtle.verify(
            'HMAC',
            key,
            Uint8Array.from(atob(signature.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0)),
            encoder.encode(`${header}.${payload}`)
        );
        if (!valid) throw new Error('Invalid signature');
        return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    }
}
""",
            bindings=[
                {
                    "name": "KV_NAMESPACE",
                    "type": "kv_namespace",
                    "kv_namespace_binding": "cfzt-kv",
                },
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.face_worker = cloudflare.WorkerScript(
            "cfzt-face-worker",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-face-{config.environment}",
            content="""
import { WorkerEntrypoint } from 'cloudflare:workers';

export default class FaceWorker extends WorkerEntrypoint {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);

        if (url.pathname === '/health') {
            return new Response(JSON.stringify({ status: 'healthy', service: 'face-ml' }), {
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (url.pathname === '/api/face/verify' && request.method === 'POST') {
            const formData = await request.formData();
            const image = formData.get('image');
            if (!image) {
                return new Response(JSON.stringify({ error: 'No image provided' }), { status: 400 });
            }

            const result = await this.verifyFace(image, env);
            return new Response(JSON.stringify(result), {
                headers: { 'Content-Type': 'application/json' }
            });
        }

        return new Response('CFZT Face Worker', { status: 200 });
    }

    async verifyFace(image, env) {
        return {
            verified: true,
            confidence: 0.95,
            liveness: true,
            timestamp: new Date().toISOString()
        };
    }
}
""",
            bindings=[
                {
                    "name": "R2_BUCKET",
                    "type": "r2_bucket",
                    "r2_bucket_binding": "cfzt-r2",
                },
                {
                    "name": "DO_NAMESPACE",
                    "type": "durable_object_namespace",
                    "durable_object_namespace_binding": "cfzt-do",
                },
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.api_worker = cloudflare.WorkerScript(
            "cfzt-api-worker",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-api-{config.environment}",
            content="""
import { WorkerEntrypoint } from 'cloudflare:workers';

export default class ApiWorker extends WorkerEntrypoint {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);

        if (url.pathname === '/health') {
            return new Response(JSON.stringify({ status: 'healthy', service: 'api' }), {
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const corsHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        };

        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders });
        }

        return new Response(JSON.stringify({ message: 'CFZT API' }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
}
""",
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_kv(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.kv_namespace = cloudflare.WorkersKvNamespace(
            "cfzt-kv-namespace",
            account_id=config.cloudflare.account_id,
            title=config.cloudflare.kv_namespace or f"cfzt-kv-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.session_kv = cloudflare.WorkersKvNamespace(
            "cfzt-session-kv",
            account_id=config.cloudflare.account_id,
            title=f"cfzt-sessions-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cache_kv = cloudflare.WorkersKvNamespace(
            "cfzt-cache-kv",
            account_id=config.cloudflare.account_id,
            title=f"cfzt-cache-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cache_config = cloudflare.WorkersKvNamespaceConfiguration(
            "cfzt-cache-config",
            account_id=config.cloudflare.account_id,
            namespace_id=self.cache_kv.id,
            config={
                "binding": "CFZT_CACHE",
                "namespace_id": self.cache_kv.id,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_r2(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.r2_bucket = cloudflare.R2Bucket(
            "cfzt-r2-bucket",
            account_id=config.cloudflare.account_id,
            name=config.cloudflare.r2_bucket or f"cfzt-r2-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.r2_images_bucket = cloudflare.R2Bucket(
            "cfzt-r2-images",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-images-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.r2_audit_bucket = cloudflare.R2Bucket(
            "cfzt-r2-audit",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-audit-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.r2_lifecycle = cloudflare.R2BucketLifecycle(
            "cfzt-r2-lifecycle",
            account_id=config.cloudflare.account_id,
            bucket_name=self.r2_bucket.name,
            rules=[{
                "enabled": True,
                "id": "cleanup-old-versions",
                "expiration": {"days": 90},
                "abort_initiated_multipart_upload": {"days": 7},
            }],
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_durable_objects(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        if not config.cloudflare.do_enabled:
            return

        self.do_namespace = cloudflare.WorkersDurableObjectNamespace(
            "cfzt-do-namespace",
            account_id=config.cloudflare.account_id,
            title=f"cfzt-do-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.session_do = cloudflare.WorkersDurableObjectNamespace(
            "cfzt-session-do",
            account_id=config.cloudflare.account_id,
            title=f"cfzt-sessions-do-{config.environment}",
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_turnstile(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        if not config.cloudflare.turnstile_enabled:
            return

        self.turnstile_widget = cloudflare.TurnstileWidget(
            "cfzt-turnstile-widget",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-turnstile-{config.environment}",
            mode="managed",
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_security_rules(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.waf_rule = cloudflare.Ruleset(
            "cfzt-waf-ruleset",
            account_id=config.cloudflare.account_id,
            kind="zone",
            name=f"cfzt-waf-{config.environment}",
            phase="http_request_firewall_custom",
            rules=[
                {
                    "action": "challenge",
                    "expression": "(http.request.uri.path contains \"/api/auth/\") and (http.request.method eq \"POST\")",
                    "description": "Challenge auth requests",
                },
                {
                    "action": "block",
                    "expression": "(cf.bot_management.score lt 10) and (not cf.bot_management.verified_bot)",
                    "description": "Block bad bots",
                },
                {
                    "action": "managed_challenge",
                    "expression": "(http.request.uri.path contains \"/api/face/\") or (http.request.uri.path contains \"/api/biometric/\")",
                    "description": "Managed challenge for biometric endpoints",
                },
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.rate_limit_rule = cloudflare.Ruleset(
            "cfzt-rate-limit-ruleset",
            account_id=config.cloudflare.account_id,
            kind="zone",
            name=f"cfzt-rate-limit-{config.environment}",
            phase="http_request_firewall_custom",
            rules=[
                {
                    "action": "managed_challenge",
                    "expression": "(http.request.uri.path eq \"/api/auth/login\") and (http.request.method eq \"POST\")",
                    "rate_limit": {
                        "requests_per_period": 5,
                        "period": 60,
                        "mitigation_timeout": 600,
                    },
                    "description": "Rate limit login attempts",
                },
                {
                    "action": "managed_challenge",
                    "expression": "(http.request.uri.path contains \"/api/\") and (not cf.bot_management.verified_bot)",
                    "rate_limit": {
                        "requests_per_period": 100,
                        "period": 60,
                        "mitigation_timeout": 300,
                    },
                    "description": "Rate limit API requests",
                },
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

    @property
    def worker_urls(self) -> dict:
        return {
            "auth": self.auth_worker.subdomain if hasattr(self.auth_worker, 'subdomain') else "",
            "face": self.face_worker.subdomain if hasattr(self.face_worker, 'subdomain') else "",
            "api": self.api_worker.subdomain if hasattr(self.api_worker, 'subdomain') else "",
        }

    @property
    def kv_namespaces(self) -> dict:
        return {
            "main": self.kv_namespace.id if hasattr(self, 'kv_namespace') else "",
            "sessions": self.session_kv.id if hasattr(self, 'session_kv') else "",
            "cache": self.cache_kv.id if hasattr(self, 'cache_kv') else "",
        }

    @property
    def r2_buckets(self) -> dict:
        return {
            "main": self.r2_bucket.name if hasattr(self, 'r2_bucket') else "",
            "images": self.r2_images_bucket.name if hasattr(self, 'r2_images_bucket') else "",
            "audit": self.r2_audit_bucket.name if hasattr(self, 'r2_audit_bucket') else "",
        }
