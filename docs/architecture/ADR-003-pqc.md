# ADR-003: Post-Quantum Cryptography Migration

## Status

Accepted

## Context

Quantum computers threaten current cryptographic algorithms. We need to migrate to post-quantum algorithms while maintaining backward compatibility.

## Decision

### Algorithm Selection

| Purpose | Classical | Post-Quantum | Hybrid |
|---------|-----------|--------------|--------|
| Key Exchange | X25519 | Kyber-1024 | X25519 + Kyber-1024 |
| Digital Signature | Ed25519 | Dilithium-5 | Ed25519 + Dilithium-5 |
| Encryption | AES-256-GCM | Kyber-1024 + AES | Hybrid |
| Hashing | SHA-256 | SHA-3-256 | SHA-256 + SHA-3-256 |

### Migration Phases

#### Phase 1: Hybrid Mode (Current)
- Classical + PQC algorithms running in parallel
- Both signatures required for verification
- Key exchange uses both X25519 and Kyber

#### Phase 2: PQC Primary (2025)
- PQC algorithms as primary
- Classical algorithms as fallback
- Monitor for compatibility issues

#### Phase 3: PQC Only (2026)
- Remove classical algorithms
- PQC-only mode
- Full quantum resistance

### Implementation Strategy

```rust
// Hybrid Key Exchange
pub fn hybrid_key_exchange() -> (PublicKey, SharedSecret) {
    // Classical key exchange
    let classical_key = x25519::generate_keypair();
    
    // PQC key exchange
    let pqc_key = kyber::keypair();
    
    // Combine secrets
    let combined_secret = combine_secrets(
        classical_key.shared_secret(),
        pqc_key.shared_secret()
    );
    
    (HybridPublicKey { classical: classical_key.public, pqc: pqc_key.public },
     combined_secret)
}

// Hybrid Signature
pub fn hybrid_sign(message: &[u8], key: &HybridPrivateKey) -> HybridSignature {
    let classical_sig = ed25519::sign(message, &key.classical);
    let pqc_sig = dilithium::sign(message, &key.pqc);
    
    HybridSignature { classical: classical_sig, pqc: pqc_sig }
}
```

### Certificate Management

```yaml
# PQC Certificate Configuration
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: pqc-certificate
  namespace: cfzt
spec:
  secretName: pqc-tls-secret
  issuerRef:
    name: pqc-issuer
    kind: ClusterIssuer
  duration: 2160h  # 90 days
  renewBefore: 720h  # 30 days
  usages:
    - server auth
    - client auth
  privateKey:
    algorithm: ECDSA
    size: 256
  # PQC extension
  additionalExtensions:
    - name: pqcAlgorithm
      value: "kyber-1024+dilithium-5"
```

### Performance Considerations

| Operation | Classical | PQC | Hybrid |
|-----------|-----------|-----|--------|
| Key Generation | 0.1ms | 2.5ms | 2.6ms |
| Encapsulation | 0.1ms | 3.2ms | 3.3ms |
| Decapsulation | 0.1ms | 2.8ms | 2.9ms |
| Signing | 0.1ms | 4.1ms | 4.2ms |
| Verification | 0.1ms | 1.8ms | 1.9ms |

### Key Size Comparison

| Algorithm | Public Key | Private Key | Ciphertext/Signature |
|-----------|------------|-------------|---------------------|
| X25519 | 32 bytes | 32 bytes | 32 bytes |
| Kyber-1024 | 1568 bytes | 3168 bytes | 1568 bytes |
| Ed25519 | 32 bytes | 64 bytes | 64 bytes |
| Dilithium-5 | 2592 bytes | 4896 bytes | 4627 bytes |

## Consequences

### Positive
- Quantum-resistant security
- Backward compatibility during migration
- NIST-standardized algorithms
- Hybrid mode provides defense in depth

### Negative
- Larger key sizes (10-100x)
- Higher computational overhead
- Increased bandwidth usage
- Compatibility issues with legacy systems

### Risks
- Algorithm vulnerabilities (unlikely for NIST standards)
- Performance impact on high-throughput services
- Key management complexity
- Client library support

## Alternatives Considered

### Immediate PQC-Only
- Pros: Maximum security now
- Cons: Breaking change, compatibility issues

### Delayed Migration
- Pros: Wait for algorithm maturity
- Cons: Vulnerable to "harvest now, decrypt later" attacks

### Custom Algorithms
- Pros: Potentially better performance
- Cons: Security risks, no standardization

## Review Date

2025-03-01
