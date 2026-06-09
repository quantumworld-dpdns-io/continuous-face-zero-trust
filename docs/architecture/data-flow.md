# Data Flow Architecture

## Overview

This document describes all data flows in the Continuous Face Zero-Trust system, covering authentication, enrollment, continuous verification, ZK proof generation, and quantum random number generation.

## Authentication Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client  │────▶│  Edge   │────▶│  Auth   │────▶│CockroachDB│
│         │◀────│ Gateway │◀────│ Service │◀────│ (Users) │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                     │               │
                     │               │
                ┌────┴────┐    ┌────┴────┐
                │  Redis  │    │ Face ML │
                │ (Cache) │    │ Service │
                └─────────┘    └─────────┘
```

### Step-by-Step Flow

1. **Client Request**
   - Client captures face image via camera
   - Image is PQC-encrypted (Kyber-1024 + AES-256-GCM)
   - Request sent to nearest Cloudflare edge node

2. **Edge Processing** (Cloudflare Worker)
   - TLS 1.3 termination
   - WAF rule evaluation
   - Rate limit check (Redis-backed)
   - Device fingerprint validation
   - Request forwarding via mTLS to auth service

3. **Auth Service** (Go)
   - Validates JWT/PASETO token or initiates new session
   - Calls Face ML service for embedding generation
   - Queries Qdrant for stored embeddings
   - Computes similarity score
   - Risk assessment (device trust + face score + behavioral)
   - Issues new session token (PASETO v4)
   - Stores session in Redis (TTL: 24h)

4. **Response**
   - Session token returned to client
   - Refresh interval set based on risk score
   - Low risk: 5min refresh; High risk: 30s refresh

## Enrollment Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client  │────▶│  Face   │────▶│  ZK     │────▶│ Qdrant  │
│         │◀────│  ML     │◀────│ Proofs  │◀────│(Embed)  │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
```

### Step-by-Step Flow

1. **Capture Phase**
   - Client captures 5-10 face images at different angles
   - Images encrypted client-side (never sent raw)
   - PQC hybrid encryption (Kyber + AES)

2. **Embedding Generation** (Face ML Service)
   - Face detection (RetinaFace)
   - Alignment and normalization
   - Embedding extraction (ArcFace, 512-dim)
   - Quality assessment (blur, lighting, pose)
   - Reject low-quality samples

3. **ZK Proof Generation** (ZK Proofs Service)
   - Generate proof that embedding is valid
   - Prove embedding matches claimed identity
   - No raw image data in proof

4. **Storage**
   - Embeddings stored in Qdrant (encrypted at rest)
   - Metadata in CockroachDB (user_id, created_at, quality_score)
   - No raw images stored anywhere

## Continuous Verification Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client  │────▶│  Face   │────▶│  Vector │
│ (Timer)  │◀────│  ML     │◀────│  Search │
└─────────┘     └─────────┘     └─────────┘
     │               │               │
     │               │               │
┌────┴────┐    ┌────┴────┐    ┌────┴────┐
│  Auth   │    │  Risk   │    │  Qdrant │
│ Service │    │ Engine  │    │         │
└─────────┘    └─────────┘    └─────────┘
```

### Step-by-Step Flow

1. **Scheduled Capture**
   - Client timer triggers face capture (every 30s-5min)
   - Adaptive interval based on risk score
   - Higher risk = more frequent captures

2. **Real-Time Processing**
   - Face detection + embedding generation (<100ms)
   - Vector similarity search against stored embeddings
   - Cosine similarity threshold: 0.85

3. **Decision Logic**
   ```
   IF similarity >= 0.95:
       risk_score -= 0.1 (high confidence match)
   ELIF similarity >= 0.85:
       risk_score += 0.0 (normal)
   ELIF similarity >= 0.70:
       risk_score += 0.3 (low confidence)
       trigger_liveness_challenge()
   ELSE:
       risk_score += 0.5 (mismatch)
       trigger_step_up_auth()
   ```

4. **Adaptive Response**
   - High confidence: extend refresh interval
   - Medium confidence: maintain current interval
   - Low confidence: trigger liveness challenge
   - Mismatch: force re-authentication

## ZK Proof Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Face   │────▶│  ZK     │────▶│ Verifier│
│  ML     │     │  Prover │     │ Service │
└─────────┘     └─────────┘     └─────────┘
```

