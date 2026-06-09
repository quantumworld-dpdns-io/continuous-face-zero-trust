from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


ZERO_TRUST_VERIFICATION = Counter(
    "zero_trust_verification_total",
    "Total zero trust verifications",
    labelnames=["status", "verification_type"],
)

ZERO_TRUST_SCORE = Gauge(
    "zero_trust_score",
    "Zero trust compliance score",
    labelnames=["component"],
)

ZERO_TRUST_POLICY_VIOLATIONS = Counter(
    "zero_trust_policy_violations_total",
    "Total zero trust policy violations",
    labelnames=["policy", "severity"],
)

ZERO_TRUST_ACTIVE_SESSIONS = Gauge(
    "zero_trust_active_sessions",
    "Number of active zero trust sessions",
)

ZERO_TRUST_VERIFICATION_LATENCY = Histogram(
    "zero_trust_verification_latency_seconds",
    "Latency of zero trust verifications",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    labelnames=["verification_type"],
)


class ZeroTrustMonitor:
    def __init__(self):
        self.policies: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, dict[str, Any]] = {}
        self.verification_history: list[dict[str, Any]] = []
        self._register_default_policies()

    def _register_default_policies(self) -> None:
        self.register_policy(
            name="verify_always",
            description="Always verify identity and device health",
            severity="critical",
            conditions=[
                "device_health_check",
                "identity_verification",
                "location_validation",
            ],
        )

        self.register_policy(
            name="least_privilege",
            description="Grant least privilege access",
            severity="high",
            conditions=[
                "role_based_access",
                "resource_classification",
                "time_based_access",
            ],
        )

        self.register_policy(
            name="micro_segmentation",
            description="Enforce micro-segmentation",
            severity="high",
            conditions=[
                "network_segmentation",
                "service_mesh_policy",
                "firewall_rules",
            ],
        )

        self.register_policy(
            name="continuous_monitoring",
            description="Continuous monitoring and validation",
            severity="medium",
            conditions=[
                "real_time_monitoring",
                "anomaly_detection",
                "behavioral_analysis",
            ],
        )

        self.register_policy(
            name="encryption_everywhere",
            description="Encrypt all data in transit and at rest",
            severity="critical",
            conditions=[
                "tls_enforcement",
                "data_encryption",
                "key_management",
            ],
        )

        self.register_policy(
            name="biometric_verification",
            description="Require biometric verification for sensitive operations",
            severity="high",
            conditions=[
                "face_recognition",
                "liveness_detection",
                "anti_spoofing",
            ],
        )

        self.register_policy(
            name="session_management",
            description="Enforce strict session management",
            severity="high",
            conditions=[
                "session_timeout",
                "session_binding",
                "session_invalidation",
            ],
        )

    def register_policy(
        self,
        name: str,
        description: str,
        severity: str,
        conditions: list[str],
    ) -> None:
        self.policies[name] = {
            "name": name,
            "description": description,
            "severity": severity,
            "conditions": conditions,
            "enabled": True,
            "created_at": time.time(),
        }

    def verify_request(
        self,
        user_id: str,
        device_id: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_time = time.time()

        verification_results = []
        overall_status = "allowed"
        risk_score = 0.0

        for policy_name, policy in self.policies.items():
            if not policy["enabled"]:
                continue

            policy_result = self._evaluate_policy(
                policy_name,
                policy,
                user_id,
                device_id,
                resource,
                action,
                context or {},
            )
            verification_results.append(policy_result)

            if not policy_result["passed"]:
                if policy["severity"] == "critical":
                    overall_status = "denied"
                    risk_score += 0.5
                elif policy["severity"] == "high":
                    overall_status = "challenged"
                    risk_score += 0.3
                else:
                    risk_score += 0.1

        risk_score = min(1.0, risk_score)

        verification = {
            "user_id": user_id,
            "device_id": device_id,
            "resource": resource,
            "action": action,
            "status": overall_status,
            "risk_score": risk_score,
            "verification_results": verification_results,
            "verified_at": time.time(),
            "context": context or {},
        }

        self.verification_history.append(verification)
        if len(self.verification_history) > 10000:
            self.verification_history = self.verification_history[-10000:]

        status_label = overall_status
        ZERO_TRUST_VERIFICATION.labels(
            status=status_label,
            verification_type="request",
        ).inc()

        ZERO_TRUST_VERIFICATION_LATENCY.labels(
            verification_type="request",
        ).observe(time.time() - start_time)

        if overall_status == "denied":
            for result in verification_results:
                if not result["passed"]:
                    ZERO_TRUST_POLICY_VIOLATIONS.labels(
                        policy=result["policy_name"],
                        severity=self.policies[result["policy_name"]]["severity"],
                    ).inc()

        return verification

    def _evaluate_policy(
        self,
        policy_name: str,
        policy: dict[str, Any],
        user_id: str,
        device_id: str,
        resource: str,
        action: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        passed = True
        details = {}

        if policy_name == "verify_always":
            if not context.get("identity_verified", False):
                passed = False
                details["reason"] = "Identity not verified"
            if not context.get("device_healthy", True):
                passed = False
                details["reason"] = "Device health check failed"

        elif policy_name == "least_privilege":
            required_role = context.get("required_role", "viewer")
            user_role = context.get("user_role", "viewer")
            role_hierarchy = {"admin": 4, "editor": 3, "viewer": 2, "guest": 1}
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                passed = False
                details["reason"] = "Insufficient privileges"

        elif policy_name == "encryption_everywhere":
            if not context.get("tls_enabled", True):
                passed = False
                details["reason"] = "TLS not enabled"

        elif policy_name == "biometric_verification":
            if context.get("requires_biometric", False):
                if not context.get("biometric_verified", False):
                    passed = False
                    details["reason"] = "Biometric verification required but not provided"
                if context.get("liveness_score", 1.0) < 0.8:
                    passed = False
                    details["reason"] = "Liveness score below threshold"

        elif policy_name == "session_management":
            session_age = context.get("session_age_seconds", 0)
            max_session_age = context.get("max_session_age_seconds", 3600)
            if session_age > max_session_age:
                passed = False
                details["reason"] = "Session expired"

        if not passed:
            details["policy_name"] = policy_name
            details["severity"] = policy["severity"]

        return {
            "policy_name": policy_name,
            "passed": passed,
            "details": details,
            "evaluated_at": time.time(),
        }

    def create_session(
        self,
        user_id: str,
        device_id: str,
        ip_address: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        import uuid
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "device_id": device_id,
            "ip_address": ip_address,
            "context": context or {},
            "created_at": time.time(),
            "last_activity": time.time(),
            "status": "active",
            "risk_score": 0.0,
        }

        ZERO_TRUST_ACTIVE_SESSIONS.inc()
        return session_id

    def validate_session(
        self,
        session_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if session_id not in self.sessions:
            return {"valid": False, "reason": "Session not found"}

        session = self.sessions[session_id]

        if session["status"] != "active":
            return {"valid": False, "reason": "Session inactive"}

        session_age = time.time() - session["created_at"]
        if session_age > 3600:
            session["status"] = "expired"
            return {"valid": False, "reason": "Session expired"}

        if context:
            if context.get("ip_address") != session["ip_address"]:
                session["status"] = "compromised"
                return {"valid": False, "reason": "IP address changed"}

            if context.get("device_id") != session["device_id"]:
                session["status"] = "compromised"
                return {"valid": False, "reason": "Device changed"}

        session["last_activity"] = time.time()
        return {"valid": True, "session": session}

    def invalidate_session(self, session_id: str) -> bool:
        if session_id not in self.sessions:
            return False

        self.sessions[session_id]["status"] = "invalidated"
        ZERO_TRUST_ACTIVE_SESSIONS.dec()
        return True

    def get_verification_history(
        self,
        user_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        history = self.verification_history

        if user_id:
            history = [h for h in history if h["user_id"] == user_id]

        if status:
            history = [h for h in history if h["status"] == status]

        return history[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        total = len(self.verification_history)
        allowed = sum(1 for h in self.verification_history if h["status"] == "allowed")
        denied = sum(1 for h in self.verification_history if h["status"] == "denied")
        challenged = sum(1 for h in self.verification_history if h["status"] == "challenged")

        return {
            "total_verifications": total,
            "allowed": allowed,
            "denied": denied,
            "challenged": challenged,
            "allowance_rate": allowed / total if total > 0 else 0.0,
            "active_sessions": len([s for s in self.sessions.values() if s["status"] == "active"]),
            "policies_enabled": len([p for p in self.policies.values() if p["enabled"]]),
        }

    def get_risk_assessment(self, user_id: str) -> dict[str, Any]:
        user_verifications = [h for h in self.verification_history if h["user_id"] == user_id]

        if not user_verifications:
            return {"user_id": user_id, "risk_score": 0.0, "risk_level": "low"}

        avg_risk = sum(h["risk_score"] for h in user_verifications) / len(user_verifications)
        denial_rate = sum(1 for h in user_verifications if h["status"] == "denied") / len(user_verifications)

        risk_score = (avg_risk * 0.7 + denial_rate * 0.3)
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.6 else "high"

        return {
            "user_id": user_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_verifications": len(user_verifications),
            "denial_rate": denial_rate,
        }
