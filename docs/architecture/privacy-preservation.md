# Privacy Preservation Architecture

## Core Principle

**No raw biometric data is ever stored, transmitted, or processed beyond the immediate authentication need.**

## Privacy Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Privacy Architecture                                                │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  No Raw     │  │  Embeddings │  │  Differential│  │  ZK       │ │
│  │  Images     │  │  Only       │  │  Privacy     │  │  Proofs   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │                │        │
│         └────────────────┼────────────────┼────────────────┘        │
│                          │                │                          │
│                   ┌──────┴──────┐  ┌──────┴──────┐                  │
│                   │  Privacy    │  │  Consent    │                  │
│                   │  Engine     │  │  Manager    │                  │
│                   └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

## No Raw Images Policy

### Capture → Process → Discard

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Camera │────▶│  Face   │────▶│ Embedding│────▶│ Discard │
│         │     │  Detect │     │ Extract  │     │ Image   │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                                      │
                                      ▼
                                 ┌─────────┐
                                 │  Store  │
                                 │ Embedding│
                                 └─────────┘
```

### Implementation

```python
class PrivacyPreservingProcessor:
    def process_image(self, image: np.ndarray) -> Optional[Embedding]:
        """
        Process image and immediately discard raw data.
        Never store, log, or transmit raw images.
        """
        # Face detection
        faces = self.face_detector.detect(image)
        if not faces:
            return None
        
        # Extract primary face
        face = faces[0]
        
        # Generate embedding
        embedding = self.embedding_model.extract(face)
        
        # Quality check
        if not self.quality_check(embedding):
            return None
        
        # CRITICAL: Delete raw image immediately
        del image
        del face
        
        # Return only embedding (no raw data)
        return embedding
```

### Security Measures

1. **Memory Protection**
   - Raw images processed in isolated memory regions
   - Secure memory allocation (mlock, mprotect)
   - Immediate deallocation after processing
   - Memory scrubbing on deallocation

2. **Storage Protection**
   - No raw images in any storage (memory, disk, network)
   - Embeddings encrypted before storage
   - Temporary files encrypted and deleted
   - Swap space encrypted

3. **Transmission Protection**
   - Raw images never leave the device
   - Only embeddings transmitted (encrypted)
   - End-to-end encryption
   - No logging of raw data

## Embedding Storage

### Encrypted Embedding Schema

```json
{
  "embedding_id": "uuid-v4",
  "user_id": "user-uuid",
  "embedding": "base64-encoded-encrypted-embedding",
  "encryption": {
    "algorithm": "AES-256-GCM",
    "key_id": "user-key-uuid",
    "iv": "base64-encoded-iv",
    "tag": "base64-encoded-gcm-tag"
  },
  "metadata": {
    "created_at": "2024-01-01T00:00:00Z",
    "quality_score": 0.95,
    "model_version": "arcface-v1.2",
    "dimensions": 512
  },
  "zksnark_commitment": "pedersen-commitment-hash"
}
```

### Encryption Key Hierarchy

```
┌─────────────────────────────────────────┐
│  Master Key (HSM)                       │
│  └── Key Encryption Key (KEK)           │
│      └── Data Encryption Key (DEK)      │
│          └── Per-User Key (PUK)         │
│              └── Embedding Key (EK)     │
└─────────────────────────────────────────┘
```

### Key Rotation

- Master Key: Annual rotation
- KEK: Quarterly rotation
- DEK: Monthly rotation
- PUK: Per-session rotation
- EK: Per-embedding rotation (derived)

## Differential Privacy

### Noise Injection

```python
class DifferentialPrivacyEngine:
    def __init__(self, epsilon: float = 0.1, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta
    
    def add_laplace_noise(self, data: np.ndarray, sensitivity: float) -> np.ndarray:
        """Add Laplace noise for differential privacy."""
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale, data.shape)
        return data + noise
    
    def add_gaussian_noise(self, data: np.ndarray, sensitivity: float) -> np.ndarray:
        """Add Gaussian noise for differential privacy."""
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon
        noise = np.random.normal(0, sigma, data.shape)
        return data + noise
```

### Privacy Budget Management

```python
class PrivacyBudgetManager:
    def __init__(self, total_epsilon: float = 1.0):
        self.total_epsilon = total_epsilon
        self.used_epsilon = 0.0
    
    def can_query(self, epsilon_cost: float) -> bool:
        """Check if query is within privacy budget."""
        return self.used_epsilon + epsilon_cost <= self.total_epsilon
    
    def record_query(self, epsilon_cost: float):
        """Record query consumption."""
        self.used_epsilon += epsilon_cost
    
    def get_remaining_budget(self) -> float:
        """Get remaining privacy budget."""
        return self.total_epsilon - self.used_epsilon
