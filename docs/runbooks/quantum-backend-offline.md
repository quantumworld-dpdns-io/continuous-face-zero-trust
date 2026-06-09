# Quantum Backend Offline — Runbook

## Detection
- Alert: `QuantumBackendOffline` triggers
- Symptoms: QRNG fallback to local simulator, QKD failures

## Impact
- Quantum RNG falls back to classical PRNG (reduced security)
- QKD key distribution unavailable
- VQC embeddings degraded

## Immediate Response (0-5 min)

1. **Check quantum service health**:
   ```bash
   kubectl -n cfzt get pods -l app=quantum-rng
   kubectl -n cfzt logs -l app=quantum-rng --tail=50
   ```

2. **Check IBM Quantum connectivity** (if using cloud backend):
   ```bash
   curl -s "https://auth.quantum-computing.ibm.com/api/version" -H "X-IBM-Token: $TOKEN"
   ```

3. **Check CUDA-Q availability** (if using GPU):
   ```bash
   nvidia-smi
   ```

## Short-term Mitigation

1. **Verify fallback to local simulator**:
   - Service should automatically fallback
   - Check QUANTUM_BACKEND env var

2. **Restart quantum services**:
   ```bash
   kubectl -n cfzt rollout restart deployment/quantum-rng
   kubectl -n cfzt rollout restart deployment/quantum-key-exchange
   ```

## Root Cause Investigation

1. Check cloud provider status pages
2. Check network connectivity to quantum backends
3. Check GPU drivers (for CUDA-Q)
4. Check for quota limits

## Recovery

1. Monitor QBER when QKD reconnects
2. Verify quantum RNG NIST tests pass
3. Run quantum simulation tests
4. Update threat model if quantum downtime was prolonged