### Proof Types

1. **Face Proof** (证明面部匹配)
   - Proves: "I have a face embedding that matches the stored one"
   - Without revealing: the actual embedding
   - Circuit: `face_match(embedding, stored_hash) == true`

2. **Liveness Proof** (证明活体)
   - Proves: "I am a live person, not a photo/video"
   - Without revealing: liveness detection parameters
   - Circuit: `liveness_check(image_features) == true`

3. **Age Proof** (证明年龄范围)
   - Proves: "I am over 18"
   - Without revealing: actual age
   - Circuit: `age_check(age_estimate, threshold) == true`

### Proof Generation Steps

1. **Circuit Preparation**
   - Load pre-compiled Noir/ArkWorks circuit
   - Prepare witness (private inputs)
   - Prepare public inputs (hash commitments)

2. **Proving**
   - Generate Groth16 proof
   - Proof size: ~200 bytes
   - Generation time: <500ms

3. **Verification**
   - Verify proof against public inputs
   - Verification time: <10ms
   - Result: accept/reject

## Quantum RNG Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Auth   │────▶│  QRNG   │────▶│ Entropy │
│ Service │◀────│ Service │◀────│  Pool   │
└─────────┘     └─────────┘     └─────────┘
```

### QRNG Usage Points

1. **Session Token Generation**
   - QRNG seeds CSPRNG
   - Tokens are quantum-random

2. **Nonce/IV Generation**
   - All nonces from QRNG
   - Prevents nonce reuse attacks

3. **ZK Proof Randomness**
   - Proof generation requires random blinding
   - QRNG provides truly random values

4. **Key Derivation**
   - HKDF salt from QRNG
   - Improves key derivation security

### QRNG Modes

1. **Hardware Mode** (HockeyPuck QRNG)
   - Photonic detection
   - 1 Mbit/s throughput
   - Min-entropy: 0.98 bits/bit

2. **Simulator Mode** (Qiskit Aer)
   - Quantum circuit simulation
   - 100K bits/s throughput
   - For development/testing

3. **Hybrid Mode**
   - Mix QRNG + CSPRNG
   - Health testing on QRNG output
   - Fallback to CSPRNG if QRNG fails

## Data Encryption Flows

### At Rest

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  App    │────▶│  KMS    │────▶│  Disk   │
│         │◀────│ (AWS/  │◀────│ (AES-  │
│         │     │  GCP)  │     │  256)   │
└─────────┘     └─────────┘     └─────────┘
```

- Embeddings: AES-256-GCM with per-user keys
- Sessions: AES-256-GCM with cluster key
- Audit logs: AES-256-GCM with master key

### In Transit

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client  │────▶│  TLS    │────▶│  Server │
│         │◀────│  1.3 +  │◀────│         │
│         │     │  PQC    │     │         │
└─────────┘     └─────────┘     └─────────┘
```

- TLS 1.3 with PQC hybrid key exchange
- Kyber-1024 + X25519 (hybrid mode)
- Forward secrecy guaranteed

## Event Streaming

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Auth   │────▶│  Kafka  │────▶│Analytics│
│ Service │     │ (Events)│     │ Service │
└─────────┘     └─────────┘     └─────────┘
                     │
                     │
                ┌────┴────┐
                │  S3     │
                │(Archive)│
                └─────────┘
```

### Event Types

| Event | Topic | Retention |
|-------|-------|-----------|
| auth.success | auth-events | 90 days |
| auth.failure | auth-events | 90 days |
| auth.challenge | auth-events | 90 days |
| enrollment.complete | enrollment-events | 90 days |
| continuous_verify.result | verify-events | 30 days |
| zk_proof.generated | proof-events | 30 days |
| security.anomaly | security-events | 1 year |
