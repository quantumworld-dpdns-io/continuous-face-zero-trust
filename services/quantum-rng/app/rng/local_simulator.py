"""Local statevector quantum simulator for RNG."""
from __future__ import annotations

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
except ImportError:
    QuantumCircuit = None
    AerSimulator = None


class LocalQuantumSimulator:
    def __init__(self):
        self.backend = AerSimulator() if AerSimulator else None

    def generate_random_bits(self, num_bits: int) -> list[int]:
        if self.backend is None:
            return [np.random.randint(0, 2) for _ in range(num_bits)]

        bits = []
        for _ in range(num_bits):
            qc = QuantumCircuit(1, 1)
            qc.h(0)
            qc.measure(0, 0)
            result = self.backend.run(qc, shots=1).result()
            counts = result.get_counts()
            bit = int(list(counts.keys())[0])
            bits.append(bit)
        return bits

    def generate_random_bytes(self, num_bytes: int) -> bytes:
        bits = self.generate_random_bits(num_bytes * 8)
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte = (byte << 1) | bits[i + j]
            result.append(byte)
        return bytes(result)

    def generate_uniform_float(self) -> float:
        bits = self.generate_random_bits(32)
        value = 0
        for b in bits:
            value = (value << 1) | b
        return value / (2**32)
