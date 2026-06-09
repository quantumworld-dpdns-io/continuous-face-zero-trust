"""Risk scoring engine."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskFactor:
    name: str
    weight: float
    score: float


class RiskEngine:
    def __init__(self, threshold_high: float = 0.7, threshold_medium: float = 0.4):
        self.threshold_high = threshold_high
        self.threshold_medium = threshold_medium

    def score(self, device_id: str, platform: str, liveness: dict, **kwargs) -> dict:
        factors: list[RiskFactor] = []

        liveness_confidence = liveness.get("confidence", 0.0)
        factors.append(RiskFactor("liveness", 0.3, 1.0 - liveness_confidence))

        factors.append(RiskFactor("platform", 0.1, 0.0 if platform in ("web", "mobile") else 0.5))

        total = sum(f.score * f.weight for f in factors)
        total_weight = sum(f.weight for f in factors)
        normalized = total / total_weight if total_weight > 0 else 0.0

        level = "high" if normalized >= self.threshold_high else "medium" if normalized >= self.threshold_medium else "low"

        return {
            "score": round(normalized, 4),
            "level": level,
            "factors": [f.name for f in factors if f.score > 0.3],
        }
