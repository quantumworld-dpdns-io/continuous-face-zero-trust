from __future__ import annotations

import json
import time
from typing import Any

import httpx
from prometheus_client import Counter, Gauge, Histogram


SIEM_EVENTS_SENT = Counter(
    "siem_events_sent_total",
    "Total SIEM events sent",
    labelnames=["siem_type", "status"],
)

SIEM_EVENTS_FAILED = Counter(
    "siem_events_failed_total",
    "Total SIEM events failed to send",
    labelnames=["siem_type", "error_type"],
)

SIEM_SEND_LATENCY = Histogram(
    "siem_send_latency_seconds",
    "Latency of SIEM event sending",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["siem_type"],
)

SIEM_QUEUE_SIZE = Gauge(
    "siem_queue_size",
    "Size of SIEM event queue",
    labelnames=["siem_type"],
)


class SIEMForwarder:
    def __init__(
        self,
        splunk_host: str | None = None,
        splunk_port: int = 8088,
        splunk_token: str | None = None,
        datadog_api_key: str | None = None,
        datadog_app_key: str | None = None,
        elk_host: str | None = None,
        elk_port: int = 9200,
    ):
        self.splunk_host = splunk_host
        self.splunk_port = splunk_port
        self.splunk_token = splunk_token
        self.datadog_api_key = datadog_api_key
        self.datadog_app_key = datadog_app_key
        self.elk_host = elk_host
        self.elk_port = elk_port
        self.event_queue: list[dict[str, Any]] = []

    def send_to_splunk(
        self,
        event: dict[str, Any],
        source: str = "cfzt",
        sourcetype: str = "cfzt:security",
    ) -> bool:
        if not self.splunk_host:
            return False

        start_time = time.time()

        try:
            payload = {
                "event": event,
                "source": source,
                "sourcetype": sourcetype,
                "time": time.time(),
            }

            with httpx.Client() as client:
                response = client.post(
                    f"https://{self.splunk_host}:{self.splunk_port}/services/collector/event",
                    json=payload,
                    headers={
                        "Authorization": f"Splunk {self.splunk_token}",
                        "Content-Type": "application/json",
                    },
                    verify=False,
                    timeout=10.0,
                )
                response.raise_for_status()

            SIEM_EVENTS_SENT.labels(siem_type="splunk", status="success").inc()
            duration = time.time() - start_time
            SIEM_SEND_LATENCY.labels(siem_type="splunk").observe(duration)
            return True

        except Exception as e:
            SIEM_EVENTS_FAILED.labels(siem_type="splunk", error_type=type(e).__name__).inc()
            SIEM_EVENTS_SENT.labels(siem_type="splunk", status="error").inc()
            return False

    def send_to_datadog(
        self,
        event: dict[str, Any],
        title: str = "CFZT Security Event",
        text: str = "",
        alert_type: str = "info",
        tags: list[str] | None = None,
    ) -> bool:
        if not self.datadog_api_key:
            return False

        start_time = time.time()

        try:
            payload = {
                "title": title,
                "text": text or json.dumps(event),
                "alert_type": alert_type,
                "tags": tags or [],
                "source_type_name": "cfzt",
                "host": "cfzt-security",
                "priority": "normal",
            }

            with httpx.Client() as client:
                response = client.post(
                    f"https://api.datadoghq.com/api/v1/events",
                    json=payload,
                    headers={
                        "DD-API-KEY": self.datadog_api_key,
                        "DD-APPLICATION-KEY": self.datadog_app_key or "",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

            SIEM_EVENTS_SENT.labels(siem_type="datadog", status="success").inc()
            duration = time.time() - start_time
            SIEM_SEND_LATENCY.labels(siem_type="datadog").observe(duration)
            return True

        except Exception as e:
            SIEM_EVENTS_FAILED.labels(siem_type="datadog", error_type=type(e).__name__).inc()
            SIEM_EVENTS_SENT.labels(siem_type="datadog", status="error").inc()
            return False

    def send_to_elk(
        self,
        event: dict[str, Any],
        index: str = "cfzt-security",
        doc_type: str = "_doc",
    ) -> bool:
        if not self.elk_host:
            return False

        start_time = time.time()

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"http://{self.elk_host}:{self.elk_port}/{index}/{doc_type}",
                    json=event,
                    headers={
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

            SIEM_EVENTS_SENT.labels(siem_type="elk", status="success").inc()
            duration = time.time() - start_time
            SIEM_SEND_LATENCY.labels(siem_type="elk").observe(duration)
            return True

        except Exception as e:
            SIEM_EVENTS_FAILED.labels(siem_type="elk", error_type=type(e).__name__).inc()
            SIEM_EVENTS_SENT.labels(siem_type="elk", status="error").inc()
            return False

    def forward_event(
        self,
        event: dict[str, Any],
        siem_types: list[str] | None = None,
        **kwargs,
    ) -> dict[str, bool]:
        results = {}
        target_siem = siem_types or ["splunk", "datadog", "elk"]

        for siem_type in target_siem:
            if siem_type == "splunk":
                results["splunk"] = self.send_to_splunk(event, **kwargs)
            elif siem_type == "datadog":
                results["datadog"] = self.send_to_datadog(event, **kwargs)
            elif siem_type == "elk":
                results["elk"] = self.send_to_elk(event, **kwargs)

        return results

    def queue_event(self, event: dict[str, Any]) -> None:
        self.event_queue.append({
            "event": event,
            "queued_at": time.time(),
        })
        SIEM_QUEUE_SIZE.labels(siem_type="queue").set(len(self.event_queue))

    def flush_queue(self, siem_types: list[str] | None = None) -> dict[str, int]:
        results = {"sent": 0, "failed": 0}

        while self.event_queue:
            item = self.event_queue.pop(0)
            send_results = self.forward_event(item["event"], siem_types)

            if any(send_results.values()):
                results["sent"] += 1
            else:
                results["failed"] += 1

        SIEM_QUEUE_SIZE.labels(siem_type="queue").set(len(self.event_queue))
        return results

    def create_security_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        details: dict[str, Any] | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "severity": severity,
            "source": source,
            "timestamp": time.time(),
            "details": details or {},
            "user_id": user_id,
            "ip_address": ip_address,
            "environment": "production",
            "service": "continuous-face-zero-trust",
        }

    def create_auth_event(
        self,
        user_id: str,
        action: str,
        status: str,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.create_security_event(
            event_type="authentication",
            severity="info" if status == "success" else "warning",
            source="auth-service",
            details={
                "action": action,
                "status": status,
                **(details or {}),
            },
            user_id=user_id,
            ip_address=ip_address,
        )

    def create_biometric_event(
        self,
        user_id: str,
        action: str,
        status: str,
        confidence: float,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.create_security_event(
            event_type="biometric",
            severity="info" if status == "success" else "warning",
            source="face-ml-service",
            details={
                "action": action,
                "status": status,
                "confidence": confidence,
                **(details or {}),
            },
            user_id=user_id,
            ip_address=ip_address,
        )

    def create_policy_violation_event(
        self,
        policy_name: str,
        violation_type: str,
        severity: str,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.create_security_event(
            event_type="policy_violation",
            severity=severity,
            source="zero-trust-engine",
            details={
                "policy_name": policy_name,
                "violation_type": violation_type,
                **(details or {}),
            },
            ip_address=ip_address,
        )
