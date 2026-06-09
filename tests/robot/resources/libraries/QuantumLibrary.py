"""QuantumLibrary — Robot Framework library for quantum operations."""
from __future__ import annotations

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class QuantumLibrary:
    """Robot Framework library for quantum computing operations in tests."""

    def __init__(self):
        self.backend = AerSimulator() if HAS_QISKIT else None

    def generate_random_bits_quantum(self, num_bits: int) -> list[int]:
        if not HAS_QISKIT:
            return [np.random.randint(0, 2) for _ in range(num_bits)]
        bits = []
        for _ in range(num_bits):
            qc = QuantumCircuit(1, 1)
            qc.h(0)
            qc.measure(0, 0)
            result = self.backend.run(qc, shots=1).result()
            counts = result.get_counts()
            bits.append(int(list(counts.keys())[0]))
        return bits

    def verify_nist_frequency(self, bits: list[int]) -> dict:
        n = len(bits)
        ones = sum(bits)
        zeros = n - ones
        ratio = abs(ones - zeros) / n
        return {
            "passed": ratio < 0.1,
            "ones": ones,
            "zeros": zeros,
            "ratio": ratio,
        }

    def verify_uniform_distribution(self, samples: list[int], expected_ratio: float = 0.5, tolerance: float = 0.1) -> dict:
        n = len(samples)
        ones = sum(samples)
        ratio = ones / n if n > 0 else 0
        return {
            "passed": abs(ratio - expected_ratio) < tolerance,
            "observed_ratio": ratio,
            "expected_ratio": expected_ratio,
            "sample_size": n,
        }

    def measure_circuit_depth(self, num_qubits: int, depth: int) -> dict:
        if not HAS_QISKIT:
            return {"depth": depth, "qubits": num_qubits, "measured": False}
        qc = QuantumCircuit(num_qubits)
        for _ in range(depth):
            for i in range(num_qubits - 1):
                qc.cx(i, i + 1)
            for i in range(num_qubits):
                qc.ry(0.1, i)
        return {"depth": qc.depth(), "qubits": qc.num_qubits, "gates": qc.size()}
