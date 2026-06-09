"""Variational Quantum Circuit for face embeddings."""
from __future__ import annotations

try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import ParameterVector
    from qiskit_aer import AerSimulator
except ImportError:
    QuantumCircuit = None
    ParameterVector = None
    AerSimulator = None

import numpy as np


class VQCEmbedder:
    def __init__(self, num_qubits: int = 4, depth: int = 2):
        self.num_qubits = num_qubits
        self.depth = depth
        self.params = ParameterVector("θ", num_qubits * depth)

    def build_circuit(self, classical_embedding: list[float]) -> "QuantumCircuit":
        if QuantumCircuit is None:
            raise ImportError("Qiskit is required for VQC embeddings")
        qc = QuantumCircuit(self.num_qubits, self.num_qubits)
        for i, val in enumerate(classical_embedding[:self.num_qubits]):
            qc.rx(val * np.pi, i)
        idx = 0
        for _ in range(self.depth):
            for i in range(self.num_qubits):
                qc.ry(self.params[idx], i)
                idx += 1
            for i in range(self.num_qubits - 1):
                qc.cx(i, i + 1)
        qc.measure(range(self.num_qubits), range(self.num_qubits))
        return qc

    def generate_embedding(self, classical_embedding: list[float]) -> np.ndarray:
        if AerSimulator is None:
            return np.random.randn(self.num_qubits * 4).astype(np.float32)
        qc = self.build_circuit(classical_embedding)
        backend = AerSimulator()
        param_values = {p: np.random.uniform(0, 2 * np.pi) for p in self.params}
        bound = qc.assign_parameters(param_values)
        result = backend.run(bound, shots=1024).result()
        counts = result.get_counts()
        probs = np.zeros(2**self.num_qubits)
        for bitstring, count in counts.items():
            idx = int(bitstring, 2)
            probs[idx] = count / 1024.0
        enhanced = np.concatenate([np.array(classical_embedding[:self.num_qubits]), probs]).astype(np.float32)
        return enhanced / (np.linalg.norm(enhanced) + 1e-8)
