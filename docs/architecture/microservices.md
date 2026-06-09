# Microservices Architecture

## Service Decomposition

### Bounded Contexts

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BOUNDED CONTEXTS                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  IDENTITY CONTEXT                                                  │ │
│  │  ├── Auth Service                                                  │ │
│  │  ├── Session Service                                               │ │
│  │  └── Token Service                                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  BIOMETRIC CONTEXT                                                 │ │
│  │  ├── Face Detection Service                                        │ │
│  │  ├── Face Embedding Service                                        │ │
│  │  ├── Liveness Detection Service                                    │ │
│  │  └── Face Matching Service                                         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  CRYPTOGRAPHIC CONTEXT                                             │ │
│  │  ├── PQC Crypto Service                                            │ │
│  │  ├── ZK Proofs Service                                             │ │
│  │  └── Key Management Service                                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  QUANTUM CONTEXT                                                   │ │
│  │  ├── QRNG Service                                                  │ │
│  │  ├── QKD Service                                                   │ │
│  │  └── VQC Service                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  DATA CONTEXT                                                      │ │
│  │  ├── Vector DB Service                                             │ │
│  │  ├── Cache Store Service                                           │ │
│  │  └── Analytics Service                                             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  EDGE CONTEXT                                                      │ │
│  │  ├── Edge Gateway Service                                          │ │
│  │  └── CDN Service                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Service Specifications

### 1. Auth Service (Go)

```yaml
# Auth Service Specification
service:
  name: auth-service
  language: go
  framework: gin
  version: v1.0.0
  
ports:
  grpc: 8080
  http: 8081
  health: 8082
  
dependencies:
  databases:
    - cockroachdb: user identities, sessions
    - redis: session cache, rate limits
  services:
    - face-ml-service: biometric verification
    - pqc-crypto-service: token signing
    - zk-proofs-service: proof verification
    - quantum-rng-service: random generation
  
responsibilities:
  - Session lifecycle management
  - JWT/PASETO token issuance
  - Continuous verification orchestration
  - Risk scoring
  - Rate limiting
  
api:
  grpc:
    - Login
    - Enroll
    - RefreshToken
    - Logout
    - ContinuousVerify
    - GetSession
  http:
    - POST /api/v1/auth/login
    - POST /api/v1/auth/enroll
    - POST /api/v1/auth/refresh
    - POST /api/v1/auth/logout
    - POST /api/v1/auth/verify
    - GET /api/v1/sessions/:id
```

### 2. Face ML Service (Python)

```yaml
# Face ML Service Specification
service:
  name: face-ml-service
  language: python
  framework: fastapi
  version: v1.0.0
  
ports:
  grpc: 8082
  http: 8083
  health: 8084
  
dependencies:
  models:
    - arcface: face embeddings
    - retinface: face detection
    - liveness-detector: anti-spoofing
  infrastructure:
    - nvidia-gpu: inference acceleration
    - qdrant: embedding storage
  
responsibilities:
  - Face detection and alignment
  - Embedding generation
  - Liveness detection
  - Similarity matching
  - Quality assessment
  
api:
  grpc:
    - Detect
    - Embed
    - Compare
    - LivenessCheck
    - Search
    - QuantumEmbed
  http:
    - POST /api/v1/face/detect
    - POST /api/v1/face/embed
    - POST /api/v1/face/compare
    - POST /api/v1/face/liveness
    - POST /api/v1/face/search
```

### 3. PQC Crypto Service (Rust)

```yaml
# PQC Crypto Service Specification
service:
  name: pqc-crypto-service
  language: rust
  framework: tonic (gRPC)
  version: v1.0.0
  
ports:
  grpc: 8086
  http: 8087
  health: 8088
  
dependencies:
  libraries:
    - liboqs-rust: PQC algorithms
    - ring: classical crypto
    - tokio: async runtime
  
responsibilities:
  - Post-quantum KEM (Kyber)
  - Post-quantum signatures (Dilithium, FALCON)
  - Hybrid encryption
  - Key derivation
  - Certificate management
  
api:
  grpc:
    - KemEncapsulate
    - KemDecapsulate
    - Sign
    - Verify
    - Encrypt
    - Decrypt
    - GetAlgorithms
  http:
    - POST /api/v1/crypto/kem/encapsulate
    - POST /api/v1/crypto/kem/decapsulate
    - POST /api/v1/crypto/sign
    - POST /api/v1/crypto/verify
    - POST /api/v1/crypto/encrypt
    - POST /api/v1/crypto/decrypt
```

### 4. ZK Proofs Service (Rust)

