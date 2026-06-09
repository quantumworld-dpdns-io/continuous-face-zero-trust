from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Histogram, Gauge, Summary, Info


QUANTUM_CIRCUIT_DEPTH = Gauge(
    "quantum_circuit_depth",
    "Depth of quantum circuit",
    labelnames=["circuit_name", "backend"],
)

QUANTUM_QUBIT_COUNT = Gauge(
    "quantum_qubit_count",
    "Number of qubits used in circuit",
    labelnames=["circuit_name", "backend"],
)

QUANTUM_FIDELITY = Gauge(
    "quantum_fidelity",
    "Fidelity of quantum circuit execution",
    labelnames=["circuit_name", "backend"],
)

QUANTUM_EXECUTION_LATENCY = Histogram(
    "quantum_execution_latency_seconds",
    "Time taken for quantum circuit execution",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    labelnames=["backend", "optimization_level"],
)

QUANTUM_SHOT_COUNT = Counter(
    "quantum_shots_total",
    "Total number of quantum shots",
    labelnames=["circuit_name", "backend"],
)

QUANTUM_CIRCUIT_FAILURES = Counter(
    "quantum_circuit_failures_total",
    "Total number of quantum circuit failures",
    labelnames=["circuit_name", "backend", "error_type"],
)

QUANTUM_CIRCUIT_SUCCESS = Counter(
    "quantum_circuit_success_total",
    "Total number of successful quantum circuit executions",
    labelnames=["circuit_name", "backend"],
)

QUANTUM_GATE_COUNT = Gauge(
    "quantum_gate_count",
    "Number of gates in quantum circuit",
    labelnames=["circuit_name", "gate_type"],
)

QUANTUM_NOISE_LEVEL = Gauge(
    "quantum_noise_level",
    "Estimated noise level in quantum system",
    labelnames=["backend", "noise_model"],
)

QUANTUM_OPTIMIZATION_LEVEL = Gauge(
    "quantum_optimization_level",
    "Current optimization level for quantum circuits",
    labelnames=["backend"],
)

QUANTUM_HYBRID_STEP_LATENCY = Histogram(
    "quantum_hybrid_step_latency_seconds",
    "Latency of hybrid quantum-classical steps",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["step_name", "backend"],
)

QUANTUM_RESULT_ACCURACY = Gauge(
    "quantum_result_accuracy",
    "Accuracy of quantum computation results",
    labelnames=["circuit_name", "backend"],
)

QUANTUM_RESOURCES_USED = Gauge(
    "quantum_resources_used",
    "Quantum compute resources consumed",
    labelnames=["resource_type", "backend"],
)

QUANTUM_API_REQUESTS = Counter(
    "quantum_api_requests_total",
    "Total number of quantum API requests",
    labelnames=["endpoint", "method", "status_code"],
)

QUANTUM_API_LATENCY = Histogram(
    "quantum_api_latency_seconds",
    "Quantum API request latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labelnames=["endpoint", "method"],
)

QUANTUM_ACTIVE_CIRCUITS = Gauge(
    "quantum_active_circuits",
    "Number of active quantum circuits being processed",
)

QUANTUM_QUEUE_DEPTH = Gauge(
    "quantum_queue_depth",
    "Depth of quantum job queue",
    labelnames=["backend"],
)

QUANTUM_BACKEND_STATUS = Gauge(
    "quantum_backend_status",
    "Status of quantum backend (1=online, 0=offline)",
    labelnames=["backend"],
)

QUANTUM_MODEL_VERSION = Info(
    "quantum_model_version",
    "Current quantum ML model version",
)

QUANTUM_CIRCUIT_OPTIMIZATION = Counter(
    "quantum_circuit_optimization_total",
    "Total number of circuit optimizations performed",
    labelnames=["optimization_type", "backend"],
)

QUANTUM_ERROR_MITIGATION = Counter(
    "quantum_error_mitigation_total",
    "Total number of error mitigation applications",
    labelnames=["mitigation_type", "backend"],
)


def record_circuit_depth(
    depth: int,
    circuit_name: str = "unknown",
    backend: str = "unknown",
) -> None:
    QUANTUM_CIRCUIT_DEPTH.labels(
        circuit_name=circuit_name,
        backend=backend,
    ).set(depth)


