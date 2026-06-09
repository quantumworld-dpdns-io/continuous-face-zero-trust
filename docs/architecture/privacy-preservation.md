# Privacy Preservation Architecture

## Core Principle

**No raw biometric data is ever stored, transmitted unnecessarily, or exposed to human operators.**

## What We Store

### Face Embeddings (512-d vectors)
- Normalized to unit length
- Stored in Qdrant vector database
- Encrypted at rest with AES-256-GCM
- Associated with device_id, not user identity

### What We NEVER Store
- Raw face images
- Face landmarks
- Bounding boxes
- Video frames
- Any recognizable biometric data

## Privacy Techniques

### 1. Embedding-Only Storage
```python
# Instead of storing the image:
# BAD:  {"image": base64_encode(face_photo)}
# GOOD: {"embedding": [0.12, -0.34, ...], "hash": "sha256..."}
```

### 2. Differential Privacy
- Add calibrated Laplace noise to embeddings
- ε-differential privacy guarantee
- Noise scale: sensitivity / epsilon
- Applied before storage and comparison

### 3. Zero-Knowledge Proofs
- Prove embedding matches without revealing it
- Prove liveness without revealing face features
- Prove age range without revealing exact age
- Prove session validity without revealing token

### 4. Secure Computation
- Embeddings compared in encrypted domain
- No plaintext biometrics in memory after processing
- Secure memory wiping after use

## Data Flow Privacy

```
Face Image → [In-Memory Processing] → Embedding
                                     ↓
                              Privacy Guard
                              - No raw image stored
                              - DP noise applied
                              - Hash computed
                                     ↓
                              Encrypted Storage
                              - AES-256-GCM
                              - Qdrant vector DB
                                     ↓
                              ZK Proof Generated
                              - Groth16/PLONK
                              - Proves match without revealing
```

## Compliance

### GDPR (General Data Protection Regulation)
- Biometric data is "special category" data
- Lawful basis: Legitimate interest (security)
- Right to erasure: Delete embedding = anonymize
- Data minimization: Only embeddings, no images
- Purpose limitation: Authentication only

### HIPAA (Health Insurance Portability)
- Biometric data as PHI (Protected Health Information)
- Access controls on embedding storage
- Audit trail for all access
- Encryption at rest and in transit

### CCPA (California Consumer Privacy Act)
- Right to know what data is collected
- Right to delete
- Right to opt-out of sale (we don't sell)
