from __future__ import annotations

import json
import time
from typing import Any, Callable

from prometheus_client import Gauge, Counter, Histogram
from .weave_eval import (
    evaluate_accuracy,
    evaluate_fairness,
    evaluate_latency,
    evaluate_confidence,
    evaluate_robustness,
)


EVAL_SUITE_ACCURACY = Gauge(
    "eval_suite_accuracy",
    "Overall accuracy from evaluation suite",
    labelnames=["suite_name", "model_version"],
)

EVAL_SUITE_LATENCY_P50 = Gauge(
    "eval_suite_latency_p50",
    "P50 latency from evaluation suite",
    labelnames=["suite_name", "model_version"],
)

EVAL_SUITE_LATENCY_P95 = Gauge(
    "eval_suite_latency_p95",
    "P95 latency from evaluation suite",
    labelnames=["suite_name", "model_version"],
)

EVAL_SUITE_LATENCY_P99 = Gauge(
    "eval_suite_latency_p99",
    "P99 latency from evaluation suite",
    labelnames=["suite_name", "model_version"],
)

EVAL_SUITE_CONFIDENCE = Gauge(
    "eval_suite_confidence",
    "Mean confidence from evaluation suite",
    labelnames=["suite_name", "model_version"],
)

EVAL_SUITE_FAIRNESS = Gauge(
    "eval_suite_fairness",
    "Fairness score from evaluation suite",
    labelnames=["suite_name", "model_version", "metric"],
)

EVAL_SUITE_ROBUSTNESS = Gauge(
    "eval_suite_robustness",
    "Robustness score from evaluation suite",
    labelnames=["suite_name", "model_version", "perturbation_type"],
)

EVAL_SUITE_ERRORS = Counter(
    "eval_suite_errors_total",
    "Total errors in evaluation suite",
    labelnames=["suite_name", "error_type"],
)

EVAL_SUITE_DURATION = Histogram(
    "eval_suite_duration_seconds",
    "Duration of evaluation suite execution",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    labelnames=["suite_name"],
)

EVAL_SUITE_RUNS = Counter(
    "eval_suite_runs_total",
    "Total number of evaluation suite runs",
    labelnames=["suite_name", "status"],
)


class EvaluationSuite:
    def __init__(
        self,
        name: str,
        model_version: str = "unknown",
        demographic_groups: list[str] | None = None,
    ):
        self.name = name
        self.model_version = model_version
        self.demographic_groups = demographic_groups or []
        self.results: dict[str, Any] = {}

    def run(
        self,
        predictions: list[dict[str, Any]],
        ground_truth: list[dict[str, Any]],
        latencies: list[float],
        confidence_scores: list[float],
        perturbed_predictions: list[dict[str, Any]] | None = None,
        original_predictions: list[dict[str, Any]] | None = None,
        perturbation_types: list[str] | None = None,
    ) -> dict[str, Any]:
        start_time = time.time()

        try:
            accuracy_results = evaluate_accuracy(predictions, ground_truth)
            self._record_accuracy(accuracy_results)

            latency_results = evaluate_latency(latencies)
            self._record_latency(latency_results)

            confidence_results = evaluate_confidence(confidence_scores)
            self._record_confidence(confidence_results)

            if self.demographic_groups:
                fairness_results = evaluate_fairness(predictions, ground_truth, self.demographic_groups)
                self._record_fairness(fairness_results)

            if perturbed_predictions and original_predictions and perturbation_types:
                robustness_results = evaluate_robustness(
                    perturbed_predictions,
                    original_predictions,
                    perturbation_types,
                )
                self._record_robustness(robustness_results)

            self.results = {
                "accuracy": accuracy_results,
                "latency": latency_results,
                "confidence": confidence_results,
                "fairness": fairness_results if self.demographic_groups else None,
                "robustness": robustness_results if perturbed_predictions else None,
            }

            duration = time.time() - start_time
            EVAL_SUITE_DURATION.labels(suite_name=self.name).observe(duration)
            EVAL_SUITE_RUNS.labels(suite_name=self.name, status="success").inc()

            return self.results

        except Exception as e:
            EVAL_SUITE_ERRORS.labels(suite_name=self.name, error_type=type(e).__name__).inc()
            EVAL_SUITE_RUNS.labels(suite_name=self.name, status="error").inc()
            raise

    def _record_accuracy(self, results: dict[str, float]) -> None:
        EVAL_SUITE_ACCURACY.labels(
            suite_name=self.name,
            model_version=self.model_version,
        ).set(results.get("accuracy", 0.0))

    def _record_latency(self, results: dict[str, float]) -> None:
        EVAL_SUITE_LATENCY_P50.labels(
            suite_name=self.name,
            model_version=self.model_version,
        ).set(results.get("p50", 0.0))
        EVAL_SUITE_LATENCY_P95.labels(
            suite_name=self.name,
            model_version=self.model_version,
        ).set(results.get("p95", 0.0))
        EVAL_SUITE_LATENCY_P99.labels(
            suite_name=self.name,
            model_version=self.model_version,
        ).set(results.get("p99", 0.0))

    def _record_confidence(self, results: dict[str, float]) -> None:
        EVAL_SUITE_CONFIDENCE.labels(
            suite_name=self.name,
            model_version=self.model_version,
        ).set(results.get("mean_confidence", 0.0))

    def _record_fairness(self, results: dict[str, float]) -> None:
        for key, value in results.items():
            EVAL_SUITE_FAIRNESS.labels(
                suite_name=self.name,
                model_version=self.model_version,
                metric=key,
            ).set(value)

    def _record_robustness(self, results: dict[str, float]) -> None:
        for key, value in results.items():
            EVAL_SUITE_ROBUSTNESS.labels(
                suite_name=self.name,
                model_version=self.model_version,
                perturbation_type=key,
            ).set(value)

    def to_json(self) -> str:
        return json.dumps(self.results, indent=2)


def run_face_ml_evaluation(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    latencies: list[float],
    confidence_scores: list[float],
    model_version: str = "unknown",
) -> dict[str, Any]:
    suite = EvaluationSuite(
        name="face_ml",
        model_version=model_version,
        demographic_groups=["gender", "ethnicity", "age_group"],
    )
    return suite.run(
        predictions=predictions,
        ground_truth=ground_truth,
        latencies=latencies,
        confidence_scores=confidence_scores,
    )


def run_zero_trust_evaluation(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    latencies: list[float],
    confidence_scores: list[float],
    model_version: str = "unknown",
) -> dict[str, Any]:
    suite = EvaluationSuite(
        name="zero_trust",
        model_version=model_version,
        demographic_groups=["department", "role", "location"],
    )
    return suite.run(
        predictions=predictions,
        ground_truth=ground_truth,
        latencies=latencies,
        confidence_scores=confidence_scores,
    )


def run_quantum_evaluation(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    latencies: list[float],
    confidence_scores: list[float],
    model_version: str = "unknown",
) -> dict[str, Any]:
    suite = EvaluationSuite(
        name="quantum_ml",
        model_version=model_version,
    )
    return suite.run(
        predictions=predictions,
        ground_truth=ground_truth,
        latencies=latencies,
        confidence_scores=confidence_scores,
    )
