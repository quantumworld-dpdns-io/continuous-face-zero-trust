# ADR-002: Quantum Integration Strategy

## Status

Accepted

## Context

We need to integrate quantum technologies to enhance security and randomness generation while managing quantum hardware dependencies and costs.

## Decision

### QRNG Integration

1. **Hardware QRNG (HockeyPuck)**
   - Primary source for true random numbers
   - 1 Mbit/s throughput
   - Used for: token generation, nonces, ZK proof randomness

2. **Simulator Fallback (Qiskit Aer)**
   - Fallback when hardware unavailable
   - 100K bits/s throughput
   - Used for: development, testing, degraded mode

3. **Hybrid Mode**
   - Mix QRNG + CSPRNG
   - Health testing on QRNG output
   - Automatic fallback on failure

### QKD Integration

1. **BB84 Protocol**
   - For inter-service key exchange
   - 256-bit keys
   - Refresh every 60 seconds

2. **QKD Network**
   - Trust node architecture
   - Multi-region key distribution
   - Fallback to PQC key exchange

### VQC Integration

1. **Feature Enhancement**
   - Optional quantum enhancement for face embeddings
   - 8-qubit circuits
   - Classical fallback available

2. **Variational Quantum Classifier**
   - Hybrid classical-quantum pipeline
   - Used for: anomaly detection, risk scoring

### Noise Mitigation

1. **Zero-Noise Extrapolation (ZNE)**
   - For VQC accuracy improvement
   - 2-3x overhead

2. **Probabilistic Error Cancellation (PEC)**
   - For high-accuracy requirements
   - Exponential overhead

### Hardware Strategy

| Component | Hardware | Simulator | Fallback |
|-----------|----------|-----------|----------|
| QRNG | HockeyPuck | Qiskit Aer | OpenSSL CSPRNG |
| QKD | Custom | - | PQC (Kyber) |
| VQC | IBM Quantum | Qiskit Aer | Classical ML |

## Consequences

### Positive
- True randomness from hardware QRNG
- Quantum-enhanced security against future quantum computers
- VQC may improve ML accuracy
- Future-proof architecture

### Negative
- Hardware QRNG adds cost (~$10K)
- QKD requires specialized infrastructure
- VQC adds latency and complexity
- Simulator not truly random

### Risks
- Quantum hardware availability
- QKD distance limitations
- VQC accuracy not guaranteed
- Vendor lock-in with hardware providers

## Alternatives Considered

### Pure Classical
- Pros: Simpler, proven technology
- Cons: Vulnerable to quantum attacks, weaker randomness

### Cloud QRNG (AWS Braket)
- Pros: No hardware investment
- Cons: Latency, cost, availability

### Custom QRNG
- Pros: Full control
- Cons: Development cost, expertise required

## Review Date

2025-06-01
