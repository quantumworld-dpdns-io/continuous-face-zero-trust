# Quantum Integration Architecture

## Quantum Computing Services

### 1. Quantum True Random Number Generation (QRNG)

**Purpose**: Generate cryptographically secure random numbers using quantum mechanical processes.

**Backends**:
- **Local Simulator**: Statevector simulator using Qiskit Aer (free, fast)
- **IBM Quantum**: Real quantum hardware via IBM Quantum Network ($1-10k/mo credits)
- **CUDA-Q**: GPU-accelerated quantum simulation (NVIDIA)
- **AWS Braket**: Access to IonQ, Rigetti, Oxford Quantum
- **Azure Quantum**: Access to Quantinuum, IonQ

**Flow**:
```
Request → Select Backend → Prepare Quantum Circuit (H gates)
         → Measure → Extract Random Bits → Validate (NIST SP 800-90B)
         → Return Random Bytes
```

**NIST Validation**:
- Frequency Monobit Test
- Frequency Block Test
- Runs Test
- Minimum Distance Test
- Spectral Test

### 2. Quantum Key Distribution (QKD)

**Purpose**: Distribute cryptographic keys with information-theoretic security.

**Protocols**:
- **BB84**: Original protocol with 4 states, 2 bases
- **SARG04**: Robust against photon number splitting attacks
- **E91**: Entanglement-based protocol (future)

**BB84 Flow**:
```
Alice: Generate random bits + bases → Encode qubits → Send to Bob
Bob:   Choose random bases → Measure qubits → Public basis comparison
       → Sift key → Error reconciliation → Privacy amplification
       → Shared secret key
```

**Security Parameters**:
- QBER threshold: 11% (above this, abort)
- Key rate: ~50% of raw bits after sifting
- Privacy amplification: Reduces to ε-secure key

### 3. Quantum Machine Learning

**Purpose**: Enhance face embeddings using quantum circuits.

**Approaches**:
- **VQC Embeddings**: Variational Quantum Circuits for embedding generation
- **Quantum Kernels**: Quantum kernel methods for similarity
- **Hybrid Training**: Classical neural network + quantum layer

**VQC Architecture**:
```
Input (classical embedding) → Angle Encoding → Parameterized Ansatz
→ Entangling Layers → Measurement → Enhanced Embedding
```

### 4. Post-Quantum Cryptography

**Purpose**: Resist attacks from future quantum computers.

**Algorithms** (NIST Standards):
- **ML-KEM (Kyber)**: Key encapsulation (FIPS 203)
- **ML-DSA (Dilithium)**: Digital signatures (FIPS 204)
- **SLH-DSA (SPHINCS+)**: Hash-based signatures (FIPS 205)
- **FALCON**: Compact signatures (alternative)

### 5. Zero-Knowledge Proofs

**Purpose**: Verify face authentication without revealing raw biometrics.

**Circuits**:
- **Face Verification**: Prove embedding is within range of enrolled template
- **Liveness Proof**: Prove liveness score exceeds threshold
- **Session Validity**: Prove session is valid without revealing token
- **Age Range**: Prove age is within range without revealing exact age

**Provers**:
- **Groth16**: Fastest proving, trusted setup required
- **PLONK**: Universal setup, flexible
- **Halo2**: No trusted setup, recursive proofs
- **Bulletproofs**: Short proofs, no trusted setup
