# Quantum Integration Architecture

## Overview

The CFZT system integrates quantum technologies across three domains: Quantum Random Number Generation (QRNG), Quantum Key Distribution (QKD), and Variational Quantum Circuits (VQC) for ML enhancement.

## Quantum Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUANTUM LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  QRNG              │  QKD                │  VQC                │
│  ├── HockeyPuck HW │  ├── BB84 Protocol  │  ├── Feature        │
│  ├── Qiskit Aer    │  ├── E91 Protocol   │  │   Encoding       │
│  └── CUDA-Q        │  └── QKD Network    │  ├── Variational    │
│                    │                     │  │   Classifier      │
│  Use: Token gen,   │  Use: Key exchange, │  └── Quantum        │
│  nonces, ZK rand   │  secure channels    │      Kernel         │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

## QRNG Architecture

### Hardware QRNG (HockeyPuck)

```
┌──────────────────────────────────────────────┐
│  Photonic Source ──▶ Beam Splitter ──▶ Detectors
│                                                  │
│  Detector A ──▶ ADC ──▶ ┌──────────────┐       │
│                         │  Conditioning │       │
│  Detector B ──▶ ADC ──▶ │  Circuit      │       │
│                         │  (Debiasing)  │       │
│                         └──────┬───────┘       │
│                                │               │
│                         ┌──────┴───────┐       │
│                         │  Health      │       │
│                         │  Tests       │       │
│                         │  (NIST SP    │       │
│                         │   800-90B)   │       │
│                         └──────┬───────┘       │
│                                │               │
│                         ┌──────┴───────┐       │
│                         │  Output      │       │
│                         │  Buffer      │       │
│                         └──────────────┘       │
└──────────────────────────────────────────────┘
```

**Specifications:**
- Throughput: 1 Mbit/s
- Min-entropy: 0.98 bits/bit
- Interface: USB 3.0 / PCIe
- Latency: <1ms per request

### QRNG Health Testing

```python
class QRNGHealthMonitor:
    def run_nist_tests(self, sample: bytes) -> HealthResult:
        tests = [
            self.frequency_monobit,      # NIST 800-90B 2.1
            self.frequency_block,         # NIST 800-90B 2.2
            self.cumulative_sum,          # NIST 800-90B 2.3
            self.longest_run,            # NIST 800-90B 2.4
            self.serial_correlation,     # NIST 800-90B 2.5
            self.approximate_entropy,     # NIST 800-90B 2.6
            self.diehard_battery,        # Additional
        ]
        results = [t(sample) for t in tests]
        return HealthResult(
            passed=all(r.passed for r in results),
            min_entropy=min(r.min_entropy for r in results),
            details=results
        )
```

### QRNG Fallback Strategy

```
┌─────────────────────────────────────────────────┐
│  QRNG Request                                    │
│  │                                               │
│  ▼                                               │
│  ┌──────────────┐   FAIL   ┌──────────────┐    │
│  │ Hardware QRNG│────────▶│ Simulator    │    │
│  └──────┬───────┘         └──────┬───────┘    │
│         │ PASS                    │ PASS        │
│         ▼                        ▼              │
│  ┌──────────────┐         ┌──────────────┐     │
│  │ Health Test  │  FAIL   │ Health Test  │     │
│  └──────┬───────┘────────▶└──────┬───────┘     │
│         │ PASS                    │ PASS         │
│         ▼                        ▼               │
│  ┌──────────────┐         ┌──────────────┐     │
│  │ Output Bits  │         │ Output Bits  │     │
│  └──────────────┘         └──────────────┘     │
│                                                   │
│  Both fail: Use CSPRNG (OpenSSL)                 │
│  Log alert: "QRNG degraded"                      │
└─────────────────────────────────────────────────┘
```

## QKD Architecture

### BB84 Protocol Implementation

```
┌─────────────────────────────────────────────────────┐
│  Alice (Sender)              │  Bob (Receiver)       │
│                              │                       │
│  Random bits ──▶ ────────▶ │ ──▶ Measurement       │
│  Random bases ──▶ Encode ──▶ │ ──▶ Decode           │
│                              │                       │
│  ◀──────── Sifted Key ──────▶│                       │
│                              │                       │
│  ◀──── Error Estimation ────▶│                       │
│                              │                       │
│  ◀──── Privacy Amplification▶│                       │
│                              │                       │
│  Final Key: 256 bits        │  Final Key: 256 bits  │
└─────────────────────────────────────────────────────┘
```

### QKD Network Topology

```
                    ┌─────────────┐
                    │  QKD        │
                    │  Trust Node │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────┴──────┐ ┌────┴────┐ ┌──────┴──────┐
     │   Node A    │ │  Node B │ │   Node C    │
     │  (AWS US)   │ │ (GCP EU)│ │  (Azure AP) │
     └─────────────┘ └─────────┘ └─────────────┘
```

### QKD Use Cases

1. **Inter-Service Key Exchange**
   - Services establish shared keys via QKD
   - Keys refreshed every 60 seconds
   - Used for mTLS session keys

2. **Database Encryption Keys**
   - QKD-derived keys for data-at-rest encryption
   - Key rotation: daily

3. **Backup Encryption**
   - QKD keys for backup encryption
   - Keys escrowed in HSM

## VQC Architecture

### Quantum Feature Encoding

```python
class QuantumFeatureEncoder:
    def encode(self, features: np.ndarray) -> QuantumCircuit:
        """
        Encode classical features into quantum states.
        Uses angle encoding for efficiency.
        """
        n_features = len(features)
        qc = QuantumCircuit(n_features)
        
        for i, feature in enumerate(features):
            # Normalize to [0, pi]
            angle = (feature + 1) * np.pi / 2
            qc.ry(angle, i)
        
        return qc
```

