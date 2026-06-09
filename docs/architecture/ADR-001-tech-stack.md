# ADR-001: Technology Stack Selection

## Status

Accepted

## Context

We need to select technologies for the Continuous Face Zero-Trust system that balance performance, security, developer productivity, and ecosystem support.

## Decision

### Backend Services

| Service | Language | Framework | Rationale |
|---------|----------|-----------|-----------|
| Auth Service | Go | Gin/gRPC | High concurrency, excellent gRPC support |
| Face ML | Python | FastAPI | ML ecosystem (PyTorch, ONNX), async support |
| PQC Crypto | Rust | Tonic | Memory safety, performance, liboqs bindings |
| ZK Proofs | Rust | Tonic | ArkWorks ecosystem, performance |
| Quantum RNG | Python | FastAPI | Qiskit/CUDA-Q integration |
| Vector DB | Go | gRPC wrapper | Performance, Qdrant client |
| Cache Store | Go | gRPC | Redis client performance |
| Analytics | Python | Polars/DuckDB | Data processing ecosystem |

### Frontend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Web App | React + TypeScript | Type safety, ecosystem |
| Mobile App | React Native | Cross-platform, code sharing |
| Edge Gateway | Cloudflare Workers | Global edge, low latency |

### Infrastructure

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Container Orchestration | Kubernetes (EKS/GKE/AKS) | Multi-cloud portability |
| Service Mesh | Istio | mTLS, traffic management, observability |
| Message Queue | Apache Kafka | Event streaming, durability |
| Primary Database | CockroachDB | Distributed SQL, multi-region |
| Cache | Redis Cluster | Performance, pub/sub |
| Vector DB | Qdrant | Performance, filtering |
| Object Storage | S3/GCS/Azure Blob | Durability, cost |

### Security

| Component | Technology | Rationale |
|-----------|------------|-----------|
| PQC Algorithms | Kyber, Dilithium, FALCON | NIST standardized |
| ZK Proofs | Groth16/PLONK via ArkWorks | Performance, ecosystem |
| Key Management | AWS KMS / GCP Cloud KMS | HSM backing, compliance |
| Certificate Management | cert-manager + Let's Encrypt | Automation, cost |

### Observability

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Metrics | Prometheus + Grafana | Industry standard |
| Logging | Fluentd + Elasticsearch | Scalability |
| Tracing | Jaeger + OpenTelemetry | Distributed tracing |
| Alerting | Alertmanager + PagerDuty | Integration |

## Consequences

### Positive
- Go provides excellent performance for high-concurrency auth service
- Python enables rapid ML development and experimentation
- Rust ensures memory safety for cryptographic operations
- Multi-cloud strategy provides redundancy and compliance

### Negative
- Multiple languages increase operational complexity
- Need expertise across Go, Python, Rust
- Cross-language gRPC requires careful schema management
- Multi-cloud increases infrastructure costs

### Risks
- Rust ecosystem for PQC is maturing but not as mature as C
- Python GIL may limit Face ML throughput
- Istio adds latency overhead (~1ms per hop)
- Kafka operational complexity

## Alternatives Considered

### All-Go Stack
- Pros: Single language, excellent performance
- Cons: ML ecosystem limitations, slower development

### All-Rust Stack
- Pros: Maximum performance, memory safety
- Cons: Steeper learning curve, smaller ecosystem

### Node.js/TypeScript
- Pros: Full-stack TypeScript, rapid development
- Cons: Performance limitations, ML ecosystem gaps

## Review Date

2025-01-01
