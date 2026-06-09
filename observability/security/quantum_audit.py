from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


QUANTUM_AUDIT_EVENTS = Counter(
    "quantum_audit_events_total",
    "Total quantum operation audit events",
    labelnames=["operation_type", "status"],
)

QUANTUM_AUDIT_DATA_ACCESS = Counter(
    "quantum_audit_data_access_total",
    "Total quantum data access events",
    labelnames=["data_type", "access_type"],
)

QUANTUM_AUDIT_VIOLATIONS = Counter(
    "quantum_audit_violations_total",
    "Total quantum audit violations",
    labelnames=["violation_type", "severity"],
)

QUANTUM_AUDIT_LATENCY = Histogram(
    "quantum_audit_latency_seconds",
    "Latency of quantum audit operations",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)

QUANTUM_AUDIT_LOG_SIZE = Gauge(
    "quantum_audit_log_size",
    "Size of quantum audit log",
)


class QuantumAudit:
    def __init__(
        self,
        retention_days: int = 2555,
        enable_circuit_logging: bool = True,
        enable_result_logging: bool = True,
    ):
        self.retention_days = retention_days
        self.enable_circuit_logging = enable_circuit_logging
        self.enable_result_logging = enable_result_logging
        self.audit_log: list[dict[str, Any]] = []
        self.circuit_log: list[dict[str, Any]] = []
        self.result_log: list[dict[str, Any]] = []

    def log_quantum_operation(
        self,
        operation_type: str,
        user_id: str,
        backend: str,
        status: str,
        circuit_name: str | None = None,
        qubit_count: int | None = None,
        shot_count: int | None = None,
        fidelity: float | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "event_id": f"q_{int(time.time() * 1000)}",
            "operation_type": operation_type,
            "user_id": user_id,
            "backend": backend,
            "status": status,
            "circuit_name": circuit_name,
            "qubit_count": qubit_count,
            "shot_count": shot_count,
            "fidelity": fidelity,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        }

        self.audit_log.append(entry)
        QUANTUM_AUDIT_LOG_SIZE.set(len(self.audit_log))

        QUANTUM_AUDIT_EVENTS.labels(
            operation_type=operation_type,
            status=status,
        ).inc()

        return entry

    def log_circuit(
        self,
        circuit_name: str,
        user_id: str,
        backend: str,
        circuit_depth: int,
        gate_count: dict[str, int],
        qubit_count: int,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enable_circuit_logging:
            return {}

        entry = {
            "log_id": f"circ_{int(time.time() * 1000)}",
            "circuit_name": circuit_name,
            "user_id": user_id,
            "backend": backend,
            "circuit_depth": circuit_depth,
            "gate_count": gate_count,
            "total_gates": sum(gate_count.values()),
            "qubit_count": qubit_count,
            "parameters": parameters or {},
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        }

        self.circuit_log.append(entry)
        return entry

    def log_result(
        self,
        circuit_name: str,
        user_id: str,
        backend: str,
        result: Any,
        fidelity: float,
        execution_time: float,
        shot_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enable_result_logging:
            return {}

        result_summary = {}
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (int, float, str, bool)):
                    result_summary[key] = value
                elif isinstance(value, list) and len(value) <= 100:
                    result_summary[key] = value
        elif isinstance(result, list) and len(result) <= 100:
            result_summary = {"counts": result}

        entry = {
            "log_id": f"res_{int(time.time() * 1000)}",
            "circuit_name": circuit_name,
            "user_id": user_id,
            "backend": backend,
            "result_summary": result_summary,
            "fidelity": fidelity,
            "execution_time": execution_time,
            "shot_count": shot_count,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        }

        self.result_log.append(entry)
        return entry

    def log_data_access(
        self,
        data_type: str,
        access_type: str,
        user_id: str,
        purpose: str,
        circuit_name: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "access_id": f"qaccess_{int(time.time() * 1000)}",
            "data_type": data_type,
            "access_type": access_type,
            "user_id": user_id,
            "purpose": purpose,
            "circuit_name": circuit_name,
            "ip_address": ip_address,
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        }

        QUANTUM_AUDIT_DATA_ACCESS.labels(
            data_type=data_type,
            access_type=access_type,
        ).inc()

        return entry

    def check_compliance(
        self,
        operation_type: str,
        backend: str,
        qubit_count: int,
        data_types: list[str],
        purpose: str,
    ) -> dict[str, Any]:
        violations = []

        if qubit_count > 128:
            violations.append({
                "type": "excessive_qubit_count",
                "severity": "medium",
                "description": f"Qubit count {qubit_count} exceeds recommended maximum",
            })

        restricted_backends = ["ibm_quantum", "google_quantum"]
        if backend in restricted_backends and purpose not in ["research", "development"]:
            violations.append({
                "type": "restricted_backend_usage",
                "severity": "high",
                "description": f"Backend {backend} requires specific authorization",
            })

        if "quantum_advantage_data" in data_types:
            violations.append({
                "type": "sensitive_data_access",
                "severity": "critical",
                "description": "Access to quantum advantage data requires special authorization",
            })

        for violation in violations:
            QUANTUM_AUDIT_VIOLATIONS.labels(
                violation_type=violation["type"],
                severity=violation["severity"],
            ).inc()

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "operation_type": operation_type,
            "backend": backend,
            "qubit_count": qubit_count,
            "checked_at": time.time(),
        }

    def get_audit_log(
        self,
        user_id: str | None = None,
        operation_type: str | None = None,
        backend: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        log = self.audit_log

        if user_id:
            log = [e for e in log if e["user_id"] == user_id]

        if operation_type:
            log = [e for e in log if e["operation_type"] == operation_type]

        if backend:
            log = [e for e in log if e["backend"] == backend]

        if start_time:
            log = [e for e in log if e["timestamp"] >= start_time]

        if end_time:
            log = [e for e in log if e["timestamp"] <= end_time]

        return log[-limit:]

    def get_circuit_log(
        self,
        user_id: str | None = None,
        circuit_name: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        log = self.circuit_log

        if user_id:
            log = [e for e in log if e["user_id"] == user_id]

        if circuit_name:
            log = [e for e in log if e["circuit_name"] == circuit_name]

        return log[-limit:]

    def get_result_log(
        self,
        user_id: str | None = None,
        circuit_name: str | None = None,
        min_fidelity: float | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        log = self.result_log

        if user_id:
            log = [e for e in log if e["user_id"] == user_id]

        if circuit_name:
            log = [e for e in log if e["circuit_name"] == circuit_name]

        if min_fidelity is not None:
            log = [e for e in log if e["fidelity"] >= min_fidelity]

        return log[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        total_operations = len(self.audit_log)
        successful = sum(1 for e in self.audit_log if e["status"] == "success")
        failed = sum(1 for e in self.audit_log if e["status"] == "failed")

        operation_counts = {}
        backend_counts = {}
        for entry in self.audit_log:
            op_type = entry["operation_type"]
            backend = entry["backend"]
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            backend_counts[backend] = backend_counts.get(backend, 0) + 1

        avg_fidelity = 0.0
        if self.result_log:
            avg_fidelity = sum(r["fidelity"] for r in self.result_log) / len(self.result_log)

        return {
            "total_operations": total_operations,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_operations if total_operations > 0 else 0.0,
            "operation_counts": operation_counts,
            "backend_counts": backend_counts,
            "total_circuits": len(self.circuit_log),
            "total_results": len(self.result_log),
            "average_fidelity": avg_fidelity,
            "retention_days": self.retention_days,
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
