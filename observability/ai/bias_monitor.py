from __future__ import annotations

import time
from typing import Any

import numpy as np
from prometheus_client import Gauge, Counter, Histogram


BIAS_METRIC_FAIRNESS = Gauge(
    "bias_metric_fairness",
    "Fairness metric across demographic groups",
    labelnames=["metric_name", "group"],
)

BIAS_METRIC_DISPARITY = Gauge(
    "bias_metric_disparity",
    "Disparity metric between demographic groups",
    labelnames=["metric_name", "group_a", "group_b"],
)

BIAS_METRIC_EQUAL_OPPORTUNITY = Gauge(
    "bias_metric_equal_opportunity",
    "Equal opportunity metric",
    labelnames=["group"],
)

BIAS_METRIC_DEMOGRAPHIC_PARITY = Gauge(
    "bias_metric_demographic_parity",
    "Demographic parity metric",
    labelnames=["group"],
)

BIAS_ALERT = Counter(
    "bias_alerts_total",
    "Total bias alerts triggered",
    labelnames=["metric_name", "severity", "group"],
)

BIAS_CHECKS = Counter(
    "bias_checks_total",
    "Total bias checks performed",
    labelnames=["metric_name", "status"],
)

BIAS_CHECK_LATENCY = Histogram(
    "bias_check_latency_seconds",
    "Latency of bias checks",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    labelnames=["metric_name"],
)


