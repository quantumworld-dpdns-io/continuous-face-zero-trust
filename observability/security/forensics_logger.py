from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


FORENSICS_LOG_ENTRIES = Counter(
    "forensics_log_entries_total",
    "Total forensic log entries",
    labelnames=["event_type", "severity"],
)

FORENSICS_LOG_SIZE = Gauge(
    "forensics_log_size_bytes",
    "Size of forensic log storage",
)

FORENSICS_INTEGRITY_CHECKS = Counter(
    "forensics_integrity_checks_total",
    "Total forensic log integrity checks",
    labelnames=["status"],
)

FORENSICS_LOG_LATENCY = Histogram(
    "forensics_log_latency_seconds",
    "Latency of forensic log operations",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)


class ForensicsLogger:
    def __init__(
        self,
        immutable: bool = True,
        encryption_enabled: bool = True,
        retention_days: int = 2555,
    ):
        self.immutable = immutable
        self.encryption_enabled = encryption_enabled
        self.retention_days = retention_days
        self.log_entries: list[dict[str, Any]] = []
        self.chain_hash: str = ""
        self.previous_hash: str = ""

    def _calculate_hash(self, data: dict[str, Any]) -> str:
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _calculate_chain_hash(self, entry: dict[str, Any], previous_hash: str) -> str:
        chain_data = {
            "entry": entry,
            "previous_hash": previous_hash,
        }
        return self._calculate_hash(chain_data)

    def log_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        details: dict[str, Any] | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        start_time = time.time()

        entry = {
            "event_id": hashlib.sha256(
                f"{time.time()}{event_type}{source}".encode()
            ).hexdigest(),
            "event_type": event_type,
            "severity": severity,
            "source": source,
            "details": details or {},
            "user_id": user_id,
            "ip_address": ip_address,
            "session_id": session_id,
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "immutable": self.immutable,
        }

        chain_hash = self._calculate_chain_hash(entry, self.previous_hash)
        entry["chain_hash"] = chain_hash
        entry["previous_hash"] = self.previous_hash

        self.log_entries.append(entry)
        self.previous_hash = chain_hash
        self.chain_hash = chain_hash

        entry_hash = self._calculate_hash(entry)
        entry["entry_hash"] = entry_hash

        FORENSICS_LOG_ENTRIES.labels(
            event_type=event_type,
            severity=severity,
        ).inc()

        total_size = sum(len(json.dumps(e, default=str).encode()) for e in self.log_entries)
        FORENSICS_LOG_SIZE.set(total_size)

        duration = time.time() - start_time
        FORENSICS_LOG_LATENCY.observe(duration)

        return entry

    def log_auth_event(
        self,
        user_id: str,
        action: str,
        status: str,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.log_event(
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

    def log_biometric_event(
        self,
        user_id: str,
        action: str,
        status: str,
        confidence: float,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.log_event(
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

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        return self.log_event(
            event_type=event_type,
            severity=severity,
            source=source,
            details=details,
            ip_address=ip_address,
        )

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.log_event(
            event_type="data_access",
            severity="info" if status == "success" else "warning",
            source="data-service",
            details={
                "resource": resource,
                "action": action,
                "status": status,
                **(details or {}),
            },
            user_id=user_id,
        )

    def verify_integrity(self) -> dict[str, Any]:
        start_time = time.time()
        is_valid = True
        broken_at = None

        for i in range(1, len(self.log_entries)):
            entry = self.log_entries[i]
            previous_entry = self.log_entries[i - 1]

            expected_previous_hash = self._calculate_chain_hash(previous_entry, entry.get("previous_hash", ""))
            if entry.get("previous_hash") != previous_entry.get("chain_hash"):
                is_valid = False
                broken_at = i
                break

        status = "valid" if is_valid else "invalid"
        FORENSICS_INTEGRITY_CHECKS.labels(status=status).inc()

        duration = time.time() - start_time

        return {
            "is_valid": is_valid,
            "broken_at": broken_at,
            "total_entries": len(self.log_entries),
            "chain_hash": self.chain_hash,
            "verification_time": duration,
        }

    def get_entries(
        self,
        event_type: str | None = None,
        severity: str | None = None,
        user_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        entries = self.log_entries

        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]

        if severity:
            entries = [e for e in entries if e["severity"] == severity]

        if user_id:
            entries = [e for e in entries if e.get("user_id") == user_id]

        if start_time:
            entries = [e for e in entries if e["timestamp"] >= start_time]

        if end_time:
            entries = [e for e in entries if e["timestamp"] <= end_time]

        return entries[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        total = len(self.log_entries)
        if total == 0:
            return {"total": 0, "by_type": {}, "by_severity": {}}

        by_type = {}
        by_severity = {}
        for entry in self.log_entries:
            event_type = entry["event_type"]
            severity = entry["severity"]
            by_type[event_type] = by_type.get(event_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total": total,
            "by_type": by_type,
            "by_severity": by_severity,
            "chain_hash": self.chain_hash,
            "first_entry_time": self.log_entries[0]["timestamp"] if self.log_entries else None,
            "last_entry_time": self.log_entries[-1]["timestamp"] if self.log_entries else None,
        }

    def export_entries(
        self,
        format: str = "json",
        **kwargs,
    ) -> str:
        entries = self.get_entries(**kwargs)

        if format == "json":
            return json.dumps(entries, indent=2, default=str)
        elif format == "csv":
            if not entries:
                return ""
            headers = entries[0].keys()
            lines = [",".join(str(h) for h in headers)]
            for entry in entries:
                lines.append(",".join(str(entry.get(h, "")) for h in headers))
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def search_entries(
        self,
        query: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        results = []
        query_lower = query.lower()

        for entry in self.log_entries:
            entry_str = json.dumps(entry, default=str).lower()
            if query_lower in entry_str:
                results.append(entry)

        return results[-limit:]
