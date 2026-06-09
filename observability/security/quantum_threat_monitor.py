from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


QUANTUM_THREAT_ALERTS = Counter(
    "quantum_threat_alerts_total",
    "Total quantum threat alerts",
    labelnames=["threat_type", "severity"],
)

QUANTUM_KEY_EXCHANGE_EVENTS = Counter(
    "quantum_key_exchange_events_total",
    "Total quantum key exchange events",
    labelnames=["status", "algorithm"],
)

QUANTUM_CRYPTO_MIGRATION_STATUS = Gauge(
    "quantum_crypto_migration_status",
    "Status of post-quantum crypto migration",
    labelnames=["component", "algorithm"],
)

QUANTUM_THREAT_SCORE = Gauge(
    "quantum_threat_score",
    "Quantum threat score (0-1)",
    labelnames=["threat_type"],
)

QUANTUM_HARVEST_NOW_EVENTS = Counter(
    "quantum_harvest_now_decrypt_later_events_total",
    "Total harvest-now-decrypt-later events",
    labelnames=["data_classification", "status"],
)

QUANTUM_MIGRATION_PROGRESS = Gauge(
    "quantum_migration_progress_percent",
    "Post-quantum migration progress",
    labelnames=["component"],
)


class QuantumThreatMonitor:
    def __init__(self):
        self.quantum_computing_power: dict[str, int] = {
            "current_estimate": 1000,
            "threshold_for_crypto_break": 4096,
            "timeline_years": 10,
        }
        self.pqc_algorithms = {
            "key_exchange": ["CRYSTALS-Kyber", "NTRU", "SABER"],
            "digital_signature": ["CRYSTALS-Dilithium", "FALCON", "SPHINCS+"],
            "hash": ["SHA-3", "BLAKE3"],
        }
        self.migration_status: dict[str, dict[str, Any]] = {}
        self.threat_history: list[dict[str, Any]] = []

    def assess_quantum_threat(self) -> dict[str, Any]:
        current_power = self.quantum_computing_power["current_estimate"]
        threshold = self.quantum_computing_power["threshold_for_crypto_break"]
        timeline = self.quantum_computing_power["timeline_years"]

        threat_level = min(1.0, current_power / threshold)
        years_to_break = max(0, timeline * (1 - threat_level))

        threat_type = "none"
        severity = "low"
        if threat_level > 0.8:
            threat_type = "imminent"
            severity = "critical"
        elif threat_level > 0.5:
            threat_type = "moderate"
            severity = "high"
        elif threat_level > 0.2:
            threat_type = "low"
            severity = "medium"

        QUANTUM_THREAT_SCORE.labels(threat_type="overall").set(threat_level)

        if threat_level > 0.5:
            QUANTUM_THREAT_ALERTS.labels(
                threat_type=threat_type,
                severity=severity,
            ).inc()

        result = {
            "threat_level": threat_level,
            "threat_type": threat_type,
            "severity": severity,
            "years_to_crypto_break": years_to_break,
            "current_qubit_estimate": current_power,
            "threshold_for_crypto_break": threshold,
            "assessed_at": time.time(),
        }

        self.threat_history.append(result)
        if len(self.threat_history) > 1000:
            self.threat_history = self.threat_history[-1000:]

        return result

    def monitor_harvest_now_decrypt_later(
        self,
        data_classification: str,
        data_volume_gb: float,
        encryption_algorithm: str,
        exposure_duration_years: float,
    ) -> dict[str, Any]:
        pqc_protected = encryption_algorithm in [
            "AES-256-GCM",
            "ChaCha20-Poly1305",
            "CRYSTALS-Kyber",
            "CRYSTALS-Dilithium",
        ]

        risk_score = 0.0
        if not pqc_protected:
            risk_score = min(1.0, (data_volume_gb / 100) * (exposure_duration_years / 10))

        status = "protected" if pqc_protected else "at_risk"

        QUANTUM_HARVEST_NOW_EVENTS.labels(
            data_classification=data_classification,
            status=status,
        ).inc()

        QUANTUM_THREAT_SCORE.labels(threat_type="harvest_now_decrypt_later").set(risk_score)

        return {
            "data_classification": data_classification,
            "data_volume_gb": data_volume_gb,
            "encryption_algorithm": encryption_algorithm,
            "exposure_duration_years": exposure_duration_years,
            "pqc_protected": pqc_protected,
            "risk_score": risk_score,
            "status": status,
            "recommended_action": "migrate_to_pqc" if not pqc_protected else "maintain_current",
            "assessed_at": time.time(),
        }

    def check_migration_status(
        self,
        component: str,
        current_algorithm: str,
        target_algorithm: str,
        migration_progress: float,
    ) -> dict[str, Any]:
        is_migrated = current_algorithm == target_algorithm
        pqc_algorithm = target_algorithm in [
            "CRYSTALS-Kyber",
            "CRYSTALS-Dilithium",
            "FALCON",
            "SPHINCS+",
            "NTRU",
            "SABER",
        ]

        QUANTUM_CRYPTO_MIGRATION_STATUS.labels(
            component=component,
            algorithm=target_algorithm,
        ).set(1.0 if is_migrated else 0.0)

        QUANTUM_MIGRATION_PROGRESS.labels(component=component).set(migration_progress * 100)

        self.migration_status[component] = {
            "current_algorithm": current_algorithm,
            "target_algorithm": target_algorithm,
            "is_migrated": is_migrated,
            "pqc_algorithm": pqc_algorithm,
            "migration_progress": migration_progress,
            "updated_at": time.time(),
        }

        return self.migration_status[component]

    def get_migration_overview(self) -> dict[str, Any]:
        total_components = len(self.migration_status)
        migrated_components = sum(1 for s in self.migration_status.values() if s["is_migrated"])

        component_details = {}
        for component, status in self.migration_status.items():
            component_details[component] = {
                "current_algorithm": status["current_algorithm"],
                "target_algorithm": status["target_algorithm"],
                "is_migrated": status["is_migrated"],
                "migration_progress": status["migration_progress"],
            }

        return {
            "total_components": total_components,
            "migrated_components": migrated_components,
            "migration_percentage": (migrated_components / total_components * 100) if total_components > 0 else 0,
            "components": component_details,
        }

    def get_threat_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.threat_history[-limit:]

    def get_recommendations(self) -> list[dict[str, Any]]:
        recommendations = []

        threat_assessment = self.assess_quantum_threat()
        if threat_assessment["threat_level"] > 0.5:
            recommendations.append({
                "priority": "high",
                "category": "crypto_migration",
                "description": "Accelerate post-quantum cryptography migration",
                "details": f"Quantum threat level is {threat_assessment['threat_level']:.2f}",
            })

        migration_overview = self.get_migration_overview()
        if migration_overview["migration_percentage"] < 100:
            recommendations.append({
                "priority": "medium",
                "category": "migration",
                "description": f"Complete post-quantum migration ({migration_overview['migration_percentage']:.1f}% done)",
                "details": f"{migration_overview['migrated_components']}/{migration_overview['total_components']} components migrated",
            })

        recommendations.append({
            "priority": "low",
            "category": "monitoring",
            "description": "Monitor quantum computing advances",
            "details": "Review quantum threat assessment quarterly",
        })

        return recommendations

    def export_assessment(self) -> str:
        import json
        return json.dumps({
            "threat_assessment": self.assess_quantum_threat(),
            "migration_overview": self.get_migration_overview(),
            "recommendations": self.get_recommendations(),
            "threat_history": self.threat_history[-10:],
        }, indent=2, default=str)
