from __future__ import annotations

from typing import Any

import pulumi
import pulumi_cloudflare as cloudflare

from ..config import Config
from ..utils import get_tag, resource_name


class DNSManager(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:DNSManager", name, {}, opts)
        self._config = config
        self._tags = get_tag(config.project_name, config.environment, {"Component": "dns"})

        self._create_zone(config, opts)
        self._create_records(config, opts)
        self._create_workers(config, opts)

    def _create_zone(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.zone = cloudflare.Zone(
            "cfzt-zone",
            zone=config.dns.zone_name or "cfzt.example.com",
            account_id=config.cloudflare.account_id,
            plan="free",
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_records(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        domain = config.dns.zone_name or "cfzt.example.com"

        self.api_record = cloudflare.Record(
            "api-record",
            zone_id=self.zone.zone_id,
            name="api",
            type="A",
            value="0.0.0.0",
            proxied=config.dns.dns_proxied,
            ttl=config.dns.ttl_seconds or 300,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.auth_record = cloudflare.Record(
            "auth-record",
            zone_id=self.zone.zone_id,
            name="auth",
            type="A",
            value="0.0.0.0",
            proxied=config.dns.dns_proxied,
            ttl=config.dns.ttl_seconds or 300,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.face_record = cloudflare.Record(
            "face-record",
            zone_id=self.zone.zone_id,
            name="face",
            type="A",
            value="0.0.0.0",
            proxied=config.dns.dns_proxied,
            ttl=config.dns.ttl_seconds or 300,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.grafana_record = cloudflare.Record(
            "grafana-record",
            zone_id=self.zone.zone_id,
            name="grafana",
            type="A",
            value="0.0.0.0",
            proxied=config.dns.dns_proxied,
            ttl=config.dns.ttl_seconds or 300,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.root_record = cloudflare.Record(
            "root-record",
            zone_id=self.zone.zone_id,
            name="@",
            type="A",
            value="0.0.0.0",
            proxied=config.dns.dns_proxied,
            ttl=config.dns.ttl_seconds or 300,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.wildcard_record = cloudflare.Record(
            "wildcard-record",
            zone_id=self.zone.zone_id,
            name="*",
            type="CNAME",
            value=domain,
            proxied=config.dns.dns_proxied,
            ttl=config.dns.ttl_seconds or 300,
            opts=pulumi.ResourceOptions(parent=self),
        )

        if config.dns.enable_dnssec:
            self.dnssec = cloudflare.ZoneDnssec(
                "cfzt-dnssec",
                zone_id=self.zone.zone_id,
                opts=pulumi.ResourceOptions(parent=self),
            )

    def _create_workers(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        if not config.cloudflare.workers_enabled:
            return

        self.auth_worker = cloudflare.WorkerScript(
            "cfzt-auth-worker",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-auth-{config.environment}",
            content="""
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
    const url = new URL(request.url)

    if (url.pathname === '/health') {
        return new Response(JSON.stringify({ status: 'healthy' }), {
            headers: { 'Content-Type': 'application/json' }
        })
    }

    return new Response('CFZT Auth Worker', { status: 200 })
}
""",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.face_worker = cloudflare.WorkerScript(
            "cfzt-face-worker",
            account_id=config.cloudflare.account_id,
            name=f"cfzt-face-{config.environment}",
            content="""
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
    const url = new URL(request.url)

    if (url.pathname === '/health') {
        return new Response(JSON.stringify({ status: 'healthy' }), {
            headers: { 'Content-Type': 'application/json' }
        })
    }

    return new Response('CFZT Face Worker', { status: 200 })
}
""",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.kv_namespace = cloudflare.WorkersKvNamespace(
            "cfzt-kv-namespace",
            account_id=config.cloudflare.account_id,
            title=config.cloudflare.kv_namespace or "cfzt-kv",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.r2_bucket = cloudflare.R2Bucket(
            "cfzt-r2-bucket",
            account_id=config.cloudflare.account_id,
            name=config.cloudflare.r2_bucket or "cfzt-r2",
            opts=pulumi.ResourceOptions(parent=self),
        )

        if config.cloudflare.do_enabled:
            self.do_namespace = cloudflare.WorkersDurableObjectNamespace(
                "cfzt-do-namespace",
                account_id=config.cloudflare.account_id,
                title=f"cfzt-do-{config.environment}",
                opts=pulumi.ResourceOptions(parent=self),
            )

        if config.cloudflare.turnstile_enabled:
            self.turnstile = cloudflare.TurnstileWidget(
                "cfzt-turnstile",
                account_id=config.cloudflare.account_id,
                name=f"cfzt-turnstile-{config.environment}",
                mode="managed",
                opts=pulumi.ResourceOptions(parent=self),
            )

    @property
    def zone_id(self) -> pulumi.Output[str]:
        return self.zone.zone_id

    @property
    def nameservers(self) -> pulumi.Output[list[str]]:
        return self.zone.name_servers
