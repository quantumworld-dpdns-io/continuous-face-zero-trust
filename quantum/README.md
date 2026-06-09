# Quantum Computing Experiments

This directory contains quantum computing experiments and circuit definitions.

## Experiments

### 1. QRNG Entropy Analysis
- `qrng_entropy.py` — Analyze entropy quality of quantum random number generation
- Compare local simulator vs IBM Quantum backend

### 2. QKD Protocol Testing
- `bb84_simulation.py` — Full BB84 protocol simulation
- `qber_analysis.py` — Quantum Bit Error Rate analysis
- `privacy_amplification.py` — Privacy amplification implementation

### 3. Quantum ML for Face Embeddings
- `vqc_embedding.py` — Variational Quantum Circuit for face embeddings
- `quantum_kernel.py` — Quantum kernel methods
- `hybrid_training.py` — Classical+quantum hybrid training

### 4. Quantum Circuit Optimization
- `circuit_transpilation.py` — Transpilation for different backends
- `noise_mitigation.py` — Error mitigation techniques
- `circuit_cutting.py` — Circuit cutting for large circuits

## Running

```bash
# Run all experiments
python -m quantum.run_all

# Run specific experiment
python -m quantum.vqc_embedding

# Compare backends
python -m quantum.backend_comparison
```
