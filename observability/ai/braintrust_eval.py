from __future__ import annotations

from typing import Any

import braintrust


def evaluate_accuracy_braintrust(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    threshold: float = 0.8,
) -> dict[str, float]:
    correct = 0
    total = len(predictions)

    for pred, gt in zip(predictions, ground_truth):
        pred_value = pred.get("value", 0.0)
        gt_value = gt.get("value", 0.0)
        if abs(pred_value - gt_value) < threshold:
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
    }


def evaluate_fairness_braintrust(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    demographic_groups: list[str],
) -> dict[str, float]:
    group_metrics = {}

    for group in demographic_groups:
        group_preds = [p for p in predictions if p.get("group") == group]
        group_gt = [g for g in ground_truth if g.get("group") == group]

        if group_preds and group_gt:
            correct = sum(1 for p, g in zip(group_preds, group_gt) if abs(p.get("value", 0.0) - g.get("value", 0.0)) < 0.1)
            group_metrics[f"accuracy_{group}"] = correct / len(group_preds)

    if len(group_metrics) > 1:
        accuracies = list(group_metrics.values())
        max_acc = max(accuracies)
        min_acc = min(accuracies)
        group_metrics["demographic_parity_difference"] = max_acc - min_acc
        group_metrics["equal_opportunity_difference"] = max_acc - min_acc

    return group_metrics


def evaluate_latency_braintrust(
    latencies: list[float],
    p50_threshold: float = 0.1,
    p95_threshold: float = 0.5,
    p99_threshold: float = 1.0,
) -> dict[str, float]:
    if not latencies:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "std": 0.0}

    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)

    p50 = sorted_latencies[int(n * 0.5)] if n > 0 else 0.0
    p95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0.0
    p99 = sorted_latencies[int(n * 0.99)] if n > 0 else 0.0
    mean = sum(sorted_latencies) / n
    variance = sum((x - mean) ** 2 for x in sorted_latencies) / n
    std = variance ** 0.5

    return {
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "mean": mean,
        "std": std,
        "p50_pass": p50 <= p50_threshold,
        "p95_pass": p95 <= p95_threshold,
        "p99_pass": p99 <= p99_threshold,
    }


def evaluate_confidence_braintrust(
    confidence_scores: list[float],
    threshold: float = 0.8,
) -> dict[str, float]:
    if not confidence_scores:
        return {"mean_confidence": 0.0, "below_threshold_rate": 0.0, "above_threshold_rate": 0.0}

    mean_confidence = sum(confidence_scores) / len(confidence_scores)
    below_threshold = sum(1 for c in confidence_scores if c < threshold)
    above_threshold = sum(1 for c in confidence_scores if c >= threshold)

    return {
        "mean_confidence": mean_confidence,
        "min_confidence": min(confidence_scores),
        "max_confidence": max(confidence_scores),
        "below_threshold_rate": below_threshold / len(confidence_scores),
        "above_threshold_rate": above_threshold / len(confidence_scores),
    }


def evaluate_robustness_braintrust(
    perturbed_predictions: list[dict[str, Any]],
    original_predictions: list[dict[str, Any]],
    perturbation_types: list[str],
) -> dict[str, float]:
    robustness_scores = {}

    for ptype in perturbation_types:
        perturbed = [p for p in perturbed_predictions if p.get("perturbation") == ptype]
        original = [o for o in original_predictions if o.get("original") == True]

        if perturbed and original:
            matches = sum(1 for p, o in zip(perturbed, original) if p.get("value") == o.get("value"))
            robustness_scores[f"robustness_{ptype}"] = matches / len(perturbed)

    if robustness_scores:
        robustness_scores["overall_robustness"] = sum(robustness_scores.values()) / len(robustness_scores)

    return robustness_scores


def run_evaluation_suite_braintrust(
    model_predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    latencies: list[float],
    confidence_scores: list[float],
    demographic_groups: list[str] | None = None,
) -> dict[str, Any]:
    results = {}

    accuracy_results = evaluate_accuracy_braintrust(model_predictions, ground_truth)
    results["accuracy"] = accuracy_results

    latency_results = evaluate_latency_braintrust(latencies)
    results["latency"] = latency_results

    confidence_results = evaluate_confidence_braintrust(confidence_scores)
    results["confidence"] = confidence_results

    if demographic_groups:
        fairness_results = evaluate_fairness_braintrust(model_predictions, ground_truth, demographic_groups)
        results["fairness"] = fairness_results

    overall_score = (
        accuracy_results.get("accuracy", 0.0) * 0.4 +
        latency_results.get("p95", 0.0) * 0.3 +
        confidence_results.get("mean_confidence", 0.0) * 0.3
    )
    results["overall_score"] = overall_score

    return results


def create_scorer(
    name: str,
    score_fn: callable,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "score_fn": score_fn,
        "metadata": metadata or {},
    }


def run_experiment_braintrust(
    name: str,
    dataset: list[dict[str, Any]],
    target_fn: callable,
    scorers: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from .braintrust_config import get_braintrust_logger

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
                scores[scorer["name"]] = scorer["score_fn"](item.get("expected", {}), result)
        experiment.log(input=item["input"], output=result, scores=scores)

    return {
        "experiment_id": experiment.id,
        "name": name,
        "status": "completed",
    }
