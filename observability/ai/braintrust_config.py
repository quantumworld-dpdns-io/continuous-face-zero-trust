from __future__ import annotations

import os
from typing import Any

import braintrust


BRAINFUST_API_KEY = os.environ.get("BRAINFUST_API_KEY", "")
BRAINFUST_PROJECT = os.environ.get("BRAINFUST_PROJECT", "cfzt-continuous-face-zero-trust")
BRAINFUST_ENVIRONMENT = os.environ.get("CFZT_ENVIRONMENT", "development")


def init_braintrust(project_name: str | None = None) -> braintrust.init:
    project = project_name or BRAINFUST_PROJECT
    return braintrust.init(
        project=project,
        api_key=BRAINFUST_API_KEY,
        metadata={
            "environment": BRAINFUST_ENVIRONMENT,
            "service": "continuous-face-zero-trust",
        },
    )


def get_braintrust_logger(project_name: str | None = None) -> Any:
    project = project_name or BRAINFUST_PROJECT
    return braintrust.init(
        project=project,
        api_key=BRAINFUST_API_KEY,
    )


def create_dataset(
    name: str,
    description: str = "",
    data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    logger = get_braintrust_logger()
    dataset = logger.create_dataset(
        name=name,
        description=description,
    )
    if data:
        for item in data:
            dataset.insert(item)
    return {
        "id": dataset.id,
        "name": name,
        "description": description,
    }


def log_experiment(
    name: str,
    dataset: list[dict[str, Any]],
    eval_fn: callable,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger = get_braintrust_logger()
    experiment = logger.start_experiment(
        name=name,
        dataset=dataset,
        eval_fn=eval_fn,
        metadata=metadata or {},
    )
    return {
        "experiment_id": experiment.id,
        "name": name,
    }


def score_accuracy(
    expected: dict[str, Any],
    actual: dict[str, Any],
    threshold: float = 0.8,
) -> float:
    expected_value = expected.get("value", 0.0)
    actual_value = actual.get("value", 0.0)
    if abs(expected_value - actual_value) < threshold:
        return 1.0
    return 0.0


def score_f1(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> float:
    expected_labels = set(expected.get("labels", []))
    actual_labels = set(actual.get("labels", []))

    if not expected_labels or not actual_labels:
        return 0.0

    true_positives = len(expected_labels & actual_labels)
    false_positives = len(actual_labels - expected_labels)
    false_negatives = len(expected_labels - actual_labels)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0

    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def score_latency(
    expected: dict[str, Any],
    actual: dict[str, Any],
    max_latency_ms: float = 1000.0,
) -> float:
    latency = actual.get("latency_ms", 0.0)
    if latency <= max_latency_ms:
        return 1.0
    return max(0.0, 1.0 - (latency - max_latency_ms) / max_latency_ms)


def score_confidence(
    expected: dict[str, Any],
    actual: dict[str, Any],
    threshold: float = 0.8,
) -> float:
    confidence = actual.get("confidence", 0.0)
    if confidence >= threshold:
        return 1.0
    return confidence / threshold


def run_experiment(
    name: str,
    dataset: list[dict[str, Any]],
    target_fn: callable,
    scorers: list[callable] | None = None,
) -> dict[str, Any]:
    logger = get_braintrust_logger()
    experiment = logger.start_experiment(
        name=name,
        dataset=dataset,
    )

    for item in dataset:
        result = target_fn(item["input"])
        scores = {}
        if scorers:
            for scorer in scorers:
                scores[scorer.__name__] = scorer(item.get("expected", {}), result)
        experiment.log(input=item["input"], output=result, scores=scores)

    return {
        "experiment_id": experiment.id,
        "name": name,
        "status": "completed",
    }


def list_experiments(
    limit: int = 100,
) -> list[dict[str, Any]]:
    logger = get_braintrust_logger()
    experiments = list(logger.list_experiments(limit=limit))
    return [
        {
            "id": exp.id,
            "name": exp.name,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
        }
        for exp in experiments
    ]


def get_experiment_scores(
    experiment_id: str,
) -> dict[str, Any]:
    logger = get_braintrust_logger()
    experiment = logger.get_experiment(experiment_id)
    return {
        "id": experiment.id,
        "name": experiment.name,
        "scores": experiment.scores if hasattr(experiment, 'scores') else {},
    }
