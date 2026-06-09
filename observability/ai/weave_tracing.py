from __future__ import annotations

import functools
import time
from typing import Any, Callable

import weave


def trace_auth(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"auth.{func.__name__}"

        @weave.op(name=op_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.metrics",
                    data={
                        "duration_seconds": duration,
                        "status": "success",
                        "tags": tags or {},
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.error",
                    data={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tags": tags or {},
                    },
                )
                raise

        return wrapper
    return decorator


def trace_face_detection(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"face.detection.{func.__name__}"

        @weave.op(name=op_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.metrics",
                    data={
                        "duration_seconds": duration,
                        "status": "success",
                        "model_version": kwargs.get("model_version", "unknown"),
                        "image_size": kwargs.get("image_size", "unknown"),
                        "tags": tags or {},
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.error",
                    data={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tags": tags or {},
                    },
                )
                raise

        return wrapper
    return decorator


def trace_face_verification(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"face.verification.{func.__name__}"

        @weave.op(name=op_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.metrics",
                    data={
                        "duration_seconds": duration,
                        "status": "success",
                        "confidence": result.get("confidence", 0.0) if isinstance(result, dict) else 0.0,
                        "match": result.get("match", False) if isinstance(result, dict) else False,
                        "tags": tags or {},
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.error",
                    data={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tags": tags or {},
                    },
                )
                raise

        return wrapper
    return decorator


def trace_liveness_detection(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"face.liveness.{func.__name__}"

        @weave.op(name=op_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.metrics",
                    data={
                        "duration_seconds": duration,
                        "status": "success",
                        "liveness_score": result.get("liveness_score", 0.0) if isinstance(result, dict) else 0.0,
                        "is_live": result.get("is_live", False) if isinstance(result, dict) else False,
                        "tags": tags or {},
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.error",
                    data={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tags": tags or {},
                    },
                )
                raise

        return wrapper
    return decorator


def trace_zero_trust(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"zk.{func.__name__}"

        @weave.op(name=op_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.metrics",
                    data={
                        "duration_seconds": duration,
                        "status": "success",
                        "policy_decision": result.get("decision", "unknown") if isinstance(result, dict) else "unknown",
                        "risk_score": result.get("risk_score", 0.0) if isinstance(result, dict) else 0.0,
                        "tags": tags or {},
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.error",
                    data={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tags": tags or {},
                    },
                )
                raise

        return wrapper
    return decorator


def trace_quantum(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"quantum.{func.__name__}"

        @weave.op(name=op_name)
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.metrics",
                    data={
                        "duration_seconds": duration,
                        "status": "success",
                        "circuit_depth": kwargs.get("circuit_depth", 0),
                        "qubit_count": kwargs.get("qubit_count", 0),
                        "shot_count": kwargs.get("shot_count", 0),
                        "fidelity": result.get("fidelity", 0.0) if isinstance(result, dict) else 0.0,
                        "tags": tags or {},
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                weave.log(
                    name=f"{op_name}.error",
                    data={
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "tags": tags or {},
                    },
                )
                raise

        return wrapper
    return decorator
