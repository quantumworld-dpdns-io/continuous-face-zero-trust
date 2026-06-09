"""BB84 Quantum Key Distribution protocol implementation."""
from __future__ import annotations

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
except ImportError:
    QuantumCircuit = None
    AerSimulator = None


class BB84Protocol:
    def __init__(self, num_qubits: int = 256):
        self.num_qubits = num_qubits
        self.backend = AerSimulator() if AerSimulator else None

    def generate_key_exchange(self) -> dict:
        alice_bases = np.random.randint(0, 2, self.num_qubits)
        alice_bits = np.random.randint(0, 2, self.num_qubits)

        if self.backend is None:
            bob_bases = np.random.randint(0, 2, self.num_qubits)
            bob_results = self._simulate_bob(alice_bits, alice_bases, bob_bases)
        else:
            bob_bases, bob_results = self._real_bob(alice_bits, alice_bases)

        sifted_alice, sifted_bob = self._sift_keys(alice_bits, bob_results, alice_bases, bob_bases)

        qber = self._compute_qber(sifted_alice, sifted_bob)
        reconciled_key = self._error_reconciliation(sifted_alice, sifted_bob)

        return {
            "sifted_key_length": len(reconciled_key),
            "qber": qber,
            "secure": qber < 0.11,
            "key": reconciled_key.tolist() if isinstance(reconciled_key, np.ndarray) else reconciled_key,
        }

    def _simulate_bob(self, alice_bits, alice_bases, bob_bases):
        results = []
        for i in range(self.num_qubits):
            if alice_bases[i] == bob_bases[i]:
                results.append(alice_bits[i])
            else:
                results.append(np.random.randint(0, 2))
        return np.array(results)

    def _real_bob(self, alice_bits, alice_bases):
        bob_bases = np.random.randint(0, 2, self.num_qubits)
        return bob_bases, self._simulate_bob(alice_bits, alice_bases, bob_bases)

    def _sift_keys(self, alice_bits, bob_bits, alice_bases, bob_bases):
        matching = alice_bases == bob_bases
        return alice_bits[matching], bob_bits[matching]

    def _compute_qber(self, alice_key, bob_key):
        if len(alice_key) == 0:
            return 1.0
        errors = np.sum(alice_key != bob_key)
        return float(errors / len(alice_key))

    def _error_reconciliation(self, alice_key, bob_key):
        return alice_key
