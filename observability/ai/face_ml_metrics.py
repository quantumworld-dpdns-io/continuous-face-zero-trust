from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Histogram, Gauge, Summary, Info


FACE_DETECTION_LATENCY = Histogram(
    "face_detection_latency_seconds",
    "Time taken for face detection",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["model_version", "image_size", "device"],
)

FACE_DETECTION_COUNTER = Counter(
    "face_detection_total",
    "Total number of face detections",
    labelnames=["status", "model_version", "device"],
)

FACE_DETECTION_CONFIDENCE = Histogram(
    "face_detection_confidence",
    "Confidence score of face detections",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    labelnames=["model_version", "device"],
)

FACE_MATCH_LATENCY = Histogram(
    "face_match_latency_seconds",
    "Time taken for face matching",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["model_version", "device"],
)

FACE_MATCH_COUNTER = Counter(
    "face_match_total",
    "Total number of face match attempts",
    labelnames=["status", "model_version", "device"],
)

FACE_MATCH_CONFIDENCE = Histogram(
    "face_match_confidence",
    "Confidence score of face matches",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    labelnames=["model_version", "device"],
)

FACE_LIVENESS_LATENCY = Histogram(
    "face_liveness_latency_seconds",
    "Time taken for liveness detection",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["model_version", "device"],
)

FACE_LIVENESS_COUNTER = Counter(
    "face_liveness_total",
    "Total number of liveness checks",
    labelnames=["status", "model_version", "device"],
)

FACE_LIVENESS_SCORE = Gauge(
    "face_liveness_score",
    "Liveness score (0.0 to 1.0)",
    labelnames=["model_version", "device"],
)

FACE_EMBEDDING_LATENCY = Histogram(
    "face_embedding_latency_seconds",
    "Time taken to generate face embeddings",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["model_version", "device"],
)

FACE_EMBEDDING_DIMENSIONS = Gauge(
    "face_embedding_dimensions",
    "Dimensions of generated embeddings",
    labelnames=["model_version"],
)

FACE_API_REQUESTS = Counter(
    "face_api_requests_total",
    "Total number of face API requests",
    labelnames=["endpoint", "method", "status_code"],
)

FACE_API_LATENCY = Histogram(
    "face_api_latency_seconds",
    "Face API request latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["endpoint", "method"],
)

FACE_ACTIVE_SESSIONS = Gauge(
    "face_active_sessions",
    "Number of active face recognition sessions",
)

FACE_MODEL_VERSION = Info(
    "face_model_version",
    "Current face ML model version",
)

FACE_GPU_MEMORY = Gauge(
    "face_gpu_memory_bytes",
    "GPU memory used by face ML model",
    labelnames=["device"],
)

FACE_GPU_UTILIZATION = Gauge(
    "face_gpu_utilization_percent",
    "GPU utilization for face ML operations",
    labelnames=["device"],
)

FACE_BATCH_SIZE = Histogram(
    "face_batch_size",
    "Batch sizes for face processing",
    buckets=[1, 2, 4, 8, 16, 32, 64, 128],
    labelnames=["model_version"],
)

FACE_FALSE_POSITIVE_RATE = Gauge(
    "face_false_positive_rate",
    "False positive rate for face matching",
    labelnames=["model_version", "threshold"],
)

FACE_FALSE_NEGATIVE_RATE = Gauge(
    "face_false_negative_rate",
    "False negative rate for face matching",
    labelnames=["model_version", "threshold"],
)

FACE_TEMPLATE_SIZE = Gauge(
    "face_template_size_bytes",
    "Size of face templates in bytes",
    labelnames=["model_version"],
)


def record_detection_latency(
    latency: float,
    model_version: str = "unknown",
    image_size: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_DETECTION_LATENCY.labels(
        model_version=model_version,
        image_size=image_size,
        device=device,
    ).observe(latency)


def record_detection(status: str, model_version: str = "unknown", device: str = "cpu") -> None:
    FACE_DETECTION_COUNTER.labels(
        status=status,
        model_version=model_version,
        device=device,
    ).inc()


def record_detection_confidence(
    confidence: float,
    model_version: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_DETECTION_CONFIDENCE.labels(
        model_version=model_version,
        device=device,
    ).observe(confidence)


def record_match_latency(
    latency: float,
    model_version: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_MATCH_LATENCY.labels(
        model_version=model_version,
        device=device,
    ).observe(latency)


def record_match(status: str, model_version: str = "unknown", device: str = "cpu") -> None:
    FACE_MATCH_COUNTER.labels(
        status=status,
        model_version=model_version,
        device=device,
    ).inc()


def record_match_confidence(
    confidence: float,
    model_version: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_MATCH_CONFIDENCE.labels(
        model_version=model_version,
        device=device,
    ).observe(confidence)


def record_liveness_latency(
    latency: float,
    model_version: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_LIVENESS_LATENCY.labels(
        model_version=model_version,
        device=device,
    ).observe(latency)


def record_liveness(status: str, model_version: str = "unknown", device: str = "cpu") -> None:
    FACE_LIVENESS_COUNTER.labels(
        status=status,
        model_version=model_version,
        device=device,
    ).inc()


def record_liveness_score(
    score: float,
    model_version: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_LIVENESS_SCORE.labels(
        model_version=model_version,
        device=device,
    ).set(score)


def record_embedding_latency(
    latency: float,
    model_version: str = "unknown",
    device: str = "cpu",
) -> None:
    FACE_EMBEDDING_LATENCY.labels(
        model_version=model_version,
        device=device,
    ).observe(latency)


def record_embedding_dimensions(
    dimensions: int,
    model_version: str = "unknown",
) -> None:
    FACE_EMBEDDING_DIMENSIONS.labels(
        model_version=model_version,
    ).set(dimensions)


def record_api_request(
    endpoint: str,
    method: str,
    status_code: int,
) -> None:
    FACE_API_REQUESTS.labels(
        endpoint=endpoint,
        method=method,
        status_code=str(status_code),
    ).inc()


def record_api_latency(
    endpoint: str,
    method: str,
    latency: float,
) -> None:
    FACE_API_LATENCY.labels(
        endpoint=endpoint,
        method=method,
    ).observe(latency)


def set_active_sessions(count: int) -> None:
    FACE_ACTIVE_SESSIONS.set(count)


def set_model_version(version: str) -> None:
    FACE_MODEL_VERSION.info({"version": version})


def record_gpu_memory(bytes_used: int, device: str = "cuda:0") -> None:
    FACE_GPU_MEMORY.labels(device=device).set(bytes_used)


def record_gpu_utilization(percent: float, device: str = "cuda:0") -> None:
    FACE_GPU_UTILIZATION.labels(device=device).set(percent)


def record_batch_size(batch_size: int, model_version: str = "unknown") -> None:
    FACE_BATCH_SIZE.labels(model_version=model_version).observe(batch_size)


def record_error_rates(
    fpr: float,
    fnr: float,
    model_version: str = "unknown",
    threshold: float = 0.8,
) -> None:
    FACE_FALSE_POSITIVE_RATE.labels(
        model_version=model_version,
        threshold=str(threshold),
    ).set(fpr)
    FACE_FALSE_NEGATIVE_RATE.labels(
        model_version=model_version,
        threshold=str(threshold),
    ).set(fnr)


def record_template_size(
    size_bytes: int,
    model_version: str = "unknown",
) -> None:
    FACE_TEMPLATE_SIZE.labels(model_version=model_version).set(size_bytes)
