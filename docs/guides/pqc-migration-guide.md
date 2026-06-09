# PQC Migration Guide

## Overview

This guide covers migrating from classical cryptography to post-quantum cryptography (PQC).

## Migration Timeline

### Phase 1: Assessment (Week 1-2)
- [ ] Inventory all cryptographic usage
- [ ] Identify classical algorithms in use (RSA, ECDSA, ECDH)
- [ ] Assess data sensitivity and retention requirements
- [ ] Prioritize migration targets

### Phase 2: Hybrid Mode (Week 3-6)
- [ ] Enable hybrid classical+PQC modes
- [ ] Kyber-768 for key encapsulation (alongside ECDH)
- [ ] Dilithium-3 for signatures (alongside ECDSA)
- [ ] Test backward compatibility

### Phase 3: PQC-Primary (Week 7-12)
- [ ] Switch to PQC-primary, classical-secondary
- [ ] Monitor performance metrics
- [ ] Update key rotation policies
- [ ] Update compliance documentation

### Phase 4: PQC-Only (Week 13+)
- [ ] Remove classical algorithms
- [ ] Full PQC deployment
- [ ] Update threat model
- [ ] Certify for compliance

## Algorithm Selection

| Use Case | Algorithm | Security Level | Key Size |
|----------|-----------|---------------|----------|
| Key Encapsulation | ML-KEM-768 | NIST Level 3 | 1184 bytes |
| Digital Signature | ML-DSA-65 | NIST Level 3 | 1952 bytes |
| Compact Signature | Falcon-512 | NIST Level 1 | 896 bytes |
| Hash Signature | SLH-DSA-SHA2-128s | NIST Level 1 | 7856 bytes |

## Code Changes

### Before (Classical)
```python
from cryptography.hazmat.primitives.asymmetric import ec
private_key = ec.generate_private_key(ec.SECP256R1())
signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
```

### After (PQC)
```python
import pqcrypto.sign.dilithium as dilithium
private_key, public_key = dilithium.generate_keypair()
signature = dilithium.sign(private_key, message)
```

### Hybrid (Transitional)
```python
# Sign with both classical and PQC
classical_sig = classical_sign(classical_key, message)
pqc_sig = dilithium.sign(pqc_key, message)
hybrid_sig = combine(classical_sig, pqc_sig)
```

## Performance Considerations

| Operation | RSA-2048 | Dilithium-3 | Kyber-768 |
|-----------|----------|-------------|-----------|
| Key Gen | 150ms | 0.5ms | 0.3ms |
| Sign | 0.8ms | 0.4ms | N/A |
| Verify | 0.02ms | 0.1ms | N/A |
| Encapsulate | N/A | N/A | 0.2ms |
| Decapsulate | N/A | N/A | 0.3ms |

## Testing

```bash
# Run PQC test suite
robot tests/robot/owasp/A02_cryptographic_failures.robot

# Run PQC performance tests
robot tests/robot/performance/pqc_encryption.robot

# Run NIST test vectors
python -m services.pqc_crypto.app.kem.test_vectors
```
