from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


EXPERIMENT_COUNTER = Counter(
    "experiment_tracker_experiments_total",
    "Total number of experiments tracked",
    labelnames=["project", "status"],
)

EXPERIMENT_DURATION = Histogram(
    "experiment_tracker_duration_seconds",
    "Duration of experiment tracking",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    labelnames=["project"],
)

EXPERIMENT_PARAMS = Gauge(
    "experiment_tracker_params",
    "Experiment parameters",
    labelnames=["experiment_id", "param_name"],
)

EXPERIMENT_METRICS = Gauge(
    "experiment_tracker_metrics",
    "Experiment metrics",
    labelnames=["experiment_id", "metric_name"],
)

EXPERIMENT_ARTIFACTS = Counter(
    "experiment_tracker_artifacts_total",
    "Total number of experiment artifacts",
    labelnames=["experiment_id", "artifact_type"],
)


class ExperimentTracker:
    def __init__(self, project: str = "cfzt"):
        self.project = project
        self.experiments: dict[str, dict[str, Any]] = {}

    def create_experiment(
        self,
        name: str,
        description: str = "",
        params: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        experiment_id = str(uuid.uuid4())

        self.experiments[experiment_id] = {
            "id": experiment_id,
            "name": name,
            "description": description,
            "project": self.project,
            "params": params or {},
            "tags": tags or [],
            "metrics": {},
            "artifacts": [],
            "status": "created",
            "created_at": time.time(),
            "updated_at": time.time(),
            "started_at": None,
            "completed_at": None,
        }

        EXPERIMENT_COUNTER.labels(project=self.project, status="created").inc()

        if params:
            for param_name, param_value in params.items():
                EXPERIMENT_PARAMS.labels(
                    experiment_id=experiment_id,
                    param_name=param_name,
                ).set(param_value if isinstance(param_value, (int, float)) else 0)

        return experiment_id

    def start_experiment(self, experiment_id: str) -> None:
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        self.experiments[experiment_id]["status"] = "running"
        self.experiments[experiment_id]["started_at"] = time.time()
        self.experiments[experiment_id]["updated_at"] = time.time()

    def complete_experiment(
        self,
        experiment_id: str,
        status: str = "completed",
    ) -> None:
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        self.experiments[experiment_id]["status"] = status
        self.experiments[experiment_id]["completed_at"] = time.time()
        self.experiments[experiment_id]["updated_at"] = time.time()

        duration = (
            self.experiments[experiment_id]["completed_at"] -
            self.experiments[experiment_id]["started_at"]
        ) if self.experiments[experiment_id]["started_at"] else 0

        EXPERIMENT_COUNTER.labels(project=self.project, status=status).inc()
        EXPERIMENT_DURATION.labels(project=self.project).observe(duration)

    def log_params(
        self,
        experiment_id: str,
        params: dict[str, Any],
    ) -> None:
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        self.experiments[experiment_id]["params"].update(params)
        self.experiments[experiment_id]["updated_at"] = time.time()

        for param_name, param_value in params.items():
            EXPERIMENT_PARAMS.labels(
                experiment_id=experiment_id,
                param_name=param_name,
            ).set(param_value if isinstance(param_value, (int, float)) else 0)

    def log_metrics(
        self,
        experiment_id: str,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        if step is not None:
            if "step_metrics" not in self.experiments[experiment_id]:
                self.experiments[experiment_id]["step_metrics"] = {}
            self.experiments[experiment_id]["step_metrics"][step] = metrics
        else:
            self.experiments[experiment_id]["metrics"].update(metrics)

        self.experiments[experiment_id]["updated_at"] = time.time()

        for metric_name, metric_value in metrics.items():
            EXPERIMENT_METRICS.labels(
                experiment_id=experiment_id,
                metric_name=metric_name,
            ).set(metric_value)

    def log_artifact(
        self,
        experiment_id: str,
        artifact_name: str,
        artifact_type: str,
        artifact_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        artifact_id = str(uuid.uuid4())
        artifact = {
            "id": artifact_id,
            "name": artifact_name,
            "type": artifact_type,
            "path": artifact_path,
            "metadata": metadata or {},
            "created_at": time.time(),
        }

        self.experiments[experiment_id]["artifacts"].append(artifact)
        self.experiments[experiment_id]["updated_at"] = time.time()

        EXPERIMENT_ARTIFACTS.labels(
            experiment_id=experiment_id,
            artifact_type=artifact_type,
        ).inc()

        return artifact_id

    def log_model(
        self,
        experiment_id: str,
        model_name: str,
        model_path: str,
        metrics: dict[str, float] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        artifact_id = self.log_artifact(
            experiment_id=experiment_id,
            artifact_name=model_name,
            artifact_type="model",
            artifact_path=model_path,
            metadata={
                "metrics": metrics or {},
                "params": params or {},
            },
        )

        if metrics:
            self.log_metrics(experiment_id, metrics)

        return artifact_id

    def log_dataset(
        self,
        experiment_id: str,
        dataset_name: str,
        dataset_path: str,
        version: str = "latest",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return self.log_artifact(
            experiment_id=experiment_id,
            artifact_name=dataset_name,
            artifact_type="dataset",
            artifact_path=dataset_path,
            metadata={
                "version": version,
                **(metadata or {}),
            },
        )

    def get_experiment(
        self,
        experiment_id: str,
    ) -> dict[str, Any] | None:
        return self.experiments.get(experiment_id)

    def list_experiments(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        experiments = list(self.experiments.values())

        if status:
            experiments = [e for e in experiments if e["status"] == status]

        experiments.sort(key=lambda x: x["created_at"], reverse=True)

        return experiments[:limit]

    def compare_experiments(
        self,
        experiment_ids: list[str],
    ) -> dict[str, Any]:
        comparisons = {}

        for exp_id in experiment_ids:
            exp = self.get_experiment(exp_id)
            if exp:
                comparisons[exp_id] = {
                    "name": exp["name"],
                    "params": exp["params"],
                    "metrics": exp["metrics"],
                    "status": exp["status"],
                    "duration": (
                        exp["completed_at"] - exp["started_at"]
                    ) if exp["started_at"] and exp["completed_at"] else None,
                }

        if len(experiment_ids) >= 2:
            exp1_metrics = comparisons.get(experiment_ids[0], {}).get("metrics", {})
            exp2_metrics = comparisons.get(experiment_ids[1], {}).get("metrics", {})

            common_metrics = set(exp1_metrics.keys()) & set(exp2_metrics.keys())
            metric_differences = {}

            for metric in common_metrics:
                diff = exp2_metrics[metric] - exp1_metrics[metric]
                pct_change = (diff / exp1_metrics[metric] * 100) if exp1_metrics[metric] != 0 else 0
                metric_differences[metric] = {
                    "exp1_value": exp1_metrics[metric],
                    "exp2_value": exp2_metrics[metric],
                    "absolute_diff": diff,
                    "percentage_change": pct_change,
                }

            comparisons["metric_differences"] = metric_differences

        return comparisons

    def export_experiment(
        self,
        experiment_id: str,
    ) -> str:
        exp = self.get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")

        return json.dumps(exp, indent=2, default=str)

    def export_all_experiments(self) -> str:
        return json.dumps(
            {
                "project": self.project,
                "experiments": list(self.experiments.values()),
            },
            indent=2,
            default=str,
        )
