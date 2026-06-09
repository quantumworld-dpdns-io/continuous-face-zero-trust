from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


BIOMETRIC_AUDIT_EVENTS = Counter(
    "biometric_audit_events_total",
    "Total biometric audit events",
    labelnames=["event_type", "status"],
)

BIOMETRIC_DATA_ACCESS = Counter(
    "biometric_data_access_total",
    "Total biometric data access events",
    labelnames=["access_type", "purpose"],
)

BIOMETRIC_PRIVACY_VIOLATIONS = Counter(
    "biometric_privacy_violations_total",
    "Total biometric privacy violations",
    labelnames=["violation_type", "severity"],
)

BIOMETRIC_AUDIT_LATENCY = Histogram(
    "biometric_audit_latency_seconds",
    "Latency of biometric audit operations",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)

BIOMETRIC_DATA_RETENTION = Gauge(
    "biometric_data_retention_days",
    "Biometric data retention period",
    labelnames=["data_type"],
)


class BiometricAudit:
    def __init__(
        self,
        retention_days: int = 365,
        max_raw_image_retention_hours: int = 0,
        differential_privacy_epsilon: float = 0.1,
    ):
        self.retention_days = retention_days
        self.max_raw_image_retention_hours = max_raw_image_retention_hours
        self.differential_privacy_epsilon = differential_privacy_epsilon
        self.audit_log: list[dict[str, Any]] = []
        self.data_access_log: list[dict[str, Any]] = []

    def log_biometric_operation(
        self,
        operation_type: str,
        user_id: str,
        status: str,
        confidence: float | None = None,
        liveness_score: float | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "event_id": f"bio_{int(time.time() * 1000)}",
            "operation_type": operation_type,
            "user_id": user_id,
            "status": status,
            "confidence": confidence,
            "liveness_score": liveness_score,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "raw_image_stored": False,
            "dp_applied": False,
        }

        self.audit_log.append(entry)

        BIOMETRIC_AUDIT_EVENTS.labels(
            event_type=operation_type,
            status=status,
        ).inc()

        return entry

    def log_data_access(
        self,
        access_type: str,
        user_id: str,
        purpose: str,
        data_types: list[str],
        accessor_id: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "access_id": f"access_{int(time.time() * 1000)}",
            "access_type": access_type,
            "user_id": user_id,
            "purpose": purpose,
            "data_types": data_types,
            "accessor_id": accessor_id,
            "ip_address": ip_address,
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "dp_applied": any(dt in ["face_embedding", "biometric_template"] for dt in data_types),
        }

        self.data_access_log.append(entry)

        BIOMETRIC_DATA_ACCESS.labels(
            access_type=access_type,
            purpose=purpose,
        ).inc()

        return entry

    def check_privacy_compliance(
        self,
        operation_type: str,
        data_types: list[str],
        purpose: str,
        consent_obtained: bool,
        retention_period_days: int,
    ) -> dict[str, Any]:
        violations = []

        if not consent_obtained:
            violations.append({
                "type": "missing_consent",
                "severity": "critical",
                "description": "Biometric data processing requires explicit consent",
            })

        if retention_period_days > self.retention_days:
            violations.append({
                "type": "excessive_retention",
                "severity": "high",
                "description": f"Retention period {retention_period_days} exceeds maximum {self.retention_days} days",
            })

        if "raw_image" in data_types and self.max_raw_image_retention_hours > 0:
            violations.append({
                "type": "raw_image_storage",
                "severity": "high",
                "description": "Raw biometric images should not be stored",
            })

        purpose_allowed = [
            "authentication",
            "verification",
            "liveness_detection",
            "anti_spoofing",
            "quality_assessment",
        ]
        if purpose not in purpose_allowed:
            violations.append({
                "type": "invalid_purpose",
                "severity": "medium",
                "description": f"Purpose '{purpose}' is not in the list of allowed purposes",
            })

        for violation in violations:
            BIOMETRIC_PRIVACY_VIOLATIONS.labels(
                violation_type=violation["type"],
                severity=violation["severity"],
            ).inc()

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "operation_type": operation_type,
            "data_types": data_types,
            "purpose": purpose,
            "checked_at": time.time(),
        }

    def apply_differential_privacy(
        self,
        data: dict[str, Any],
        sensitivity: float = 1.0,
    ) -> dict[str, Any]:
        import numpy as np

        noisy_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                noise = np.random.laplace(0, sensitivity / self.differential_privacy_epsilon)
                noisy_data[key] = value + noise
            elif isinstance(value, list):
                noisy_data[key] = [
                    v + np.random.laplace(0, sensitivity / self.differential_privacy_epsilon)
                    if isinstance(v, (int, float)) else v
                    for v in value
                ]
            else:
                noisy_data[key] = value

        noisy_data["_dp_applied"] = True
        noisy_data["_dp_epsilon"] = self.differential_privacy_epsilon
        noisy_data["_dp_sensitivity"] = sensitivity

        return noisy_data

    def anonymize_biometric_data(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        anonymized = data.copy()

        if "user_id" in anonymized:
            import hashlib
            anonymized["user_id_hash"] = hashlib.sha256(
                anonymized["user_id"].encode()
            ).hexdigest()[:16]
            del anonymized["user_id"]

        if "ip_address" in anonymized:
            parts = anonymized["ip_address"].split(".")
            if len(parts) == 4:
                anonymized["ip_address"] = f"{parts[0]}.{parts[1]}.*.*"
            del anonymized["ip_address"]

        if "face_embedding" in anonymized:
            anonymized["face_embedding"] = self.apply_differential_privacy(
                {"embedding": anonymized["face_embedding"]}
            )["embedding"]

        return anonymized

    def get_audit_log(
        self,
        user_id: str | None = None,
        operation_type: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        log = self.audit_log

        if user_id:
            log = [e for e in log if e["user_id"] == user_id]

        if operation_type:
            log = [e for e in log if e["operation_type"] == operation_type]

        if start_time:
            log = [e for e in log if e["timestamp"] >= start_time]

        if end_time:
            log = [e for e in log if e["timestamp"] <= end_time]

        return log[-limit:]

    def get_data_access_log(
        self,
        user_id: str | None = None,
        access_type: str | None = None,
        purpose: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        log = self.data_access_log

        if user_id:
            log = [e for e in log if e["user_id"] == user_id]

        if access_type:
            log = [e for e in log if e["access_type"] == access_type]

        if purpose:
            log = [e for e in log if e["purpose"] == purpose]

        return log[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        total_operations = len(self.audit_log)
        successful = sum(1 for e in self.audit_log if e["status"] == "success")
        failed = sum(1 for e in self.audit_log if e["status"] == "failed")

        operation_counts = {}
        for entry in self.audit_log:
            op_type = entry["operation_type"]
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1

        return {
            "total_operations": total_operations,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_operations if total_operations > 0 else 0.0,
            "operation_counts": operation_counts,
            "data_access_events": len(self.data_access_log),
            "retention_days": self.retention_days,
            "differential_privacy_epsilon": self.differential_privacy_epsilon,
        }

    def export_audit_log(
        self,
        format: str = "json",
        **kwargs,
    ) -> str:
        import json
        log = self.get_audit_log(**kwargs)

        if format == "json":
            return json.dumps(log, indent=2, default=str)
        elif format == "csv":
            if not log:
                return ""
            headers = log[0].keys()
            lines = [",".join(str(h) for h in headers)]
            for entry in log:
                lines.append(",".join(str(entry.get(h, "")) for h in headers))
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
