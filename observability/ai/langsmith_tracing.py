from __future__ import annotations

import functools
import time
from typing import Any, Callable

from langsmith.run_helpers import trace as langsmith_trace
from langsmith import Client


def trace_langsmith(
    name: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    project_name: str | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"langsmith.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                with langsmith_trace(
                    name=op_name,
                    tags=tags or [],
                    metadata=metadata or {},
                    project_name=project_name,
                ) as trace_result:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    trace_result.on_end(
                        outputs={"result": result},
                        metadata={
                            "duration_seconds": duration,
                            "status": "success",
                        },
                    )
                    return result
            except Exception as e:
                duration = time.time() - start_time
                trace_result.on_end(
                    error=str(e),
                    metadata={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        return wrapper
    return decorator


def trace_auth_langsmith(
    name: str | None = None,
    tags: list[str] | None = None,
) -> Callable:
    return trace_langsmith(
        name=name or "auth_langsmith",
        tags=(tags or []) + ["auth", "zero-trust"],
        metadata={"component": "authentication"},
    )


def trace_face_langsmith(
    name: str | None = None,
    tags: list[str] | None = None,
) -> Callable:
    return trace_langsmith(
        name=name or "face_langsmith",
        tags=(tags or []) + ["face-ml", "biometric"],
        metadata={"component": "face-recognition"},
    )


def trace_zero_trust_langsmith(
    name: str | None = None,
    tags: list[str] | None = None,
) -> Callable:
    return trace_langsmith(
        name=name or "zk_langsmith",
        tags=(tags or []) + ["zero-trust", "policy"],
        metadata={"component": "zero-trust-engine"},
    )


def trace_quantum_langsmith(
    name: str | None = None,
    tags: list[str] | None = None,
) -> Callable:
    return trace_langsmith(
        name=name or "quantum_langsmith",
        tags=(tags or []) + ["quantum", "ml"],
        metadata={"component": "quantum-computing"},
    )


def log_llm_call(
    model_name: str,
    prompt: str,
    completion: str,
    tokens_used: int,
    latency_ms: float,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    client = Client()
    run = client.create_run(
        name="llm_call",
        run_type="llm",
        inputs={"prompt": prompt},
        outputs={"completion": completion},
        tags=tags or [],
        extra={
            "model_name": model_name,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
        },
    )
    return {
        "run_id": str(run.id),
        "model_name": model_name,
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
    }


def log_tool_call(
    tool_name: str,
    tool_input: Any,
    tool_output: Any,
    latency_ms: float,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    client = Client()
    run = client.create_run(
        name=f"tool_{tool_name}",
        run_type="tool",
        inputs={"input": tool_input},
        outputs={"output": tool_output},
        tags=tags or [],
        extra={"latency_ms": latency_ms},
    )
    return {
        "run_id": str(run.id),
        "tool_name": tool_name,
        "latency_ms": latency_ms,
    }


def create_feedback(
    run_id: str,
    key: str,
    value: Any,
    comment: str = "",
    source: str = "user",
) -> dict[str, Any]:
    client = Client()
    feedback = client.create_feedback(
        run_id=run_id,
        key=key,
        value=value,
        comment=comment,
        source=source,
    )
    return {
        "feedback_id": str(feedback.id),
        "run_id": run_id,
        "key": key,
        "value": value,
    }


def get_run_metrics(
    project_name: str | None = None,
    run_type: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    client = Client()
    runs = list(client.list_runs(
        project_name=project_name,
        run_type=run_type,
        limit=limit,
    ))

    total_tokens = sum(r.total_tokens or 0 for r in runs)
    total_cost = sum(r.total_cost or 0 for r in runs)
    avg_latency = sum(r.latency_ms or 0 for r in runs) / len(runs) if runs else 0

    return {
        "total_runs": len(runs),
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "average_latency_ms": avg_latency,
        "error_rate": sum(1 for r in runs if r.error) / len(runs) if runs else 0,
    }
