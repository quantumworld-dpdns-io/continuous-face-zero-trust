# ADR-004: Zero-Knowledge Proof System Selection

## Status

Accepted

## Context

We need ZK proofs to verify biometric claims without revealing sensitive data. Selection must balance performance, security, and developer experience.

## Decision

### Proof System Selection

| System | Proving Time | Verification Time | Proof Size | Use Case |
|--------|--------------|-------------------|------------|----------|
| Groth16 | 500ms | 10ms | 200 bytes | Face matching |
| PLONK | 800ms | 15ms | 400 bytes | Liveness proof |
| Marlin | 1000ms | 20ms | 500 bytes | Age proof |
| Bulletproofs | 2000ms | 50ms | 1.5KB | Range proofs |

### Primary System: Groth16

**Rationale:**
- Fastest verification (10ms)
- Smallest proof size (200 bytes)
- Well-studied security
- Good tooling support

**Circuits:**

1. **Face Matching Proof**
```rust
// Noir circuit
fn main(
    embedding: [Field; 512],  // Private
    stored_hash: Field,       // Public
    threshold: Field,         // Public
) -> pub Field {
    let embedding_hash = poseidon::PoseidonHash::hash(embedding);
    assert(embedding_hash == stored_hash);
    embedding_hash
}
```

2. **Liveness Proof**
```rust
fn main(
    image_features: [Field; 256],  // Private
    liveness_threshold: Field,     // Public
    model_hash: Field,             // Public
) -> pub Field {
    let liveness_score = compute_liveness(image_features);
    assert(liveness_score >= liveness_threshold);
    poseidon::PoseidonHash::hash(image_features)
}
```

3. **Age Proof**
```rust
fn main(
    age_estimate: Field,     // Private
    age_threshold: Field,    // Public
    model_hash: Field,       // Public
) -> pub Field {
    assert(age_estimate >= age_threshold);
    poseidon::PoseidonHash::hash([age_estimate])
}
```

### Implementation Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Circuit Language | Noir | Developer-friendly, type safety |
| Proof System | Groth16 | Performance, security |
| Cryptography | ArkWorks | Rust ecosystem, audited |
| Trusted Setup | Per-circuit | Required for Groth16 |

### Proof Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Generate   │────▶│  Store      │────▶│  Verify     │
│  Proof      │     │  Proof      │     │  Proof      │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐
│  Circuit    │     │  Encrypted  │     │  Public     │
│  Compile    │     │  Storage    │     │  Inputs     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Proof Aggregation

```python
class ProofAggregator:
    def aggregate(self, proofs: List[Proof]) -> AggregatedProof:
        """Aggregate multiple proofs into one."""
        # Verify individual proofs
        for proof in proofs:
            assert self.verify(proof)
        
        # Aggregate using recursive proof
        aggregated = self.aggregate_proofs(proofs)
        
        # Return single proof
        return aggregated
    
    def verify_aggregated(self, aggregated: AggregatedProof) -> bool:
        """Verify aggregated proof."""
        return self.verify_recursive(aggregated)
```

### Trusted Setup

```bash
# Generate trusted setup parameters
cargo run --release -- circuit setup \
    --circuit-name face_matching \
    --output ./params/face_matching.params \
    --entropy "$(qrng generate --bits 256)"

# Contribute to ceremony
cargo run --release -- circuit contribute \
    --circuit-name face_matching \
    --params ./params/face_matching.params \
    --entropy "$(qrng generate --bits 256)"
```

## Consequences

### Positive
- Groth16 provides fastest verification
- Noir circuit language is developer-friendly
- ArkWorks provides audited cryptography
- Proof aggregation reduces on-chain costs

### Negative
- Trusted setup required for Groth16
- Circuit updates require new trusted setup
- Proof generation is computationally expensive
- Larger proof size than hash-based approaches

### Risks
- Trusted setup compromise
- Circuit vulnerabilities
- Quantum attacks on elliptic curves (mitigated by PQC)

## Alternatives Considered

### PLONK
- Pros: Universal trusted setup
- Cons: Slower verification, larger proofs

### STARKs
- Pros: No trusted setup, quantum-resistant
- Cons: Very large proofs, slower verification

### Bulletproofs
- Pros: No trusted setup, small proofs
- Cons: Slow proving and verification

## Review Date

2025-06-01
