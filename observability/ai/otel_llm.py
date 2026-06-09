from __future__ import annotations

import functools
import time
from typing import Any, Callable

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes


def init_otel_llm_tracer(
    service_name: str = "cfzt-llm-service",
    endpoint: str = "localhost:4317",
) -> TracerProvider:
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "production",
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider


def get_llm_tracer(name: str = "cfzt-llm") -> trace.Tracer:
    return trace.get_tracer(name)


def trace_llm_completion(
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = f"llm.completion.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_llm_tracer()
            with tracer.start_as_current_span(
                op_name,
                attributes={
                    "llm.model_name": model_name or kwargs.get("model", "unknown"),
                    "llm.temperature": temperature or kwargs.get("temperature", 0.7),
                    "llm.max_tokens": max_tokens or kwargs.get("max_tokens", 2048),
                    SpanAttributes.LLM_REQUEST_TYPE: "completion",
                    **(tags or {}),
                },
            ) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("status", "success")

                    if isinstance(result, dict):
                        span.set_attribute("llm.usage.input_tokens", result.get("input_tokens", 0))
                        span.set_attribute("llm.usage.output_tokens", result.get("output_tokens", 0))
                        span.set_attribute("llm.usage.total_tokens", result.get("total_tokens", 0))

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


def trace_llm_chat(
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = f"llm.chat.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_llm_tracer()
            with tracer.start_as_current_span(
                op_name,
                attributes={
                    "llm.model_name": model_name or kwargs.get("model", "unknown"),
                    "llm.temperature": temperature or kwargs.get("temperature", 0.7),
                    "llm.max_tokens": max_tokens or kwargs.get("max_tokens", 2048),
                    SpanAttributes.LLM_REQUEST_TYPE: "chat",
                    **(tags or {}),
                },
            ) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("status", "success")

                    if isinstance(result, dict):
                        span.set_attribute("llm.usage.input_tokens", result.get("input_tokens", 0))
                        span.set_attribute("llm.usage.output_tokens", result.get("output_tokens", 0))
                        span.set_attribute("llm.usage.total_tokens", result.get("total_tokens", 0))

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


def trace_llm_embedding(
    model_name: str | None = None,
    dimensions: int | None = None,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = f"llm.embedding.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_llm_tracer()
            with tracer.start_as_current_span(
                op_name,
                attributes={
                    "llm.model_name": model_name or kwargs.get("model", "unknown"),
                    "llm.embedding.dimensions": dimensions or kwargs.get("dimensions", 1536),
                    SpanAttributes.LLM_REQUEST_TYPE: "embedding",
                    **(tags or {}),
                },
            ) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_attribute("status", "success")

                    if isinstance(result, dict):
                        span.set_attribute("llm.usage.input_tokens", result.get("input_tokens", 0))

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


def trace_llm_tool_call(
    tool_name: str,
    tags: dict[str, str] | None = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        op_name = f"llm.tool.{tool_name}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_llm_tracer()
            with tracer.start_as_current_span(
                op_name,
                attributes={
                    "llm.tool.name": tool_name,
                    SpanAttributes.LLM_REQUEST_TYPE: "tool",
                    **(tags or {}),
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


def create_llm_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> trace.Span:
    tracer = get_llm_tracer()
    return tracer.start_span(
        name,
        attributes=attributes or {},
    )


def set_llm_span_attributes(
    span: trace.Span,
    model_name: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
    temperature: float = 0.7,
) -> None:
    span.set_attribute("llm.model_name", model_name)
    span.set_attribute("llm.usage.input_tokens", input_tokens)
    span.set_attribute("llm.usage.output_tokens", output_tokens)
    span.set_attribute("llm.usage.total_tokens", total_tokens)
    span.set_attribute("llm.temperature", temperature)
