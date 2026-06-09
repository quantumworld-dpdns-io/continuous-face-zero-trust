from __future__ import annotations

import os
from typing import Any

import weave


WEAVE_PROJECT = os.environ.get("WEAVE_PROJECT", "cfzt-continuous-face-zero-trust")
WEAVE_ENTITY = os.environ.get("WEAVE_ENTITY", "cfzt-team")
WEAVE_HOST = os.environ.get("WEAVE_HOST", "https://trace.wandb.ai")


def init_weave(project_name: str | None = None) -> None:
    project = project_name or WEAVE_PROJECT
    weave.init(
        project=project,
        entity=WEAVE_ENTITY,
        host=WEAVE_HOST,
        settings=weave.Settings(
            should_capture_code=True,
            capture_system_prompt=True,
        ),
    )


def get_weave_client() -> weave.Client:
    return weave.init(project=WEAVE_PROJECT, entity=WEAVE_ENTITY)


def log_model_config(config: dict[str, Any], name: str = "face-ml-config") -> None:
    weave.log(
        name=name,
        data=config,
    )


def log_dataset(
    name: str,
    data: list[dict[str, Any]],
    description: str = "",
) -> None:
    weave.log_dataset(
        name=name,
        data=data,
        description=description,
    )


def create_evaluation(
    name: str,
    dataset: list[dict[str, Any]],
    scorers: list[callable],
    model: callable,
    experiment_name: str | None = None,
) -> Any:
    evaluation = weave.Evaluation(
        name=name,
        dataset=dataset,
        scorers=scorers,
        experiment_name=experiment_name,
    )
    return evaluation


class WeaveCallback:
    def __init__(self, project_name: str | None = None):
        self.project = project_name or WEAVE_PROJECT
        self.client = None

    def __enter__(self) -> "WeaveCallback":
        init_weave(self.project)
        self.client = get_weave_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


def create_op_metadata(
    op_name: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "op_name": op_name,
        "inputs": inputs,
        "outputs": outputs,
    }
    if metadata:
        result["metadata"] = metadata
    return result