```yaml
# ZK Proofs Service Specification
service:
  name: zk-proofs-service
  language: rust
  framework: tonic (gRPC)
  version: v1.0.0
  
ports:
  grpc: 8088
  http: 8089
  health: 8090
  
dependencies:
  libraries:
    - arkworks: ZK proof system
    - noir: circuit compiler
  infrastructure:
    - quantum-rng-service: randomness
  
responsibilities:
  - ZK-SNARK proof generation
  - Proof verification
  - Circuit compilation
  - Proof aggregation
  
api:
  grpc:
    - GenerateProof
    - VerifyProof
    - GenerateFaceProof
    - GenerateLivenessProof
    - AggregateProofs
  http:
    - POST /api/v1/zk/generate
    - POST /api/v1/zk/verify
    - POST /api/v1/zk/face-proof
    - POST /api/v1/zk/liveness-proof
    - POST /api/v1/zk/aggregate
```

### 5. Quantum RNG Service (Python)

```yaml
# Quantum RNG Service Specification
service:
  name: quantum-rng-service
  language: python
  framework: fastapi
  version: v1.0.0
  
ports:
  grpc: 8084
  http: 8085
  health: 8086
  
dependencies:
  hardware:
    - hockeypuck-qrng: true random numbers
  software:
    - qiskit-aer: quantum simulation
    - cuda-q: GPU-accelerated simulation
  
responsibilities:
  - True random number generation
  - Quantum entropy mixing
  - Health testing (NIST 800-90B)
  - Entropy pool management
  
api:
  grpc:
    - GenerateRandom
    - GetHealth
    - GetEntropyPool
  http:
    - POST /api/v1/quantum/rng/generate
    - GET /api/v1/quantum/rng/health
    - GET /api/v1/quantum/rng/pool
```

## Communication Patterns

### Synchronous (gRPC)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client  │────▶│  Auth   │────▶│ Face ML │
│         │◀────│ Service │◀────│ Service │
└─────────┘     └─────────┘     └─────────┘
```

**Use Cases:**
- Real-time face verification
- Token validation
- Health checks

### Asynchronous (Kafka)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Auth   │────▶│  Kafka  │────▶│Analytics│
│ Service │     │ (Events)│     │ Service │
└─────────┘     └─────────┘     └─────────┘
```

**Use Cases:**
- Audit logging
- Analytics events
- Background processing

### Event-Driven

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Auth   │────▶│  Event  │────▶│ Multiple│
│ Service │     │  Bus    │     │ Services│
└─────────┘     └─────────┘     └─────────┘
```

**Use Cases:**
- Cross-service notifications
- Workflow orchestration
- Saga pattern

## API Gateway

### Edge Gateway Configuration

```yaml
# Edge Gateway Configuration
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: edge-gateway
  namespace: cfzt
spec:
  hosts:
  - api.cfzt.io
  gateways:
  - cfzt/edge-gateway
  http:
  - match:
    - uri:
        prefix: /api/v1/auth
    route:
    - destination:
        host: auth-service
        port:
          number: 8080
  - match:
    - uri:
        prefix: /api/v1/face
    route:
    - destination:
        host: face-ml-service
        port:
          number: 8082
  - match:
    - uri:
        prefix: /api/v1/crypto
    route:
    - destination:
        host: pqc-crypto-service
        port:
          number: 8086
  - match:
    - uri:
        prefix: /api/v1/zk
    route:
    - destination:
        host: zk-proofs-service
        port:
          number: 8088
```

## Service Dependencies

### Dependency Graph

```
                    ┌─────────────┐
                    │ Edge Gateway│
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │ Auth Service│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────┴───────┐  ┌───────┴───────┐  ┌───────┴───────┐
│ Face ML Svc   │  │ PQC Crypto   │  │ ZK Proofs    │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────┴──────┐
                    │ Quantum RNG │
                    └─────────────┘
```

### Circuit Breakers

| Service | Failure Threshold | Recovery Timeout | Half-Open Requests |
|---------|-------------------|------------------|-------------------|
| Auth Service | 5 consecutive failures | 30s | 3 |
| Face ML | 3 consecutive failures | 60s | 2 |
| PQC Crypto | 5 consecutive failures | 30s | 3 |
| ZK Proofs | 3 consecutive failures | 60s | 2 |
| Quantum RNG | 2 consecutive failures | 120s | 1 |

## Deployment Patterns

### Rolling Updates

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### Blue-Green Deployments

```yaml
# Blue deployment (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service-blue
  labels:
    app: auth-service
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
      version: blue

# Green deployment (new)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service-green
  labels:
    app: auth-service
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
      version: green
```

## Monitoring

### Metrics

| Service | Key Metrics |
|---------|-------------|
| Auth Service | Request rate, error rate, latency, token count |
| Face ML | Inference latency, GPU utilization, accuracy |
| PQC Crypto | Operations/sec, key generation time |
| ZK Proofs | Proof generation time, verification time |
| Quantum RNG | Entropy rate, health status, fallback rate |

### Alerts

```yaml
groups:
- name: cfzt-alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency detected"
      
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Error rate exceeds 5%"
```
