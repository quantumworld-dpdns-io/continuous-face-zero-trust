from __future__ import annotations

import json
import time
import uuid
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


INCIDENT_COUNTER = Counter(
    "incident_total",
    "Total incidents",
    labelnames=["severity", "status"],
)

INCIDENT_RESPONSE_TIME = Histogram(
    "incident_response_time_seconds",
    "Incident response time",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
    labelnames=["severity"],
)

INCIDENT_RESOLUTION_TIME = Histogram(
    "incident_resolution_time_seconds",
    "Incident resolution time",
    buckets=[60.0, 300.0, 600.0, 1800.0, 3600.0, 7200.0],
    labelnames=["severity"],
)

INCIDENT_PLAYBOOK_EXECUTIONS = Counter(
    "incident_playbook_executions_total",
    "Total incident playbook executions",
    labelnames=["playbook_name", "status"],
)

INCIDENT_ACTIVE = Gauge(
    "incident_active_count",
    "Number of active incidents",
)


class IncidentResponder:
    def __init__(self):
        self.playbooks: dict[str, dict[str, Any]] = {}
        self.incidents: dict[str, dict[str, Any]] = {}
        self._register_default_playbooks()

    def _register_default_playbooks(self) -> None:
        self.register_playbook(
            name="brute_force_response",
            description="Respond to brute force attack",
            severity="high",
            steps=[
                {"action": "block_ip", "params": {"duration": 3600}},
                {"action": "notify_security_team", "params": {"channel": "security-alerts"}},
                {"action": "enable_enhanced_monitoring", "params": {"duration": 86400}},
                {"action": "force_password_reset", "params": {"user_id": "{user_id}"}},
            ],
        )

        self.register_playbook(
            name="data_breach_response",
            description="Respond to data breach",
            severity="critical",
            steps=[
                {"action": "isolate_affected_systems", "params": {}},
                {"action": "preserve_evidence", "params": {}},
                {"action": "notify_incident_commander", "params": {}},
                {"action": "assess_scope", "params": {}},
                {"action": "notify_authorities", "params": {"timeline": "72h"}},
                {"action": "notify_affected_users", "params": {}},
                {"action": "begin_remediation", "params": {}},
            ],
        )

        self.register_playbook(
            name="biometric_spoofing_response",
            description="Respond to biometric spoofing attempt",
            severity="critical",
            steps=[
                {"action": "block_user_session", "params": {"user_id": "{user_id}"}},
                {"action": "flag_for_review", "params": {"reason": "biometric_spoofing"}},
                {"action": "notify_security_team", "params": {"channel": "biometric-alerts"}},
                {"action": "increase_liveness_threshold", "params": {"threshold": 0.95}},
                {"action": "require_additional_verification", "params": {}},
            ],
        )

        self.register_playbook(
            name="session_hijack_response",
            description="Respond to session hijacking",
            severity="high",
            steps=[
                {"action": "revoke_session", "params": {"session_id": "{session_id}"}},
                {"action": "revoke_all_user_sessions", "params": {"user_id": "{user_id}"}},
                {"action": "notify_user", "params": {"method": "email"}},
                {"action": "enable_enhanced_monitoring", "params": {"user_id": "{user_id}"}},
            ],
        )

        self.register_playbook(
            name="privilege_escalation_response",
            description="Respond to privilege escalation",
            severity="critical",
            steps=[
                {"action": "revoke_elevated_permissions", "params": {"user_id": "{user_id}"}},
                {"action": "block_user", "params": {"user_id": "{user_id}"}},
                {"action": "notify_admin_team", "params": {"channel": "admin-alerts"}},
                {"action": "audit_recent_permissions_changes", "params": {}},
                {"action": "require_reauthentication", "params": {}},
            ],
        )

        self.register_playbook(
            name="ddos_response",
            description="Respond to DDoS attack",
            severity="high",
            steps=[
                {"action": "enable_rate_limiting", "params": {"rate": "100/min"}},
                {"action": "activate_cdn_protection", "params": {}},
                {"action": "notify_infrastructure_team", "params": {"channel": "infra-alerts"}},
                {"action": "scale_resources", "params": {"multiplier": 2}},
                {"action": "block_suspicious_ips", "params": {}},
            ],
        )

    def register_playbook(
        self,
        name: str,
        description: str,
        severity: str,
        steps: list[dict[str, Any]],
    ) -> None:
        self.playbooks[name] = {
            "name": name,
            "description": description,
            "severity": severity,
            "steps": steps,
            "created_at": time.time(),
        }

    def create_incident(
        self,
        title: str,
        description: str,
        severity: str,
        source: str,
        playbook_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        incident_id = str(uuid.uuid4())

        self.incidents[incident_id] = {
            "id": incident_id,
            "title": title,
            "description": description,
            "severity": severity,
            "source": source,
            "status": "open",
            "playbook_name": playbook_name,
            "metadata": metadata or {},
            "created_at": time.time(),
            "updated_at": time.time(),
            "acknowledged_at": None,
            "resolved_at": None,
            "response_actions": [],
            "timeline": [{"event": "created", "timestamp": time.time()}],
        }

        INCIDENT_COUNTER.labels(severity=severity, status="open").inc()
        INCIDENT_ACTIVE.inc()

        return incident_id

    def respond_to_incident(
        self,
        incident_id: str,
        playbook_name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if incident_id not in self.incidents:
            raise ValueError(f"Incident {incident_id} not found")

        incident = self.incidents[incident_id]
        playbook = playbook_name or incident.get("playbook_name")

        if not playbook or playbook not in self.playbooks:
            return {"error": "No playbook specified or found"}

        start_time = time.time()
        playbook_def = self.playbooks[playbook]
        results = []

        for step in playbook_def["steps"]:
            action_result = self._execute_action(
                step["action"],
                step.get("params", {}),
                context or {},
            )
            results.append({
                "action": step["action"],
                "result": action_result,
                "timestamp": time.time(),
            })
            incident["response_actions"].append({
                "action": step["action"],
                "result": action_result,
                "timestamp": time.time(),
            })

        duration = time.time() - start_time
        INCIDENT_PLAYBOOK_EXECUTIONS.labels(
            playbook_name=playbook,
            status="success",
        ).inc()

        incident["timeline"].append({
            "event": "playbook_executed",
            "playbook": playbook,
            "duration": duration,
            "timestamp": time.time(),
        })

        response_time = time.time() - incident["created_at"]
        INCIDENT_RESPONSE_TIME.labels(severity=incident["severity"]).observe(response_time)

        return {
            "incident_id": incident_id,
            "playbook": playbook,
            "results": results,
            "duration": duration,
            "status": "responded",
        }

    def _execute_action(
        self,
        action: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        action_handlers = {
            "block_ip": lambda p, c: {"status": "success", "message": f"Blocked IP for {p.get('duration', 3600)}s"},
            "notify_security_team": lambda p, c: {"status": "success", "message": f"Notification sent to {p.get('channel', 'security-alerts')}"},
            "enable_enhanced_monitoring": lambda p, c: {"status": "success", "message": "Enhanced monitoring enabled"},
            "force_password_reset": lambda p, c: {"status": "success", "message": f"Password reset forced for {p.get('user_id', 'unknown')}"},
            "isolate_affected_systems": lambda p, c: {"status": "success", "message": "Systems isolated"},
            "preserve_evidence": lambda p, c: {"status": "success", "message": "Evidence preserved"},
            "notify_incident_commander": lambda p, c: {"status": "success", "message": "Incident commander notified"},
            "assess_scope": lambda p, c: {"status": "success", "message": "Scope assessed"},
            "notify_authorities": lambda p, c: {"status": "success", "message": f"Authorities notified (timeline: {p.get('timeline', '72h')})"},
            "notify_affected_users": lambda p, c: {"status": "success", "message": "Affected users notified"},
            "begin_remediation": lambda p, c: {"status": "success", "message": "Remediation begun"},
            "block_user_session": lambda p, c: {"status": "success", "message": f"Session blocked for {p.get('user_id', 'unknown')}"},
            "flag_for_review": lambda p, c: {"status": "success", "message": f"Flagged for review: {p.get('reason', 'unknown')}"},
            "increase_liveness_threshold": lambda p, c: {"status": "success", "message": f"Liveness threshold increased to {p.get('threshold', 0.95)}"},
            "require_additional_verification": lambda p, c: {"status": "success", "message": "Additional verification required"},
            "revoke_session": lambda p, c: {"status": "success", "message": f"Session {p.get('session_id', 'unknown')} revoked"},
            "revoke_all_user_sessions": lambda p, c: {"status": "success", "message": f"All sessions revoked for {p.get('user_id', 'unknown')}"},
            "notify_user": lambda p, c: {"status": "success", "message": f"User notified via {p.get('method', 'email')}"},
            "revoke_elevated_permissions": lambda p, c: {"status": "success", "message": f"Elevated permissions revoked for {p.get('user_id', 'unknown')}"},
            "block_user": lambda p, c: {"status": "success", "message": f"User {p.get('user_id', 'unknown')} blocked"},
            "notify_admin_team": lambda p, c: {"status": "success", "message": f"Admin team notified via {p.get('channel', 'admin-alerts')}"},
            "audit_recent_permissions_changes": lambda p, c: {"status": "success", "message": "Permissions changes audited"},
            "require_reauthentication": lambda p, c: {"status": "success", "message": "Reauthentication required"},
            "enable_rate_limiting": lambda p, c: {"status": "success", "message": f"Rate limiting enabled at {p.get('rate', '100/min')}"},
            "activate_cdn_protection": lambda p, c: {"status": "success", "message": "CDN protection activated"},
            "notify_infrastructure_team": lambda p, c: {"status": "success", "message": f"Infrastructure team notified via {p.get('channel', 'infra-alerts')}"},
            "scale_resources": lambda p, c: {"status": "success", "message": f"Resources scaled by {p.get('multiplier', 2)}x"},
            "block_suspicious_ips": lambda p, c: {"status": "success", "message": "Suspicious IPs blocked"},
        }

        handler = action_handlers.get(action)
        if handler:
            return handler(params, context)
        return {"status": "unknown", "message": f"Unknown action: {action}"}

    def acknowledge_incident(self, incident_id: str, acknowledger: str) -> None:
        if incident_id not in self.incidents:
            raise ValueError(f"Incident {incident_id} not found")

        self.incidents[incident_id]["status"] = "acknowledged"
        self.incidents[incident_id]["acknowledged_at"] = time.time()
        self.incidents[incident_id]["acknowledger"] = acknowledger
        self.incidents[incident_id]["timeline"].append({
            "event": "acknowledged",
            "acknowledger": acknowledger,
            "timestamp": time.time(),
        })

    def resolve_incident(
        self,
        incident_id: str,
        resolver: str,
        resolution_notes: str = "",
    ) -> None:
        if incident_id not in self.incidents:
            raise ValueError(f"Incident {incident_id} not found")

        incident = self.incidents[incident_id]
        incident["status"] = "resolved"
        incident["resolved_at"] = time.time()
        incident["resolver"] = resolver
        incident["resolution_notes"] = resolution_notes
        incident["timeline"].append({
            "event": "resolved",
            "resolver": resolver,
            "notes": resolution_notes,
            "timestamp": time.time(),
        })

        INCIDENT_ACTIVE.dec()

        resolution_time = time.time() - incident["created_at"]
        INCIDENT_RESOLUTION_TIME.labels(severity=incident["severity"]).observe(resolution_time)

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        return self.incidents.get(incident_id)

    def list_incidents(
        self,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        incidents = list(self.incidents.values())

        if status:
            incidents = [i for i in incidents if i["status"] == status]

        if severity:
            incidents = [i for i in incidents if i["severity"] == severity]

        incidents.sort(key=lambda x: x["created_at"], reverse=True)

        return incidents[:limit]

    def get_incident_statistics(self) -> dict[str, Any]:
        total = len(self.incidents)
        open_incidents = sum(1 for i in self.incidents.values() if i["status"] == "open")
        acknowledged = sum(1 for i in self.incidents.values() if i["status"] == "acknowledged")
        resolved = sum(1 for i in self.incidents.values() if i["status"] == "resolved")

        severity_counts = {}
        for incident in self.incidents.values():
            severity = incident["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total": total,
            "open": open_incidents,
            "acknowledged": acknowledged,
            "resolved": resolved,
            "by_severity": severity_counts,
        }

    def get_timeline(self, incident_id: str) -> list[dict[str, Any]]:
        incident = self.get_incident(incident_id)
        if not incident:
            return []
        return incident["timeline"]