```

### Privacy-Preserving Analytics

| Query Type | Epsilon Cost | Mechanism |
|------------|--------------|-----------|
| Count users | 0.01 | Laplace |
| Average similarity | 0.05 | Gaussian |
| Distribution analysis | 0.10 | Exponential |
| Anomaly detection | 0.20 | Report noisy max |

## Zero-Knowledge Proofs

### ZK Proof Types for Privacy

1. **Identity Proof**
   - Proves: "I am who I claim to be"
   - Without revealing: actual identity details
   - Circuit: `verify_identity(biometric_hash, identity_hash)`

2. **Attribute Proof**
   - Proves: "I have attribute X > threshold"
   - Without revealing: actual attribute value
   - Circuit: `verify_attribute(attribute, threshold)`

3. **Membership Proof**
   - Proves: "I am a member of group G"
   - Without revealing: which member I am
   - Circuit: `verify_membership(member_hash, merkle_root)`

### ZK Proof Implementation

```rust
// Noir circuit for face matching proof
fn main(
    embedding: [Field; 512],  // Private
    stored_hash: Field,       // Public
    threshold: Field,         // Public
) -> pub Field {
    // Hash the embedding
    let embedding_hash = poseidon::PoseidonHash::hash(embedding);
    
    // Verify embedding matches stored hash
    assert(embedding_hash == stored_hash);
    
    // Verify similarity threshold is met
    // (simplified - actual implementation uses cosine similarity)
    let similarity = compute_similarity(embedding, stored_embedding);
    assert(similarity >= threshold);
    
    // Return proof commitment
    embedding_hash
}
```

### Privacy Guarantees

| Claim | What's Proved | What's Hidden |
|-------|---------------|---------------|
| Identity | Biometric match | Actual embedding |
| Liveness | Live person | Liveness parameters |
| Age | Age > threshold | Actual age |
| Membership | Group membership | Specific member |
| Location | Location in region | Exact coordinates |

## Consent Management

### Consent Schema

```json
{
  "user_id": "uuid",
  "consents": [
    {
      "purpose": "biometric_authentication",
      "granted": true,
      "timestamp": "2024-01-01T00:00:00Z",
      "expires": "2025-01-01T00:00:00Z",
      "scope": ["face_embedding", "liveness_check"]
    },
    {
      "purpose": "analytics",
      "granted": false,
      "timestamp": "2024-01-01T00:00:00Z",
      "scope": ["anonymized_usage"]
    }
  ],
  "withdrawal": {
    "available": true,
    "method": "api_or_ui",
    "processing_time": "30_days"
  }
}
```

### Consent Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────▶│ Consent │────▶│ System  │
│         │◀────│ Manager │◀────│ Check   │
└─────────┘     └─────────┘     └─────────┘
```

1. **Collection**: Explicit, informed consent
2. **Storage**: Encrypted, versioned consent records
3. **Enforcement**: System checks consent before processing
4. **Withdrawal**: User can withdraw consent anytime
5. **Deletion**: Data deleted upon consent withdrawal

## Data Subject Rights

### Right to Access

```python
def export_user_data(user_id: str) -> dict:
    """Export all user data (GDPR Article 15)."""
    return {
        "user_id": user_id,
        "embeddings": get_user_embeddings(user_id),
        "sessions": get_user_sessions(user_id),
        "consents": get_user_consents(user_id),
        "audit_logs": get_user_audit_logs(user_id),
        "metadata": get_user_metadata(user_id)
    }
```

### Right to Erasure

```python
def delete_user_data(user_id: str) -> bool:
    """Delete all user data (GDPR Article 17)."""
    # Cryptographic erasure
    delete_user_keys(user_id)  # Delete encryption keys
    delete_user_embeddings(user_id)  # Delete embeddings
    delete_user_sessions(user_id)  # Delete sessions
    delete_user_consents(user_id)  # Delete consents
    log_erasure(user_id)  # Log for audit (retained)
    return True
```

### Right to Portability

```python
def export_portable_data(user_id: str) -> bytes:
    """Export data in machine-readable format (GDPR Article 20)."""
    data = export_user_data(user_id)
    return json.dumps(data, indent=2).encode()
```

## Privacy Audit Trail

### Audit Event Schema

```json
{
  "event_id": "uuid",
  "event_type": "data_access|data_modification|consent_change",
  "user_id": "uuid",
  "actor": "system|user|admin",
  "action": "read|write|delete|export",
  "resource": "embedding|session|consent",
  "timestamp": "2024-01-01T00:00:00Z",
  "ip_address": "hashed-ip",
  "user_agent": "sanitized-agent",
  "result": "success|failure",
  "privacy_impact": "low|medium|high"
}
```

### Audit Retention

| Event Type | Retention | Storage |
|------------|-----------|---------|
| Data Access | 1 year | CockroachDB → S3 |
| Data Modification | 1 year | CockroachDB → S3 |
| Consent Changes | 3 years | CockroachDB → S3 |
| Security Events | 7 years | CockroachDB → S3 |