def record_qubit_count(
    count: int,
    circuit_name: str = "unknown",
    backend: str = "unknown",
) -> None:
    QUANTUM_QUBIT_COUNT.labels(
        circuit_name=circuit_name,
        backend=backend,
    ).set(count)


def record_fidelity(
    fidelity: float,
    circuit_name: str = "unknown",
    backend: str = "unknown",
) -> None:
    QUANTUM_FIDELITY.labels(
        circuit_name=circuit_name,
        backend=backend,
    ).set(fidelity)


def record_execution_latency(
    latency: float,
    backend: str = "unknown",
    optimization_level: int = 0,
) -> None:
    QUANTUM_EXECUTION_LATENCY.labels(
        backend=backend,
        optimization_level=str(optimization_level),
    ).observe(latency)


def record_shot_count(
    shots: int,
    circuit_name: str = "unknown",
    backend: str = "unknown",
) -> None:
    QUANTUM_SHOT_COUNT.labels(
        circuit_name=circuit_name,
        backend=backend,
    ).inc(shots)


def record_circuit_failure(
    circuit_name: str,
    backend: str,
    error_type: str,
) -> None:
    QUANTUM_CIRCUIT_FAILURES.labels(
        circuit_name=circuit_name,
        backend=backend,
        error_type=error_type,
    ).inc()


def record_circuit_success(
    circuit_name: str,
    backend: str,
) -> None:
    QUANTUM_CIRCUIT_SUCCESS.labels(
        circuit_name=circuit_name,
        backend=backend,
    ).inc()


def record_gate_count(
    count: int,
    circuit_name: str,
    gate_type: str = "total",
) -> None:
    QUANTUM_GATE_COUNT.labels(
        circuit_name=circuit_name,
        gate_type=gate_type,
    ).set(count)


def record_noise_level(
    level: float,
    backend: str = "unknown",
    noise_model: str = "depolarizing",
) -> None:
    QUANTUM_NOISE_LEVEL.labels(
        backend=backend,
        noise_model=noise_model,
    ).set(level)


def record_optimization_level(
    level: int,
    backend: str = "unknown",
) -> None:
    QUANTUM_OPTIMIZATION_LEVEL.labels(backend=backend).set(level)


def record_hybrid_step_latency(
    latency: float,
    step_name: str,
    backend: str = "unknown",
) -> None:
    QUANTUM_HYBRID_STEP_LATENCY.labels(
        step_name=step_name,
        backend=backend,
    ).observe(latency)


def record_result_accuracy(
    accuracy: float,
    circuit_name: str = "unknown",
    backend: str = "unknown",
) -> None:
    QUANTUM_RESULT_ACCURACY.labels(
        circuit_name=circuit_name,
        backend=backend,
    ).set(accuracy)


def record_resources_used(
    amount: float,
    resource_type: str,
    backend: str = "unknown",
) -> None:
    QUANTUM_RESOURCES_USED.labels(
        resource_type=resource_type,
        backend=backend,
    ).set(amount)


def record_api_request(
    endpoint: str,
    method: str,
    status_code: int,
) -> None:
    QUANTUM_API_REQUESTS.labels(
        endpoint=endpoint,
        method=method,
        status_code=str(status_code),
    ).inc()


def record_api_latency(
    endpoint: str,
    method: str,
    latency: float,
) -> None:
    QUANTUM_API_LATENCY.labels(
        endpoint=endpoint,
        method=method,
    ).observe(latency)


def set_active_circuits(count: int) -> None:
    QUANTUM_ACTIVE_CIRCUITS.set(count)


def set_queue_depth(depth: int, backend: str = "unknown") -> None:
    QUANTUM_QUEUE_DEPTH.labels(backend=backend).set(depth)


def set_backend_status(status: int, backend: str = "unknown") -> None:
    QUANTUM_BACKEND_STATUS.labels(backend=backend).set(status)


def set_model_version(version: str) -> None:
    QUANTUM_MODEL_VERSION.info({"version": version})


def record_circuit_optimization(
    optimization_type: str,
    backend: str = "unknown",
) -> None:
    QUANTUM_CIRCUIT_OPTIMIZATION.labels(
        optimization_type=optimization_type,
        backend=backend,
    ).inc()


def record_error_mitigation(
    mitigation_type: str,
    backend: str = "unknown",
) -> None:
    QUANTUM_ERROR_MITIGATION.labels(
        mitigation_type=mitigation_type,
        backend=backend,
    ).inc()
