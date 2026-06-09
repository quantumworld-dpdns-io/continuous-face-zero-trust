# PQC Migration Developer Guide

## Overview

This guide covers migrating from classical to post-quantum cryptography in the CFZT system.

## Prerequisites

- Rust 1.70+
- liboqs-rust
- Understanding of PQC algorithms

## Installation

```bash
# Install liboqs-rust
cargo add liboqs-rust

# Or add to Cargo.toml
[dependencies]
liboqs-rust = "0.10"
```

## Algorithm Selection

| Purpose | Classical | Post-Quantum | Hybrid |
|---------|-----------|--------------|--------|
| Key Exchange | X25519 | Kyber-1024 | X25519 + Kyber-1024 |
| Digital Signature | Ed25519 | Dilithium-5 | Ed25519 + Dilithium-5 |
| Encryption | AES-256-GCM | Kyber-1024 + AES | Hybrid |

## Implementation

### 1. Key Exchange

```rust
use pqc_kyber::*;

fn hybrid_key_exchange() -> Result<(PublicKey, SharedSecret), Box<dyn std::error::Error>> {
    // Classical key exchange
    let classical_key = x25519::generate_keypair();
    
    // PQC key exchange
    let pqc_key = kyber::keypair();
    
    // Combine secrets
    let combined_secret = combine_secrets(
        classical_key.shared_secret(),
        pqc_key.shared_secret()
    );
    
    Ok((HybridPublicKey { classical: classical_key.public, pqc: pqc_key.public },
        combined_secret))
}
```

### 2. Digital Signatures

```rust
use pqc_dilithium::*;

fn hybrid_sign(message: &[u8], key: &HybridPrivateKey) -> Result<HybridSignature, Box<dyn std::error::Error>> {
    // Classical signature
    let classical_sig = ed25519::sign(message, &key.classical);
    
    // PQC signature
    let pqc_sig = dilithium::sign(message, &key.pqc);
    
    Ok(HybridSignature { classical: classical_sig, pqc: pqc_sig })
}

fn hybrid_verify(message: &[u8], signature: &HybridSignature, public_key: &HybridPublicKey) -> Result<bool, Box<dyn std::error::Error>> {
    // Verify classical signature
    let classical_valid = ed25519::verify(message, &signature.classical, &public_key.classical)?;
    
    // Verify PQC signature
    let pqc_valid = dilithium::verify(message, &signature.pqc, &public_key.pqc)?;
    
    Ok(classical_valid && pqc_valid)
}
```

### 3. Hybrid Encryption

```rust
use pqc_kyber::*;
use aes_gcm::*;

fn hybrid_encrypt(plaintext: &[u8], public_key: &HybridPublicKey) -> Result<HybridCiphertext, Box<dyn std::error::Error>> {
    // Generate AES key using KEM
    let (ciphertext, shared_secret) = kyber::encapsulate(&public_key.pqc)?;
    
    // Derive AES key from shared secret
    let aes_key = derive_aes_key(&shared_secret);
    
    // Encrypt with AES
    let cipher = Aes256Gcm::new(&aes_key);
    let nonce = generate_nonce();
    let aes_ciphertext = cipher.encrypt(&nonce, plaintext)?;
    
    Ok(HybridCiphertext {
        kem_ciphertext: ciphertext,
        aes_ciphertext: aes_ciphertext,
        nonce: nonce,
    })
}

fn hybrid_decrypt(ciphertext: &HybridCiphertext, private_key: &HybridPrivateKey) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    // Decapsulate shared secret
    let shared_secret = kyber::decapsulate(&ciphertext.kem_ciphertext, &private_key.pqc)?;
    
    // Derive AES key from shared secret
    let aes_key = derive_aes_key(&shared_secret);
    
    // Decrypt with AES
    let cipher = Aes256Gcm::new(&aes_key);
    let plaintext = cipher.decrypt(&ciphertext.nonce, ciphertext.aes_ciphertext.as_ref())?;
    
    Ok(plaintext)
}
```

## Configuration

### 1. Algorithm Configuration

```yaml
# config/pqc.yaml
pqc:
  enabled: true
  mode: hybrid  # hybrid, pqc-only, classical-only
  
  kem:
    algorithm: kyber-1024
    fallback: x25519
  
  signature:
    algorithm: dilithium-5
    fallback: ed25519
  
  encryption:
    algorithm: hybrid-kyber-aes
    fallback: aes-256-gcm
```

### 2. Service Configuration

```yaml
# k8s/pqc-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pqc-config
  namespace: cfzt
data:
  PQC_ENABLED: "true"
  PQC_MODE: "hybrid"
  KEM_ALGORITHM: "kyber-1024"
  SIGNATURE_ALGORITHM: "dilithium-5"
  ENCRYPTION_ALGORITHM: "hybrid-kyber-aes"
```

## Testing

### 1. Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kyber_key_generation() {
        let keypair = kyber::keypair();
        
        assert_eq!(keypair.public_key().len(), 1568);
        assert_eq!(keypair.private_key().len(), 3168);
    }
    
    #[test]
    fn test_kyber_encapsulation() {
        let keypair = kyber::keypair();
        let (ciphertext, shared_secret) = kyber::encapsulate(keypair.public_key());
        
        let decrypted_secret = kyber::decapsulate(&ciphertext, keypair.private_key());
        
        assert_eq!(shared_secret, decrypted_secret);
    }
    
    #[test]
    fn test_dilithium_signing() {
        let keypair = dilithium::keypair();
        let message = b"test message";
        
        let signature = dilithium::sign(message, keypair.private_key());
        let valid = dilithium::verify(message, &signature, keypair.public_key());
        
        assert!(valid);
    }
}
```

### 2. Integration Tests

```python
# tests/integration/test_pqc.py
import pytest
from cfzt.pqc import PQCClient

@pytest.fixture
def client():
    return PQCClient()

def test_kem(client):
    """Test KEM encapsulation/decapsulation."""
    public_key = client.generate_kem_keypair()
    ciphertext, shared_secret = client.kem_encapsulate(public_key)
    decrypted_secret = client.kem_decapsulate(ciphertext, public_key)
    
    assert shared_secret == decrypted_secret

def test_signing(client):
    """Test signing/verification."""
    public_key = client.generate_signing_keypair()
    message = b"test message"
    signature = client.sign(message, public_key)
    valid = client.verify(message, signature, public_key)
    
    assert valid
```

## Performance Considerations

| Operation | Classical | PQC | Hybrid |
|-----------|-----------|-----|--------|
| Key Generation | 0.1ms | 2.5ms | 2.6ms |
| Encapsulation | 0.1ms | 3.2ms | 3.3ms |
| Decapsulation | 0.1ms | 2.8ms | 2.9ms |
| Signing | 0.1ms | 4.1ms | 4.2ms |
| Verification | 0.1ms | 1.8ms | 1.9ms |

## Rollback

```bash
# Revert to classical algorithms
kubectl patch configmap pqc-config -n cfzt --type=merge -p '{"data":{"mode":"classical"}}'

# Restart services
kubectl rollout restart deployment/pqc-crypto-service -n cfzt
```

## Resources

- [liboqs Documentation](https://openquantumsafeproject.org/liboqs/)
- [NIST PQC Standards](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [CRYSTALS-Kyber](https://pq-crystals.org/kyber/)
- [CRYSTALS-Dilithium](https://pq-crystals.org/dilithium/)
