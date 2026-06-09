from __future__ import annotations

import os
from typing import Any

import phoenix as px


PHOENIX_HOST = os.environ.get("PHOENIX_HOST", "0.0.0.0")
PHOENIX_PORT = int(os.environ.get("PHOENIX_PORT", "6006"))
PHOENIX_PROJECT_NAME = os.environ.get("PHOENIX_PROJECT_NAME", "cfzt-continuous-face-zero-trust")
PHOENIX_COLLECTOR_ENDPOINT = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
PHOENIX_API_KEY = os.environ.get("PHOENIX_API_KEY", "")
PHOENIX_ENABLED = os.environ.get("PHOENIX_ENABLED", "true").lower() == "true"


def init_phoenix(
    host: str | None = None,
    port: int | None = None,
    project_name: str | None = None,
) -> px.Client:
    return px.Client(
        host=host or PHOENIX_HOST,
        port=port or PHOENIX_PORT,
        project_name=project_name or PHOENIX_PROJECT_NAME,
    )


def get_phoenix_client() -> px.Client:
    return px.Client(
        host=PHOENIX_HOST,
        port=PHOENIX_PORT,
        project_name=PHOENIX_PROJECT_NAME,
    )


def create_project(
    project_name: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    client = get_phoenix_client()
    project = client.create_project(
        project_name=project_name or PHOENIX_PROJECT_NAME,
        description=description,
    )
    return {
        "id": project.id,
        "name": project.name,
        "description": description,
    }


def log_trace(
    name: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    client = get_phoenix_client()
    trace = client.log_traces(
        project_name=project_name or PHOENIX_PROJECT_NAME,
        traces=[{
            "name": name,
            "inputs": inputs,
            "outputs": outputs,
            "metadata": metadata or {},
        }],
    )
    return {
        "trace_id": str(trace.id) if trace else None,
        "name": name,
    }


def log_evaluation(
    dataset_name: str,
    eval_name: str,
    results: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    client = get_phoenix_client()
    evaluation = client.log_evaluations(
        project_name=project_name or PHOENIX_PROJECT_NAME,
        dataset_name=dataset_name,
        eval_name=eval_name,
        results=results,
        metadata=metadata or {},
    )
    return {
        "evaluation_id": str(evaluation.id) if evaluation else None,
        "dataset_name": dataset_name,
        "eval_name": eval_name,
    }


def get_traces(
    project_name: str | None = None,
    limit: int = 100,
    filter_dict: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    client = get_phoenix_client()
    traces = client.get_traces(
        project_name=project_name or PHOENIX_PROJECT_NAME,
        limit=limit,
        filter=filter_dict,
    )
    return [
        {
            "id": str(trace.id),
            "name": trace.name,
            "start_time": trace.start_time.isoformat() if trace.start_time else None,
            "end_time": trace.end_time.isoformat() if trace.end_time else None,
            "latency_ms": trace.latency_ms,
        }
        for trace in traces
    ]


def get_evaluations(
    dataset_name: str,
    project_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    client = get_phoenix_client()
    evaluations = client.get_evaluations(
        project_name=project_name or PHOENIX_PROJECT_NAME,
        dataset_name=dataset_name,
        limit=limit,
    )
    return [
        {
            "id": str(evaluation.id),
            "name": evaluation.name,
            "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
        }
        for evaluation in evaluations
    ]


def create_dataset_from_traces(
    dataset_name: str,
    traces: list[dict[str, Any]],
    project_name: str | None = None,
) -> dict[str, Any]:
    client = get_phoenix_client()
    dataset = client.create_dataset_from_traces(
        dataset_name=dataset_name,
        traces=traces,
        project_name=project_name or PHOENIX_PROJECT_NAME,
    )
    return {
        "id": str(dataset.id),
        "name": dataset.name,
    }


def delete_project(
    project_name: str | None = None,
) -> bool:
    client = get_phoenix_client()
    client.delete_project(project_name or PHOENIX_PROJECT_NAME)
    return True
