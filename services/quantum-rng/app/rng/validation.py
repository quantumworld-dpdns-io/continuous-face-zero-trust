"""NIST SP 800-90B entropy validation tests."""
from __future__ import annotations

import math
from collections import Counter


def frequency_monobit_test(data: bytes) -> dict:
    bits = ''.join(format(b, '08b') for b in data)
    n = len(bits)
    s = sum(1 if b == '1' else -1 for b in bits)
    s_abs = abs(s) / math.sqrt(n)
    p_value = math.erfc(s_abs / math.sqrt(2))
    return {"test": "frequency_monobit", "passed": p_value > 0.01, "p_value": p_value}


def frequency_block_test(data: bytes, block_size: int = 128) -> dict:
    bits = ''.join(format(b, '08b') for b in data)
    n = len(bits)
    num_blocks = n // block_size
    if num_blocks == 0:
        return {"test": "frequency_block", "passed": False, "p_value": 0.0}

    proportions = []
    for i in range(num_blocks):
        block = bits[i * block_size:(i + 1) * block_size]
        pi = sum(1 for c in block if c == '1') / block_size
        proportions.append(pi)

    chi_sq = sum(4 * block_size * (p - 0.5) ** 2 for p in proportions)
    p_value = math.erfc(chi_sq / (2 * math.sqrt(num_blocks)))
    return {"test": "frequency_block", "passed": p_value > 0.01, "p_value": p_value}


def runs_test(data: bytes) -> dict:
    bits = ''.join(format(b, '08b') for b in data)
    n = len(bits)
    pi = sum(1 for b in bits if b == '1') / n
    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return {"test": "runs", "passed": False, "p_value": 0.0}

    runs = 1
    for i in range(1, n):
        if bits[i] != bits[i - 1]:
            runs += 1

    expected = 2 * n * pi * (1 - pi)
    z = abs(runs - expected) / math.sqrt(2 * expected)
    p_value = math.erfc(z / math.sqrt(2))
    return {"test": "runs", "passed": p_value > 0.01, "p_value": p_value}


def run_all_tests(data: bytes) -> list[dict]:
    results = [
        frequency_monobit_test(data),
        frequency_block_test(data),
        runs_test(data),
    ]
    all_passed = all(r["passed"] for r in results)
    return results + [{"all_passed": all_passed}]
