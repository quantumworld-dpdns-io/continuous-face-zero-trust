from __future__ import annotations

import re
import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


THREAT_DETECTIONS = Counter(
    "threat_detection_total",
    "Total threat detections",
    labelnames=["rule_name", "severity", "action"],
)

THREAT_RULE_HITS = Counter(
    "threat_rule_hits_total",
    "Total threat rule hits",
    labelnames=["rule_name"],
)

THREAT_FALSE_POSITIVES = Counter(
    "threat_false_positives_total",
    "Total false positive threats",
    labelnames=["rule_name"],
)

THREAT_LATENCY = Histogram(
    "threat_detection_latency_seconds",
    "Latency of threat detection",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    labelnames=["rule_name"],
)

THREAT_ACTIVE_RULES = Gauge(
    "threat_active_rules",
    "Number of active threat detection rules",
)


class ThreatDetector:
    def __init__(self):
        self.rules: list[dict[str, Any]] = []
        self.detection_history: list[dict[str, Any]] = []
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        self.add_rule(
            name="brute_force_login",
            description="Detects brute force login attempts",
            severity="high",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "authentication" and
                event.get("status") == "failed" and
                self._count_recent_events(event.get("user_id"), "authentication", "failed", 300) > 5
            ),
        )

        self.add_rule(
            name="credential_stuffing",
            description="Detects credential stuffing attacks",
            severity="critical",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "authentication" and
                event.get("status") == "failed" and
                self._count_recent_events(event.get("ip_address"), "authentication", "failed", 600) > 20
            ),
        )

        self.add_rule(
            name="impossible_travel",
            description="Detects impossible travel scenarios",
            severity="high",
            action="challenge",
            condition=lambda event: (
                event.get("event_type") == "authentication" and
                event.get("status") == "success" and
                self._check_impossible_travel(event)
            ),
        )

        self.add_rule(
            name="biometric_spoofing",
            description="Detects potential biometric spoofing attempts",
            severity="critical",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "biometric" and
                event.get("liveness_score", 1.0) < 0.5
            ),
        )

        self.add_rule(
            name="session_hijacking",
            description="Detects potential session hijacking",
            severity="high",
            action="revoke",
            condition=lambda event: (
                event.get("event_type") == "session" and
                self._check_session_anomaly(event)
            ),
        )

        self.add_rule(
            name="sql_injection",
            description="Detects SQL injection attempts",
            severity="critical",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "request" and
                self._check_sql_injection(event)
            ),
        )

        self.add_rule(
            name="xss_attack",
            description="Detects XSS attack attempts",
            severity="high",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "request" and
                self._check_xss(event)
            ),
        )

        self.add_rule(
            name="privilege_escalation",
            description="Detects privilege escalation attempts",
            severity="critical",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "authorization" and
                event.get("status") == "denied" and
                self._count_recent_events(event.get("user_id"), "authorization", "denied", 3600) > 3
            ),
        )

        self.add_rule(
            name="data_exfiltration",
            description="Detects potential data exfiltration",
            severity="critical",
            action="block",
            condition=lambda event: (
                event.get("event_type") == "data_access" and
                event.get("bytes_transferred", 0) > 10485760
            ),
        )

        self.add_rule(
            name="anomalous_api_usage",
            description="Detects anomalous API usage patterns",
            severity="medium",
            action="alert",
            condition=lambda event: (
                event.get("event_type") == "api_request" and
                self._check_api_anomaly(event)
            ),
        )

        THREAT_ACTIVE_RULES.set(len(self.rules))

    def add_rule(
        self,
        name: str,
        description: str,
        severity: str,
        action: str,
        condition: callable,
    ) -> None:
        self.rules.append({
            "name": name,
            "description": description,
            "severity": severity,
            "action": action,
            "condition": condition,
            "enabled": True,
            "created_at": time.time(),
        })
        THREAT_ACTIVE_RULES.set(len(self.rules))

    def remove_rule(self, name: str) -> bool:
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r["name"] != name]
        removed = len(self.rules) < initial_count
        if removed:
            THREAT_ACTIVE_RULES.set(len(self.rules))
        return removed

    def enable_rule(self, name: str) -> bool:
        for rule in self.rules:
            if rule["name"] == name:
                rule["enabled"] = True
                return True
        return False

    def disable_rule(self, name: str) -> bool:
        for rule in self.rules:
            if rule["name"] == name:
                rule["enabled"] = False
                return True
        return False

    def detect(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        detections = []
        start_time = time.time()

        for rule in self.rules:
            if not rule["enabled"]:
                continue

            try:
                if rule["condition"](event):
                    detection = {
                        "rule_name": rule["name"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "action": rule["action"],
                        "event": event,
                        "detected_at": time.time(),
                    }
                    detections.append(detection)

                    THREAT_DETECTIONS.labels(
                        rule_name=rule["name"],
                        severity=rule["severity"],
                        action=rule["action"],
                    ).inc()
                    THREAT_RULE_HITS.labels(rule_name=rule["name"]).inc()

                    self.detection_history.append(detection)
                    if len(self.detection_history) > 10000:
                        self.detection_history = self.detection_history[-10000:]

            except Exception as e:
                pass

        duration = time.time() - start_time
        THREAT_LATENCY.labels(rule_name="all").observe(duration)

        return detections

    def _count_recent_events(
        self,
        identifier: str,
        event_type: str,
        status: str,
        window_seconds: int,
    ) -> int:
        cutoff_time = time.time() - window_seconds
        count = 0

        for detection in reversed(self.detection_history):
            if detection["detected_at"] < cutoff_time:
                break

            event = detection.get("event", {})
            if (
                event.get("event_type") == event_type and
                event.get("status") == status and
                (event.get("user_id") == identifier or event.get("ip_address") == identifier)
            ):
                count += 1

        return count

    def _check_impossible_travel(self, event: dict[str, Any]) -> bool:
        return False

    def _check_session_anomaly(self, event: dict[str, Any]) -> bool:
        return False

    def _check_sql_injection(self, event: dict[str, Any]) -> bool:
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
            r"(--|;|'|\")",
            r"(\bOR\b\s+\b1\b\s*=\s*\b1\b)",
            r"(\bAND\b\s+\b1\b\s*=\s*\b1\b)",
        ]

        request_data = event.get("details", {}).get("request_data", "")
        for pattern in sql_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                return True
        return False

    def _check_xss(self, event: dict[str, Any]) -> bool:
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]

        request_data = event.get("details", {}).get("request_data", "")
        for pattern in xss_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                return True
        return False

    def _check_api_anomaly(self, event: dict[str, Any]) -> bool:
        return False

    def get_detections(
        self,
        rule_name: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        detections = self.detection_history

        if rule_name:
            detections = [d for d in detections if d["rule_name"] == rule_name]

        if severity:
            detections = [d for d in detections if d["severity"] == severity]

        return detections[-limit:]

    def get_detection_stats(self) -> dict[str, Any]:
        total = len(self.detection_history)
        if total == 0:
            return {"total": 0, "by_severity": {}, "by_rule": {}}

        by_severity = {}
        by_rule = {}

        for detection in self.detection_history:
            severity = detection["severity"]
            rule_name = detection["rule_name"]

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_rule[rule_name] = by_rule.get(rule_name, 0) + 1

        return {
            "total": total,
            "by_severity": by_severity,
            "by_rule": by_rule,
            "active_rules": len([r for r in self.rules if r["enabled"]]),
        }

    def export_rules(self) -> list[dict[str, Any]]:
        return [
            {
                "name": r["name"],
                "description": r["description"],
                "severity": r["severity"],
                "action": r["action"],
                "enabled": r["enabled"],
            }
            for r in self.rules
        ]
