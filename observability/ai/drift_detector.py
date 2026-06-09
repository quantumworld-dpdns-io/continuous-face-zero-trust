from __future__ import annotations

import json
import time
from typing import Any

import numpy as np
from scipy import stats
from prometheus_client import Gauge, Counter, Histogram


DRIFT_DETECTION_PSI = Gauge(
    "drift_detection_psi",
    "Population Stability Index for feature drift",
    labelnames=["feature_name", "window"],
)

DRIFT_DETECTION_KL_DIVERGENCE = Gauge(
    "drift_detection_kl_divergence",
    "KL Divergence for feature drift",
    labelnames=["feature_name", "window"],
)

DRIFT_DETECTION_JS_DIVERGENCE = Gauge(
    "drift_detection_js_divergence",
    "Jensen-Shannon Divergence for feature drift",
    labelnames=["feature_name", "window"],
)

DRIFT_DETECTION_WASSERSTEIN_DISTANCE = Gauge(
    "drift_detection_wasserstein_distance",
    "Wasserstein Distance for feature drift",
    labelnames=["feature_name", "window"],
)

DRIFT_DETECTION_ALERT = Counter(
    "drift_detection_alerts_total",
    "Total drift detection alerts",
    labelnames=["feature_name", "drift_type", "severity"],
)

DRIFT_DETECTION_CHECKS = Counter(
    "drift_detection_checks_total",
    "Total drift detection checks performed",
    labelnames=["feature_name", "status"],
)

DRIFT_DETECTION_LATENCY = Histogram(
    "drift_detection_latency_seconds",
    "Latency of drift detection checks",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    labelnames=["feature_name"],
)