### Variational Quantum Classifier

```
┌─────────────────────────────────────────────────────┐
│  Classical Input                                     │
│  │                                                   │
│  ▼                                                   │
│  ┌─────────────────┐                                 │
│  │ Feature Encoding │ (Angle Encoding)               │
│  └────────┬────────┘                                 │
│           │                                          │
│  ┌────────▼────────┐                                 │
│  │ Parameterized   │ (RY, RZ rotations)             │
│  │ Quantum Circuit  │                                 │
│  └────────┬────────┘                                 │
│           │                                          │
│  ┌────────▼────────┐                                 │
│  │ Measurement     │ (Pauli Z)                       │
│  └────────┬────────┘                                 │
│           │                                          │
│  ┌────────▼────────┐                                 │
│  │ Classical       │ (Adam Optimizer)                │
│  │ Optimization    │                                 │
│  └────────┬────────┘                                 │
│           │                                          │
│  ┌────────▼────────┐                                 │
│  │ Updated         │ (Gradient Descent)              │
│  │ Parameters      │                                 │
│  └─────────────────┘                                 │
└─────────────────────────────────────────────────────┘
```

### VQC for Face Embedding Enhancement

1. **Input**: Classical face embedding (512-dim)
2. **Dimensionality Reduction**: PCA → 8-dim
3. **Quantum Encoding**: Angle encoding into 8 qubits
4. **Variational Layers**: 4 layers of parameterized gates
5. **Measurement**: Expectation values
6. **Output**: Enhanced embedding (16-dim)

### Hybrid Classical-Quantum Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  Classical Pipeline                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Face    │  │  ArcFace │  │  L2      │                  │
│  │  Detect  │──▶│  Embed   │──▶│  Norm    │                  │
│  └──────────┘  └──────────┘  └────┬─────┘                  │
│                                    │                         │
│  ┌─────────────────────────────────┼──────────────────┐     │
│  │  Quantum Enhancement (Optional) │                   │     │
│  │  ┌──────────┐  ┌──────────┐  ┌─▼────────┐         │     │
│  │  │  PCA     │  │  VQC     │  │  Output  │         │     │
│  │  │  Reduce  │──▶│  Enhance │──▶│  Blend   │         │     │
│  │  └──────────┘  └──────────┘  └──────────┘         │     │
│  └────────────────────────────────────────────────────┘     │
│                                    │                         │
│                                    ▼                         │
│                            ┌──────────────┐                  │
│                            │  Final       │                  │
│                            │  Embedding   │                  │
│                            └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Noise Models

### Hardware Noise Simulation

```python
class NoiseModel:
    def __init__(self):
        self.depolarizing_prob = 0.01
        self.amplitude_damping_prob = 0.02
        self.phase_damping_prob = 0.005
        self.readout_error_prob = 0.03
    
    def apply(self, circuit: QuantumCircuit) -> QuantumCircuit:
        noisy_circuit = circuit.copy()
        
        for gate in circuit.data:
            # Add depolarizing noise after each gate
            if np.random.random() < self.depolarizing_prob:
                noisy_circuit = self.add_depolarizing_error(
                    noisy_circuit, gate.qubits
                )
            
            # Add amplitude damping
            if np.random.random() < self.amplitude_damping_prob:
                noisy_circuit = self.add_amplitude_damping(
                    noisy_circuit, gate.qubits
                )
        
        # Add readout errors
        for qubit in range(circuit.num_qubits):
            if np.random.random() < self.readout_error_prob:
                noisy_circuit.x(qubit)
        
        return noisy_circuit
```

### Noise Mitigation Strategies

1. **Zero-Noise Extrapolation (ZNE)**
   - Run circuit at multiple noise levels
   - Extrapolate to zero noise
   - Overhead: 2-3x circuit executions

2. **Probabilistic Error Cancellation (PEC)**
   - Decompose noise into quasi-probability operators
   - Sample from quasi-distribution
   - Overhead: exponential in noise strength

3. **Dynamical Decoupling**
   - Insert DD sequences between gates
   - Reduce coherent errors
   - Overhead: additional gate count

## Quantum-Classical Interface

### API Contract

```protobuf
service QuantumService {
  rpc GenerateRandom(QuantumRandomRequest) returns (QuantumRandomResponse);
  rpc ExchangeKey(QKDKeyExchangeRequest) returns (QKDKeyExchangeResponse);
  rpc EnhanceEmbedding(VQCEnhanceRequest) returns (VQCEnhanceResponse);
  rpc GetHealth(QuantumHealthRequest) returns (QuantumHealthResponse);
}

message QuantumRandomRequest {
  int32 num_bits = 1;
  string purpose = 2;  // token, nonce, zk_proof, key_derivation
  bool require_hardware = 3;
}

message QuantumRandomResponse {
  bytes random_data = 1;
  string source = 2;  // hardware, simulator, hybrid
  float min_entropy = 3;
  bool health_passed = 4;
}
```

### Latency Budget

| Operation | Target Latency | Breakdown |
|-----------|---------------|-----------|
| QRNG (128 bits) | <5ms | USB: 1ms, Health: 2ms, Buffer: 2ms |
| QRNG (4096 bits) | <20ms | USB: 10ms, Health: 5ms, Buffer: 5ms |
| QKD Key Exchange | <100ms | Protocol: 50ms, Error: 20ms, Amplification: 30ms |
| VQC Enhancement | <50ms | Encoding: 10ms, Circuit: 30ms, Measurement: 10ms |
