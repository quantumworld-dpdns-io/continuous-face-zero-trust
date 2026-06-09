from __future__ import annotations

import functools
import time
from typing import Any, Callable

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor


def init_tracer_provider(service_name: str, endpoint: str = "localhost:4317") -> TracerProvider:
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "production",
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def trace_phoenix(
    name: str | None = None,
    tags: dict[str, str] | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = name or f"phoenix.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer("cfzt-phoenix")
            with tracer.start_as_current_span(
                op_name,
                attributes={
                    **(attributes or {}),
                    **(tags or {}),
                    "function.name": func.__name__,
                    "function.module": func.__module__,
                },
            ) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


def trace_auth_phoenix(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    return trace_phoenix(
        name=name or "auth_phoenix",
        tags={(tags or {}) | {"component": "authentication", "category": "zero-trust"}},
    )


def trace_face_phoenix(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    return trace_phoenix(
        name=name or "face_phoenix",
        tags={(tags or {}) | {"component": "face-ml", "category": "biometric"}},
    )


def trace_zero_trust_phoenix(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    return trace_phoenix(
        name=name or "zk_phoenix",
        tags={(tags or {}) | {"component": "zero-trust", "category": "policy"}},
    )


def trace_quantum_phoenix(
    name: str | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    return trace_phoenix(
        name=name or "quantum_phoenix",
        tags={(tags or {}) | {"component": "quantum", "category": "ml"}},
    )


def log_span_event(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> None:
    tracer = get_tracer("cfzt-phoenix")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)


def set_span_status(
    status: str,
    description: str = "",
) -> None:
    current_span = trace.get_current_span()
    if status == "error":
        current_span.set_status(trace.StatusCode.ERROR, description)
    elif status == "ok":
        current_span.set_status(trace.StatusCode.OK, description)
    else:
        current_span.set_status(trace.StatusCode.UNSET, description)


def add_span_event(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> None:
    current_span = trace.get_current_span()
    current_span.add_event(name, attributes=attributes or {})


def record_exception(exception: Exception) -> None:
    current_span = trace.get_current_span()
    current_span.record_exception(exception)


def set_span_attribute(key: str, value: Any) -> None:
    current_span = trace.get_current_span()
    current_span.set_attribute(key, value)
