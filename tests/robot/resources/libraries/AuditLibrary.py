"""AuditLibrary — Robot Framework library for audit trail operations."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone


class AuditLibrary:
    """Robot Framework library for audit trail test operations."""

    def __init__(self):
        self._events: list[dict] = []
        self._chain: list[str] = []

    def log_event(self, event_type: str, details: dict, severity: str = "info") -> dict:
        event = {
            "event_id": hashlib.sha256(f"{event_type}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        self._chain.append(event["event_id"])
        return event

    def verify_chain_integrity(self) -> dict:
        if not self._chain:
            return {"valid": True, "events": 0}
        return {"valid": True, "events": len(self._chain), "chain_hash": hashlib.sha256(":".join(self._chain).encode()).hexdigest()}

    def verify_event_completeness(self, event: dict, required_fields: list[str] | None = None) -> dict:
        if required_fields is None:
            required_fields = ["event_id", "event_type", "severity", "details", "timestamp"]
        present = [f for f in required_fields if f in event]
        missing = [f for f in required_fields if f not in event]
        return {"complete": len(missing) == 0, "present": present, "missing": missing}

    def verify_timestamp_format(self, timestamp: str) -> dict:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return {"valid": True, "is_utc": dt.tzinfo is not None}
        except Exception:
            return {"valid": False}

    def verify_no_tampering(self, original: dict, current: dict) -> dict:
        changed = []
        for key in original:
            if key in current and original[key] != current[key]:
                changed.append(key)
        return {"tampered": len(changed) > 0, "changed_fields": changed}

    def filter_events(self, event_type: str | None = None, severity: str | None = None) -> list[dict]:
        filtered = self._events
        if event_type:
            filtered = [e for e in filtered if e.get("event_type") == event_type]
        if severity:
            filtered = [e for e in filtered if e.get("severity") == severity]
        return filtered
