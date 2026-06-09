# Architecture Overview

## System Architecture

The Continuous Face Zero Trust (CFZT) platform is a polyglot microservices system implementing privacy-preserving continuous face-based authentication with quantum computing integration.

## Service Architecture

```
                    ┌─────────────────────────┐
                    │    Cloudflare Edge       │
                    │  (TypeScript / Hono)     │
                    │  ┌───────┐ ┌──────────┐ │
                    │  │ WAF   │ │ Turnstile │ │
                    │  └───────┘ └──────────┘ │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Istio Service Mesh     │
                    │   (mTLS everywhere)      │
                    │                          │
    ┌───────────────┼──────────────────────────┼───────────────┐
    │               │                          │               │
    │  ┌────────────▼──────┐  ┌───────────────▼────┐         │
    │  │    Auth API       │  │     Face ML        │         │
    │  │  Python/FastAPI   │◄─┤  Python/ONNX       │         │
    │  │  :8000 / :50051   │  │  :8001 / :50052    │         │
    │  └────────┬──────────┘  └────────────────────┘         │
    │           │                                             │
    │  ┌────────▼──────────┐  ┌────────────────────┐         │
    │  │    ZK Proofs      │  │  Quantum Services  │         │
    │  │  Rust/ArkWorks    │  │  Qiskit / CUDA-Q   │         │
    │  │  :8002 / :50053   │  │  :8003-8005        │         │
    │  └───────────────────┘  └────────────────────┘         │
    │                                                         │
    │  ┌───────────────────┐  ┌────────────────────┐         │
    │  │    PQC Crypto     │  │   Cache Store      │         │
    │  │  Python/liboqs    │  │   DragonflyDB      │         │
    │  │  :8006 / :50055   │  │   :8007 / :6379    │         │
    │  └───────────────────┘  └────────────────────┘         │
    │                                                         │
    │  ┌───────────────────┐  ┌────────────────────┐         │
    │  │    Vector DB      │  │    Analytics       │         │
    │  │  Qdrant           │  │  DuckDB + Iceberg  │         │
    │  │  :8008 / :6333    │  │  :8009             │         │
    │  └───────────────────┘  └────────────────────┘         │
    └─────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Observability         │
                    │  OTel / Prometheus /     │
                    │  Grafana / Jaeger /      │
                    │  W&B Weave / Phoenix     │
                    └─────────────────────────┘
```

## Data Flow

### Authentication Flow
1. Client sends face image to Edge Gateway
2. Edge Gateway applies WAF + Turnstile + rate limiting
3. Request forwarded to Auth API via gRPC
4. Auth API calls Face ML for embedding + liveness
5. Auth API calls ZK Proofs for verification proof
6. Auth API calls Quantum RNG for session key
7. Auth API calls PQC Crypto for post-quantum token signing
8. Session stored in Redis, embeddings in Qdrant
9. Tokens returned to client

### Continuous Verification Flow
1. Client periodically sends face frames via WebSocket
2. Face ML compares against stored embedding
3. If drift detected, session flagged
4. ZK proof generated for audit trail
5. Risk score recalculated
6. Session terminated if risk exceeds threshold

## Security Layers

1. **Network**: Istio mTLS, NetworkPolicies, WAF
2. **Identity**: JWT + PASETO tokens, continuous verification
3. **Biometric**: Liveness detection, anti-spoofing, embedding matching
4. **Quantum**: QRNG for keys, QKD for key exchange
5. **Post-Quantum**: Kyber KEM, Dilithium signatures
6. **Zero-Knowledge**: Proofs without revealing raw biometrics
7. **Privacy**: No raw images stored, differential privacy, embedding-only