class BiasMonitor:
    def __init__(
        self,
        fairness_threshold: float = 0.8,
        disparity_threshold: float = 0.2,
        equal_opportunity_threshold: float = 0.8,
        demographic_parity_threshold: float = 0.8,
    ):
        self.fairness_threshold = fairness_threshold
        self.disparity_threshold = disparity_threshold
        self.equal_opportunity_threshold = equal_opportunity_threshold
        self.demographic_parity_threshold = demographic_parity_threshold
        self.bias_history: dict[str, list[dict[str, Any]]] = {}

    def calculate_fairness(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        demographic_groups: np.ndarray,
    ) -> dict[str, float]:
        groups = np.unique(demographic_groups)
        group_fairness = {}

        for group in groups:
            mask = demographic_groups == group
            group_preds = predictions[mask]
            group_gt = ground_truth[mask]

            if len(group_preds) > 0:
                accuracy = np.mean(group_preds == group_gt)
                group_fairness[group] = accuracy
            else:
                group_fairness[group] = 0.0

        return group_fairness

    def calculate_disparity(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        demographic_groups: np.ndarray,
    ) -> dict[str, float]:
        groups = np.unique(demographic_groups)
        group_rates = {}

        for group in groups:
            mask = demographic_groups == group
            group_preds = predictions[mask]
            group_gt = ground_truth[mask]

            if len(group_preds) > 0:
                true_positive_rate = np.sum((group_preds == 1) & (group_gt == 1)) / np.sum(group_gt == 1) if np.sum(group_gt == 1) > 0 else 0.0
                group_rates[group] = true_positive_rate
            else:
                group_rates[group] = 0.0

        disparities = {}
        for i, group_a in enumerate(groups):
            for group_b in groups[i + 1:]:
                disparity = abs(group_rates[group_a] - group_rates[group_b])
                disparities[f"{group_a}_vs_{group_b}"] = disparity

        return disparities

    def calculate_equal_opportunity(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        demographic_groups: np.ndarray,
    ) -> dict[str, float]:
        groups = np.unique(demographic_groups)
        equal_opportunity = {}

        for group in groups:
            mask = demographic_groups == group
            group_preds = predictions[mask]
            group_gt = ground_truth[mask]

            if len(group_preds) > 0 and np.sum(group_gt == 1) > 0:
                tpr = np.sum((group_preds == 1) & (group_gt == 1)) / np.sum(group_gt == 1)
                equal_opportunity[group] = tpr
            else:
                equal_opportunity[group] = 0.0

        return equal_opportunity

    def calculate_demographic_parity(
        self,
        predictions: np.ndarray,
        demographic_groups: np.ndarray,
    ) -> dict[str, float]:
        groups = np.unique(demographic_groups)
        demographic_parity = {}

        for group in groups:
            mask = demographic_groups == group
            group_preds = predictions[mask]

            if len(group_preds) > 0:
                positive_rate = np.mean(group_preds == 1)
                demographic_parity[group] = positive_rate
            else:
                demographic_parity[group] = 0.0

        return demographic_parity

    def check_bias(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        demographic_groups: np.ndarray,
        metric_name: str = "face_recognition",
    ) -> dict[str, Any]:
        start_time = time.time()

        fairness = self.calculate_fairness(predictions, ground_truth, demographic_groups)
        disparity = self.calculate_disparity(predictions, ground_truth, demographic_groups)
        equal_opportunity = self.calculate_equal_opportunity(predictions, ground_truth, demographic_groups)
        demographic_parity = self.calculate_demographic_parity(predictions, demographic_groups)

        for group, score in fairness.items():
            BIAS_METRIC_FAIRNESS.labels(metric_name=metric_name, group=group).set(score)

        for pair, score in disparity.items():
            group_a, group_b = pair.split("_vs_")
            BIAS_METRIC_DISPARITY.labels(
                metric_name=metric_name,
                group_a=group_a,
                group_b=group_b,
            ).set(score)

        for group, score in equal_opportunity.items():
            BIAS_METRIC_EQUAL_OPPORTUNITY.labels(group=group).set(score)

        for group, score in demographic_parity.items():
            BIAS_METRIC_DEMOGRAPHIC_PARITY.labels(group=group).set(score)

        is_biased = False
        bias_type = "none"
        severity = "low"
        biased_groups = []

        min_fairness = min(fairness.values()) if fairness else 1.0
        max_disparity = max(disparity.values()) if disparity else 0.0
        min_equal_opportunity = min(equal_opportunity.values()) if equal_opportunity else 1.0

        if min_fairness < self.fairness_threshold:
            is_biased = True
            bias_type = "fairness"
            severity = "high" if min_fairness < self.fairness_threshold * 0.5 else "medium"
            biased_groups = [g for g, s in fairness.items() if s < self.fairness_threshold]

        if max_disparity > self.disparity_threshold:
            is_biased = True
            bias_type = "disparity"
            severity = "high" if max_disparity > self.disparity_threshold * 2 else "medium"

        if min_equal_opportunity < self.equal_opportunity_threshold:
            is_biased = True
            bias_type = "equal_opportunity"
            severity = "high" if min_equal_opportunity < self.equal_opportunity_threshold * 0.5 else "medium"

        if is_biased:
            for group in biased_groups:
                BIAS_ALERT.labels(
                    metric_name=metric_name,
                    severity=severity,
                    group=group,
                ).inc()

        BIAS_CHECKS.labels(
            metric_name=metric_name,
            status="biased" if is_biased else "fair",
        ).inc()

        duration = time.time() - start_time
        BIAS_CHECK_LATENCY.labels(metric_name=metric_name).observe(duration)

        result = {
            "metric_name": metric_name,
            "is_biased": is_biased,
            "bias_type": bias_type,
            "severity": severity,
            "biased_groups": biased_groups,
            "fairness": fairness,
            "disparity": disparity,
            "equal_opportunity": equal_opportunity,
            "demographic_parity": demographic_parity,
            "thresholds": {
                "fairness": self.fairness_threshold,
                "disparity": self.disparity_threshold,
                "equal_opportunity": self.equal_opportunity_threshold,
                "demographic_parity": self.demographic_parity_threshold,
            },
            "timestamp": time.time(),
        }

        if metric_name not in self.bias_history:
            self.bias_history[metric_name] = []
        self.bias_history[metric_name].append(result)

        if len(self.bias_history[metric_name]) > 1000:
            self.bias_history[metric_name] = self.bias_history[metric_name][-1000:]

        return result

    def get_bias_summary(
        self,
        metric_name: str,
    ) -> dict[str, Any]:
        if metric_name not in self.bias_history:
            return {"metric_name": metric_name, "checks": 0}

        history = self.bias_history[metric_name]
        biased_count = sum(1 for h in history if h["is_biased"])

        return {
            "metric_name": metric_name,
            "checks": len(history),
            "biased_count": biased_count,
            "bias_rate": biased_count / len(history) if history else 0.0,
            "latest_check": history[-1] if history else None,
        }

    def export_history(self) -> dict[str, Any]:
        return {"bias_history": self.bias_history}
