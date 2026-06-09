from __future__ import annotations

import time
from typing import Any

import numpy as np
from prometheus_client import Counter, Gauge, Histogram


ANOMALY_SCORE = Gauge(
    "anomaly_detection_score",
    "Anomaly detection score",
    labelnames=["model_name", "feature"],
)

ANOMALY_ALERTS = Counter(
    "anomaly_detection_alerts_total",
    "Total anomaly detection alerts",
    labelnames=["model_name", "severity"],
)

ANOMALY_DETECTIONS = Counter(
    "anomaly_detection_total",
    "Total anomaly detections",
    labelnames=["model_name", "status"],
)

ANOMALY_LATENCY = Histogram(
    "anomaly_detection_latency_seconds",
    "Latency of anomaly detection",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    labelnames=["model_name"],
)

ANOMALY_THRESHOLD = Gauge(
    "anomaly_detection_threshold",
    "Current anomaly detection threshold",
    labelnames=["model_name"],
)


class AnomalyDetector:
    def __init__(
        self,
        model_name: str = "auth_anomaly",
        contamination: float = 0.1,
        window_size: int = 100,
        threshold: float = 0.5,
    ):
        self.model_name = model_name
        self.contamination = contamination
        self.window_size = window_size
        self.threshold = threshold
        self.history: list[dict[str, Any]] = []
        self.baseline_mean: dict[str, float] = {}
        self.baseline_std: dict[str, float] = {}
        self.is_fitted = False

    def fit(self, data: list[dict[str, Any]]) -> None:
        features = self._extract_features(data)

        for feature_name, feature_values in features.items():
            if len(feature_values) > 0:
                self.baseline_mean[feature_name] = float(np.mean(feature_values))
                self.baseline_std[feature_name] = float(np.std(feature_values))
                if self.baseline_std[feature_name] == 0:
                    self.baseline_std[feature_name] = 1.0

        self.is_fitted = True
        ANOMALY_THRESHOLD.labels(model_name=self.model_name).set(self.threshold)

    def _extract_features(self, data: list[dict[str, Any]]) -> dict[str, list[float]]:
        features: dict[str, list[float]] = {}

        for event in data:
            if "timestamp" in event:
                if "hour" not in features:
                    features["hour"] = []
                features["hour"].append(float(event["timestamp"] % 86400 / 3600))

            if "event_type" in event:
                if "event_type_encoded" not in features:
                    features["event_type_encoded"] = []
                event_types = {"authentication": 0, "biometric": 1, "api_request": 2, "session": 3}
                features["event_type_encoded"].append(float(event_types.get(event["event_type"], -1)))

            if "status" in event:
                if "status_encoded" not in features:
                    features["status_encoded"] = []
                statuses = {"success": 0, "failed": 1, "denied": 2}
                features["status_encoded"].append(float(statuses.get(event["status"], -1)))

            if "ip_address" in event:
                if "ip_entropy" not in features:
                    features["ip_entropy"] = []
                features["ip_entropy"].append(self._calculate_entropy(event["ip_address"]))

        return features

    def _calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0

        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1

        entropy = 0.0
        for count in char_counts.values():
            prob = count / len(text)
            if prob > 0:
                entropy -= prob * np.log2(prob)

        return float(entropy)

    def predict(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self.is_fitted:
            self.fit([event])

        start_time = time.time()

        features = self._extract_features([event])
        anomaly_scores = {}

        for feature_name, feature_values in features.items():
            if feature_name in self.baseline_mean and len(feature_values) > 0:
                value = feature_values[0]
                mean = self.baseline_mean[feature_name]
                std = self.baseline_std[feature_name]

                z_score = abs(value - mean) / std if std > 0 else 0.0
                anomaly_score = 1.0 / (1.0 + np.exp(-z_score))

                anomaly_scores[feature_name] = float(anomaly_score)
                ANOMALY_SCORE.labels(
                    model_name=self.model_name,
                    feature=feature_name,
                ).set(anomaly_score)

        overall_score = np.mean(list(anomaly_scores.values())) if anomaly_scores else 0.0
        is_anomaly = overall_score > self.threshold

        status = "anomaly" if is_anomaly else "normal"
        ANOMALY_DETECTIONS.labels(
            model_name=self.model_name,
            status=status,
        ).inc()

        if is_anomaly:
            severity = "high" if overall_score > 0.8 else "medium" if overall_score > 0.6 else "low"
            ANOMALY_ALERTS.labels(
                model_name=self.model_name,
                severity=severity,
            ).inc()

        duration = time.time() - start_time
        ANOMALY_LATENCY.labels(model_name=self.model_name).observe(duration)

        result = {
            "is_anomaly": is_anomaly,
            "anomaly_score": float(overall_score),
            "feature_scores": anomaly_scores,
            "threshold": self.threshold,
            "event": event,
            "detected_at": time.time(),
        }

        self.history.append(result)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        return result

    def update_baseline(self, new_data: list[dict[str, Any]]) -> None:
        all_data = []
        for event in new_data:
            features = self._extract_features([event])
            for feature_name, feature_values in features.items():
                if feature_name not in self.baseline_mean:
                    self.baseline_mean[feature_name] = feature_values[0]
                    self.baseline_std[feature_name] = 1.0
                else:
                    old_mean = self.baseline_mean[feature_name]
                    old_std = self.baseline_std[feature_name]
                    new_value = feature_values[0]
                    self.baseline_mean[feature_name] = (old_mean + new_value) / 2
                    self.baseline_std[feature_name] = max(old_std, abs(new_value - old_mean))

    def get_anomalies(
        self,
        min_score: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        anomalies = [h for h in self.history if h["is_anomaly"]]

        if min_score is not None:
            anomalies = [a for a in anomalies if a["anomaly_score"] >= min_score]

        return anomalies[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        total = len(self.history)
        anomalies = sum(1 for h in self.history if h["is_anomaly"])

        return {
            "total_predictions": total,
            "anomalies_detected": anomalies,
            "anomaly_rate": anomalies / total if total > 0 else 0.0,
            "mean_anomaly_score": float(np.mean([h["anomaly_score"] for h in self.history])) if self.history else 0.0,
            "max_anomaly_score": float(max([h["anomaly_score"] for h in self.history])) if self.history else 0.0,
            "baseline_features": list(self.baseline_mean.keys()),
        }

    def set_threshold(self, threshold: float) -> None:
        self.threshold = threshold
        ANOMALY_THRESHOLD.labels(model_name=self.model_name).set(threshold)

    def export_history(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "history": self.history,
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
        }