class DriftDetector:
    def __init__(
        self,
        psi_threshold: float = 0.2,
        kl_threshold: float = 0.1,
        js_threshold: float = 0.1,
        wasserstein_threshold: float = 0.1,
        window_size: int = 1000,
    ):
        self.psi_threshold = psi_threshold
        self.kl_threshold = kl_threshold
        self.js_threshold = js_threshold
        self.wasserstein_threshold = wasserstein_threshold
        self.window_size = window_size
        self.reference_distributions: dict[str, np.ndarray] = {}
        self.drift_history: dict[str, list[dict[str, Any]]] = {}

    def set_reference_distribution(
        self,
        feature_name: str,
        reference_data: np.ndarray,
    ) -> None:
        self.reference_distributions[feature_name] = reference_data

    def calculate_psi(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        bins: int = 10,
    ) -> float:
        expected_hist, bin_edges = np.histogram(expected, bins=bins, density=True)
        actual_hist, _ = np.histogram(actual, bins=bin_edges, density=True)

        expected_hist = np.clip(expected_hist, 1e-10, None)
        actual_hist = np.clip(actual_hist, 1e-10, None)

        psi = np.sum((actual_hist - expected_hist) * np.log(actual_hist / expected_hist))
        return float(psi)

    def calculate_kl_divergence(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        bins: int = 10,
    ) -> float:
        expected_hist, bin_edges = np.histogram(expected, bins=bins, density=True)
        actual_hist, _ = np.histogram(actual, bins=bin_edges, density=True)

        expected_hist = np.clip(expected_hist, 1e-10, None)
        actual_hist = np.clip(actual_hist, 1e-10, None)

        kl_div = stats.entropy(expected_hist, actual_hist)
        return float(kl_div)

    def calculate_js_divergence(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        bins: int = 10,
    ) -> float:
        expected_hist, bin_edges = np.histogram(expected, bins=bins, density=True)
        actual_hist, _ = np.histogram(actual, bins=bin_edges, density=True)

        expected_hist = np.clip(expected_hist, 1e-10, None)
        actual_hist = np.clip(actual_hist, 1e-10, None)

        m = 0.5 * (expected_hist + actual_hist)
        js_div = 0.5 * stats.entropy(expected_hist, m) + 0.5 * stats.entropy(actual_hist, m)
        return float(js_div)

    def calculate_wasserstein_distance(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
    ) -> float:
        return float(stats.wasserstein_distance(expected, actual))

    def detect_drift(
        self,
        feature_name: str,
        current_data: np.ndarray,
        window: str = "current",
    ) -> dict[str, Any]:
        start_time = time.time()

        if feature_name not in self.reference_distributions:
            raise ValueError(f"No reference distribution set for feature: {feature_name}")

        reference = self.reference_distributions[feature_name]

        psi = self.calculate_psi(reference, current_data)
        kl_div = self.calculate_kl_divergence(reference, current_data)
        js_div = self.calculate_js_divergence(reference, current_data)
        wasserstein = self.calculate_wasserstein_distance(reference, current_data)

        DRIFT_DETECTION_PSI.labels(feature_name=feature_name, window=window).set(psi)
        DRIFT_DETECTION_KL_DIVERGENCE.labels(feature_name=feature_name, window=window).set(kl_div)
        DRIFT_DETECTION_JS_DIVERGENCE.labels(feature_name=feature_name, window=window).set(js_div)
        DRIFT_DETECTION_WASSERSTEIN_DISTANCE.labels(feature_name=feature_name, window=window).set(wasserstein)

        is_drifted = False
        drift_type = "none"
        severity = "low"

        if psi > self.psi_threshold:
            is_drifted = True
            drift_type = "psi"
            severity = "high" if psi > self.psi_threshold * 2 else "medium"
        elif kl_div > self.kl_threshold:
            is_drifted = True
            drift_type = "kl_divergence"
            severity = "high" if kl_div > self.kl_threshold * 2 else "medium"
        elif js_div > self.js_threshold:
            is_drifted = True
            drift_type = "js_divergence"
            severity = "medium"
        elif wasserstein > self.wasserstein_threshold:
            is_drifted = True
            drift_type = "wasserstein"
            severity = "low"

        if is_drifted:
            DRIFT_DETECTION_ALERT.labels(
                feature_name=feature_name,
                drift_type=drift_type,
                severity=severity,
            ).inc()

        DRIFT_DETECTION_CHECKS.labels(
            feature_name=feature_name,
            status="drifted" if is_drifted else "stable",
        ).inc()

        duration = time.time() - start_time
        DRIFT_DETECTION_LATENCY.labels(feature_name=feature_name).observe(duration)

        result = {
            "feature_name": feature_name,
            "is_drifted": is_drifted,
            "drift_type": drift_type,
            "severity": severity,
            "metrics": {
                "psi": psi,
                "kl_divergence": kl_div,
                "js_divergence": js_div,
                "wasserstein_distance": wasserstein,
            },
            "thresholds": {
                "psi": self.psi_threshold,
                "kl_divergence": self.kl_threshold,
                "js_divergence": self.js_threshold,
                "wasserstein_distance": self.wasserstein_threshold,
            },
            "window": window,
            "timestamp": time.time(),
        }

        if feature_name not in self.drift_history:
            self.drift_history[feature_name] = []
        self.drift_history[feature_name].append(result)

        if len(self.drift_history[feature_name]) > 1000:
            self.drift_history[feature_name] = self.drift_history[feature_name][-1000:]

        return result

    def get_drift_summary(
        self,
        feature_name: str,
    ) -> dict[str, Any]:
        if feature_name not in self.drift_history:
            return {"feature_name": feature_name, "checks": 0}

        history = self.drift_history[feature_name]
        drifted_count = sum(1 for h in history if h["is_drifted"])

        return {
            "feature_name": feature_name,
            "checks": len(history),
            "drifted_count": drifted_count,
            "drift_rate": drifted_count / len(history) if history else 0.0,
            "latest_check": history[-1] if history else None,
        }

    def export_history(self) -> dict[str, Any]:
        return {
            "drift_history": self.drift_history,
            "reference_distributions": {
                k: v.tolist() for k, v in self.reference_distributions.items()
            },
        }
