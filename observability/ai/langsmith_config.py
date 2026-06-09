from __future__ import annotations

import os
from typing import Any

from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.run_helpers import trace


LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "cfzt-continuous-face-zero-trust")
LANGCHAIN_ENDPOINT = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_TRACING = os.environ.get("LANGCHAIN_TRACING", "true") == "true"


def init_langsmith() -> Client:
    return Client(
        api_key=LANGCHAIN_API_KEY,
        api_url=LANGCHAIN_ENDPOINT,
    )


def get_langsmith_client() -> Client:
    return Client(
        api_key=LANGCHAIN_API_KEY,
        api_url=LANGCHAIN_ENDPOINT,
    )


def create_project(
    project_name: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    client = get_langsmith_client()
    project = client.create_project(
        project_name=project_name or LANGCHAIN_PROJECT,
        description=description,
        tags=["cfzt", "face-ml", "zero-trust"],
    )
    return {
        "id": project.id,
        "name": project.name,
        "description": description,
    }


def log_feedback(
    run_id: str,
    key: str,
    value: Any,
    comment: str = "",
) -> None:
    client = get_langsmith_client()
    client.create_feedback(
        run_id=run_id,
        key=key,
        value=value,
        comment=comment,
    )


def create_dataset(
    dataset_name: str,
    description: str = "",
) -> dict[str, Any]:
    client = get_langsmith_client()
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description=description,
    )
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": description,
    }


def create_example(
    dataset_id: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    client = get_langsmith_client()
    example = client.create_example(
        dataset_id=dataset_id,
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
    )
    return {
        "id": example.id,
        "dataset_id": dataset_id,
    }


def run_evaluation(
    dataset_name: str,
    target_fn: callable,
    evaluators: list[callable],
    experiment_prefix: str | None = None,
) -> dict[str, Any]:
    client = get_langsmith_client()
    results = evaluate(
        target=target_fn,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
        max_concurrency=4,
        metadata={
            "project": LANGCHAIN_PROJECT,
            "environment": os.environ.get("CFZT_ENVIRONMENT", "development"),
        },
    )
    return {
        "experiment_id": results.experiment_id,
        "results": results.results,
    }


def list_runs(
    project_name: str | None = None,
    limit: int = 100,
    filter_dict: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    client = get_langsmith_client()
    runs = list(client.list_runs(
        project_name=project_name or LANGCHAIN_PROJECT,
        limit=limit,
        filter=filter_dict,
    ))
    return [
        {
            "id": run.id,
            "name": run.name,
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "latency_ms": run.latency_ms,
            "total_tokens": run.total_tokens,
            "total_cost": run.total_cost,
        }
        for run in runs
    ]
