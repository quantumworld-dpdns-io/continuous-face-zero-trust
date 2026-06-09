from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


COMPLIANCE_CHECKS = Counter(
    "compliance_checks_total",
    "Total compliance checks",
    labelnames=["standard", "status"],
)

COMPLIANCE_VIOLATIONS = Counter(
    "compliance_violations_total",
    "Total compliance violations",
    labelnames=["standard", "control", "severity"],
)

COMPLIANCE_SCORE = Gauge(
    "compliance_score",
    "Compliance score by standard",
    labelnames=["standard"],
)

COMPLIANCE_CHECK_LATENCY = Histogram(
    "compliance_check_latency_seconds",
    "Latency of compliance checks",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    labelnames=["standard"],
)


class ComplianceChecker:
    def __init__(self):
        self.standards = {
            "SOC2": self._get_soc2_controls(),
            "HIPAA": self._get_hipaa_controls(),
            "GDPR": self._get_gdpr_controls(),
        }
        self.check_results: dict[str, list[dict[str, Any]]] = {}
        self.violation_history: list[dict[str, Any]] = []

    def _get_soc2_controls(self) -> dict[str, dict[str, Any]]:
        return {
            "CC6.1": {
                "name": "Logical Access Security",
                "description": "The entity implements logical access security measures",
                "category": "access_control",
                "checks": [
                    "multi_factor_authentication",
                    "role_based_access_control",
                    "password_policy",
                    "session_management",
                ],
            },
            "CC6.2": {
                "name": "Authentication",
                "description": "Prior to issuing system credentials, the entity registers and authorizes new internal and external users",
                "category": "access_control",
                "checks": [
                    "user_registration_process",
                    "authorization_workflow",
                    "credential_management",
                ],
            },
            "CC6.3": {
                "name": "Access Control",
                "description": "The entity authorizes, modifies, or removes access to data, software, functions, and other system components",
                "category": "access_control",
                "checks": [
                    "access_review_process",
                    "access_modification_workflow",
                    "access_revocation_process",
                ],
            },
            "CC7.1": {
                "name": "Security Monitoring",
                "description": "To meet its objectives, the entity uses detection and monitoring procedures",
                "category": "monitoring",
                "checks": [
                    "intrusion_detection",
                    "security_logging",
                    "anomaly_detection",
                    "alerting_mechanisms",
                ],
            },
            "CC8.1": {
                "name": "Change Management",
                "description": "The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, and implements changes",
                "category": "change_management",
                "checks": [
                    "change_approval_process",
                    "change_testing",
                    "change_documentation",
                    "rollback_procedures",
                ],
            },
        }

    def _get_hipaa_controls(self) -> dict[str, dict[str, Any]]:
        return {
            "164.312(a)(1)": {
                "name": "Access Control",
                "description": "Implement technical policies and procedures for electronic information systems that maintain ePHI",
                "category": "access_control",
                "checks": [
                    "unique_user_identification",
                    "emergency_access_procedure",
                    "automatic_logoff",
                    "encryption_decryption",
                ],
            },
            "164.312(a)(2)(i)": {
                "name": "Unique User Identification",
                "description": "Implement procedures to obtain necessary ePHI",
                "category": "access_control",
                "checks": [
                    "unique_user_ids",
                    "user_authentication",
                    "access_logs",
                ],
            },
            "164.312(b)": {
                "name": "Audit Controls",
                "description": "Implement hardware, software, and/or procedural mechanisms that record and examine activity",
                "category": "audit",
                "checks": [
                    "audit_logging",
                    "audit_review",
                    "audit_trail_integrity",
                ],
            },
            "164.312(c)(1)": {
                "name": "Integrity",
                "description": "Implement policies and procedures to protect ePHI from improper alteration or destruction",
                "category": "data_integrity",
                "checks": [
                    "data_integrity_controls",
                    "authentication_mechanisms",
                    "backup_verification",
                ],
            },
            "164.312(d)": {
                "name": "Person or Entity Authentication",
                "description": "Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed",
                "category": "authentication",
                "checks": [
                    "identity_verification",
                    "multi_factor_authentication",
                    "biometric_authentication",
                ],
            },
            "164.312(e)(1)": {
                "name": "Transmission Security",
                "description": "Implement technical security measures to guard against unauthorized access to ePHI",
                "category": "encryption",
                "checks": [
                    "tls_encryption",
                    "data_in_transit_protection",
                    "network_segmentation",
                ],
            },
        }

    def _get_gdpr_controls(self) -> dict[str, dict[str, Any]]:
        return {
            "Art.5": {
                "name": "Principles of Processing",
                "description": "Personal data shall be processed lawfully, fairly, and transparently",
                "category": "data_processing",
                "checks": [
                    "lawful_basis",
                    "purpose_limitation",
                    "data_minimization",
                    "accuracy",
                    "storage_limitation",
                    "integrity_confidentiality",
                ],
            },
            "Art.25": {
                "name": "Data Protection by Design",
                "description": "Implement appropriate technical and organizational measures designed to implement data protection principles",
                "category": "privacy_by_design",
                "checks": [
                    "privacy_impact_assessment",
                    "data_protection_measures",
                    "consent_mechanisms",
                ],
            },
            "Art.32": {
                "name": "Security of Processing",
                "description": "Implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk",
                "category": "security",
                "checks": [
                    "encryption",
                    "pseudonymization",
                    "confidentiality",
                    "integrity",
                    "availability",
                    "regular_testing",
                ],
            },
            "Art.33": {
                "name": "Breach Notification",
                "description": "Notify the supervisory authority of a personal data breach",
                "category": "breach_notification",
                "checks": [
                    "breach_detection",
                    "notification_procedure",
                    "notification_timeline",
                ],
            },
            "Art.35": {
                "name": "Data Protection Impact Assessment",
                "description": "Carry out a data protection impact assessment",
                "category": "privacy_by_design",
                "checks": [
                    "dpo_involvement",
                    "risk_assessment",
                    "mitigation_measures",
                ],
            },
        }

    def check_compliance(
        self,
        standard: str,
        system_config: dict[str, Any],
    ) -> dict[str, Any]:
        start_time = time.time()

        if standard not in self.standards:
            raise ValueError(f"Unknown compliance standard: {standard}")

        controls = self.standards[standard]
        results = {}
        violations = []

        for control_id, control in controls.items():
            control_result = self._check_control(control_id, control, system_config)
            results[control_id] = control_result

            if not control_result["compliant"]:
                violations.append({
                    "control_id": control_id,
                    "control_name": control["name"],
                    "violations": control_result["violations"],
                    "severity": control_result["severity"],
                })

                COMPLIANCE_VIOLATIONS.labels(
                    standard=standard,
                    control=control_id,
                    severity=control_result["severity"],
                ).inc()

        compliant_controls = sum(1 for r in results.values() if r["compliant"])
        total_controls = len(results)
        compliance_score = compliant_controls / total_controls if total_controls > 0 else 0.0

        COMPLIANCE_SCORE.labels(standard=standard).set(compliance_score * 100)

        status = "compliant" if compliance_score >= 0.9 else "non_compliant"
        COMPLIANCE_CHECKS.labels(standard=standard, status=status).inc()

        duration = time.time() - start_time
        COMPLIANCE_CHECK_LATENCY.labels(standard=standard).observe(duration)

        result = {
            "standard": standard,
            "compliance_score": compliance_score,
            "compliant_controls": compliant_controls,
            "total_controls": total_controls,
            "status": status,
            "control_results": results,
            "violations": violations,
            "checked_at": time.time(),
        }

        if standard not in self.check_results:
            self.check_results[standard] = []
        self.check_results[standard].append(result)

        self.violation_history.extend(violations)

        return result

    def _check_control(
        self,
        control_id: str,
        control: dict[str, Any],
        system_config: dict[str, Any],
    ) -> dict[str, Any]:
        violations = []
        severity = "low"

        for check in control["checks"]:
            if not self._evaluate_check(check, system_config):
                violations.append(check)
                if check in ["multi_factor_authentication", "encryption_decryption", "tls_encryption"]:
                    severity = "high"
                elif check in ["access_logs", "audit_logging", "breach_detection"]:
                    severity = "medium"

        return {
            "control_id": control_id,
            "control_name": control["name"],
            "compliant": len(violations) == 0,
            "violations": violations,
            "severity": severity,
            "category": control["category"],
        }

    def _evaluate_check(self, check: str, system_config: dict[str, Any]) -> bool:
        check_mappings = {
            "multi_factor_authentication": lambda c: c.get("mfa_enabled", False),
            "role_based_access_control": lambda c: c.get("rbac_enabled", False),
            "password_policy": lambda c: c.get("password_policy_enabled", False),
            "session_management": lambda c: c.get("session_management_enabled", False),
            "user_registration_process": lambda c: c.get("user_registration_enabled", False),
            "authorization_workflow": lambda c: c.get("authorization_workflow_enabled", False),
            "credential_management": lambda c: c.get("credential_management_enabled", False),
            "access_review_process": lambda c: c.get("access_review_enabled", False),
            "access_modification_workflow": lambda c: c.get("access_modification_enabled", False),
            "access_revocation_process": lambda c: c.get("access_revocation_enabled", False),
            "intrusion_detection": lambda c: c.get("ids_enabled", False),
            "security_logging": lambda c: c.get("security_logging_enabled", False),
            "anomaly_detection": lambda c: c.get("anomaly_detection_enabled", False),
            "alerting_mechanisms": lambda c: c.get("alerting_enabled", False),
            "change_approval_process": lambda c: c.get("change_approval_enabled", False),
            "change_testing": lambda c: c.get("change_testing_enabled", False),
            "change_documentation": lambda c: c.get("change_documentation_enabled", False),
            "rollback_procedures": lambda c: c.get("rollback_procedures_enabled", False),
            "unique_user_identification": lambda c: c.get("unique_user_ids", False),
            "emergency_access_procedure": lambda c: c.get("emergency_access_enabled", False),
            "automatic_logoff": lambda c: c.get("auto_logoff_enabled", False),
            "encryption_decryption": lambda c: c.get("encryption_enabled", False),
            "unique_user_ids": lambda c: c.get("unique_user_ids", False),
            "user_authentication": lambda c: c.get("user_auth_enabled", False),
            "access_logs": lambda c: c.get("access_logs_enabled", False),
            "audit_logging": lambda c: c.get("audit_logging_enabled", False),
            "audit_review": lambda c: c.get("audit_review_enabled", False),
            "audit_trail_integrity": lambda c: c.get("audit_trail_integrity", False),
            "data_integrity_controls": lambda c: c.get("data_integrity_enabled", False),
            "authentication_mechanisms": lambda c: c.get("auth_mechanisms_enabled", False),
            "backup_verification": lambda c: c.get("backup_verification_enabled", False),
            "identity_verification": lambda c: c.get("identity_verification_enabled", False),
            "biometric_authentication": lambda c: c.get("biometric_auth_enabled", False),
            "tls_encryption": lambda c: c.get("tls_enabled", False),
            "data_in_transit_protection": lambda c: c.get("data_transit_protection", False),
            "network_segmentation": lambda c: c.get("network_segmentation_enabled", False),
            "lawful_basis": lambda c: c.get("lawful_basis_documented", False),
            "purpose_limitation": lambda c: c.get("purpose_limitation_enabled", False),
            "data_minimization": lambda c: c.get("data_minimization_enabled", False),
            "accuracy": lambda c: c.get("data_accuracy_controls", False),
            "storage_limitation": lambda c: c.get("storage_limitation_enabled", False),
            "integrity_confidentiality": lambda c: c.get("integrity_confidentiality", False),
            "privacy_impact_assessment": lambda c: c.get("pia_completed", False),
            "data_protection_measures": lambda c: c.get("data_protection_enabled", False),
            "consent_mechanisms": lambda c: c.get("consent_mechanisms_enabled", False),
            "encryption": lambda c: c.get("encryption_enabled", False),
            "pseudonymization": lambda c: c.get("pseudonymization_enabled", False),
            "confidentiality": lambda c: c.get("confidentiality_controls", False),
            "integrity": lambda c: c.get("integrity_controls", False),
            "availability": lambda c: c.get("availability_controls", False),
            "regular_testing": lambda c: c.get("regular_testing_enabled", False),
            "breach_detection": lambda c: c.get("breach_detection_enabled", False),
            "notification_procedure": lambda c: c.get("notification_procedure_enabled", False),
            "notification_timeline": lambda c: c.get("notification_timeline_documented", False),
            "dpo_involvement": lambda c: c.get("dpo_involved", False),
            "risk_assessment": lambda c: c.get("risk_assessment_completed", False),
            "mitigation_measures": lambda c: c.get("mitigation_measures_implemented", False),
        }

        check_fn = check_mappings.get(check)
        if check_fn:
            return check_fn(system_config)
        return True

    def get_compliance_summary(self) -> dict[str, Any]:
        summary = {}
        for standard, results in self.check_results.items():
            if results:
                latest = results[-1]
                summary[standard] = {
                    "compliance_score": latest["compliance_score"],
                    "status": latest["status"],
                    "total_checks": len(results),
                    "violations": len(latest["violations"]),
                }
        return summary

    def get_violation_history(
        self,
        standard: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        violations = self.violation_history

        if standard:
            violations = [v for v in violations if v.get("standard") == standard]

        return violations[-limit:]
