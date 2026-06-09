# Continuous Face Zero Trust

> Privacy-preserving continuous face-based zero-trust workspace authentication for remote workers and VDI — quantum-ready, post-quantum secure, ZK-proof verified.

[![CI](https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust/actions/workflows/ci.yml/badge.svg)](https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust/actions/workflows/ci.yml)
[![Security](https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust/actions/workflows/security-owasp.yml/badge.svg)](https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust/actions/workflows/security-owasp.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

This repository implements a **production-grade zero-trust authentication platform** that combines continuous face-based biometric verification with quantum computing, post-quantum cryptography, and zero-knowledge proofs — all deployed as polyglot microservices on an Istio service mesh across multiple cloud providers.

Part of the [quantumworld-dpdns-io](https://github.com/quantumworld-dpdns-io) Wild SaaS & Tech Development initiative.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   CLOUDFLARE EDGE (TypeScript/Hono)              │
│  API Gateway ── Turnstile ── Rate Limiting ── WAF ── WebSocket  │
└────────────────────────┬──────────────────────┬──────────────────┘
                         │ gRPC/REST            │ WS
┌────────────────────────▼──────────────────────▼──────────────────┐
│                   ISTIO SERVICE MESH (mTLS)                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │Auth API │ │ Face ML  │ │ZK Proofs │ │  Quantum Services  │  │
│  │ Python  │ │ Python/  │ │  Rust/   │ │  Qiskit / CUDA-Q   │  │
│  │ FastAPI │ │ ONNX     │ │  Noir    │ │  QRNG / QKD / VQC  │  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────────┬───────────┘  │
│       └───────────┴────────────┴─────────────────┘              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  PQC Crypto │ Redis/DragonflyDB │ Qdrant Vector │ DuckDB  ││
│  │  Kyber/Dilithium/Falcon/SPHINCS+                           ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  OpenTelemetry ── Prometheus ── Grafana ── Jaeger          ││
│  │  W&B Weave ── LangSmith ── Arize Phoenix ── Braintrust    ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
         │ Terraform/Pulumi        │ Helm Charts
         ▼                         ▼
  ┌─────────────┐  ┌──────────────────────────────────────┐
  │ AWS │ GCP │ │  │ EKS │ GKE │ AKS │ K3s │ CF Workers  │
  │ Azure │ CF  │  │ Scaleway │ Exoscale │ Zeabur │ etc.  │
  └─────────────┘  └──────────────────────────────────────┘
```

## Tech Stack

| Component | Language | Framework | Purpose |
|-----------|----------|-----------|---------|
| **Auth API** | Python 3.12 | FastAPI + gRPC | Authentication orchestrator |
| **Face ML** | Python 3.12 | ONNX Runtime + CUDA-Q | Face detection/embedding/liveness |
| **ZK Proofs** | Rust 1.78 | ArkWorks + Noir | Zero-knowledge proof generation |
| **Quantum RNG** | Python 3.12 | Qiskit + CUDA-Q | Quantum true random numbers |
| **Quantum KD** | Python 3.12 | Qiskit | BB84 key distribution |
| **Quantum ML** | Python 3.12 | Qiskit | Variational quantum circuits |
| **PQC Crypto** | Python 3.12 | liboqs | Post-quantum KEM & signatures |
| **Cache Store** | Python 3.12 | DragonflyDB/Redis | Session & token caching |
| **Vector DB** | Python 3.12 | Qdrant | Face embedding storage/search |
| **Analytics** | Python 3.12 | DuckDB + Iceberg | Audit & analytics |
| **Edge Gateway** | TypeScript | Hono/Cloudflare Workers | Edge routing & WAF |
| **Service Mesh** | YAML | Istio | mTLS, traffic management |
| **IaC** | HCL/Python | Terraform + Pulumi | Multi-cloud infrastructure |
| **Tests** | Robot Framework | RF + pytest + cargo test | OWASP Top 10 security tests |
| **CI/CD** | YAML | GitHub Actions | Multi-cloud dispatch |

## Quick Start

```bash
# Clone
git clone https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust.git
cd continuous-face-zero-trust

# One-click dev setup
./scripts/dev-setup.sh

# Start all services
docker compose up -d

# Verify
curl http://localhost:8000/health   # Auth API
curl http://localhost:8001/health   # Face ML
curl http://localhost:8787/health   # Edge Gateway
```

## Services

### Core Services
- **Auth API** (`:8000` / `:50051`) — Authentication, enrollment, session management
- **Face ML** (`:8001` / `:50052`) — ONNX-based face detection, embedding, liveness
- **ZK Proofs** (`:8002` / `:50053`) — Groth16/PLONK/Halo2 proof generation (Rust)
- **PQC Crypto** (`:8006` / `:50055`) — Kyber/Dilithium/FALCON/SPHINCS+

### Quantum Services
- **Quantum RNG** (`:8003`) — Quantum true random number generation
- **Quantum KD** (`:8004`) — BB84 quantum key distribution
- **Quantum ML** (`:8005`) — Variational quantum circuits for embeddings

### Data Services
- **Cache Store** (`:8007`) — Redis/DragonflyDB operations
- **Vector DB** (`:8008`) — Qdrant vector database
- **Analytics** (`:8009`) — DuckDB + Apache Iceberg analytics

### Infrastructure
- **Edge Gateway** (`:8787`) — Cloudflare Workers edge routing
- **Redis** (`:6379`) — Session/token cache (DragonflyDB compatible)
- **Qdrant** (`:6333`) — Face embedding vector storage
- **OTel Collector** (`:4317`) — OpenTelemetry collection
- **Prometheus** (`:9090`) — Metrics scraping
- **Grafana** (`:3000`) — Dashboards
- **Jaeger** (`:16686`) — Distributed tracing

## Quantum Computing Features

### 1. Quantum True Random Number Generation (QRNG)
- Local statevector simulator (free)
- IBM Quantum cloud backend
- CUDA-Q GPU-accelerated simulation
- NIST SP 800-90B entropy validation

### 2. Quantum Key Distribution (QKD)
- BB84 protocol implementation
- SARG04 variant
- Key reconciliation & privacy amplification
- QBER monitoring & alerting

### 3. Quantum Machine Learning
- Variational Quantum Circuit (VQC) embeddings
- Quantum kernel methods
- Hybrid classical+quantum training
- Noise-aware circuit optimization

### 4. Post-Quantum Cryptography
- CRYSTALS-Kyber (ML-KEM) — Key encapsulation
- CRYSTALS-Dilithium (ML-DSA) — Digital signatures
- FALCON — Compact signatures
- SPHINCS+ (SLH-DSA) — Hash-based signatures
- Hybrid classical+PQC modes

### 5. Zero-Knowledge Proofs
- Groth16, PLONK, Halo2, Bulletproofs
- Noir circuit DSL
- Face verification proofs
- Liveness proofs
- Session validity proofs

## Security

### OWASP Top 10 (2021) Coverage
All 10 categories are tested via Robot Framework:
- **A01** — Broken Access Control (IDOR, JWT manipulation, session fixation)
- **A02** — Cryptographic Failures (weak algorithms, key management, PQC readiness)
- **A03** — Injection (SQL, NoSQL, command, SSRF)
- **A04** — Insecure Design (rate limiting, anti-spoofing, business logic)
- **A05** — Security Misconfiguration (headers, error handling, mesh config)
- **A06** — Vulnerable Components (dependency scanning, SBOM, container scanning)
- **A07** — Auth Failures (brute force, face auth bypass, session management)
- **A08** — Data Integrity (CI/CD security, signed artifacts, tampering detection)
- **A09** — Logging Failures (audit logging, suspicious activity, quantum audit)
- **A10** — SSRF (internal network, cloud metadata, webhook abuse)

### Zero-Trust Principles
- Never trust, always verify
- Continuous re-authentication (periodic face verification)
- Device trust scoring
- Session-level risk assessment
- Privacy-preserving: no raw biometric storage

## CI/CD Pipelines

### Automated CI
- **Python**: ruff lint + pytest + typecheck
- **Rust**: clippy + cargo test + rustfmt
- **TypeScript**: biome check + vitest + tsc
- **Go**: golangci-lint + go test
- **Protobuf**: buf lint + breaking change detection
- **Docker**: multi-arch builds with layer caching
- **Security**: bandit + safety + semgrep + trivy + gitleaks

### Releases
- Release Please automation
- PyPI, crates.io, npm, Go module publishing
- Docker multi-arch push (ghcr.io)
- Helm chart publishing
- Sigstore cosign artifact signing
- SBOM generation and attachment

### Multi-Cloud Deployment (Manual Dispatch)
```
cloudflare | aws | gcp | azure | k8s | scaleway | exoscale | zeabur | northflank | vngcloud | selectel | arvancloud | onprem | hybrid
```

## Testing

```bash
# All tests
make test

# OWASP Top 10 security tests
make test-owasp

# Performance tests
make test-performance

# Robot Framework (with HTML reports)
robot --outputdir test-results tests/robot/

# Specific OWASP category
robot tests/robot/owasp/A01_broken_access_control.robot
```

## Development

```bash
# Lint all languages
make lint

# Format all languages
make format

# Build all services
make build

# Run quantum simulations locally
make quantum-sim
```

## Project Structure

```
.
├── services/              # Microservices (polyglot)
│   ├── auth-api/          # Python/FastAPI — authentication
│   ├── face-ml/           # Python/ONNX — face ML pipeline
│   ├── zk-proofs/         # Rust — zero-knowledge proofs
│   ├── quantum-rng/       # Python/Qiskit — quantum RNG
│   ├── quantum-key-exchange/ # Python/Qiskit — QKD
│   ├── quantum-ml/        # Python/Qiskit — quantum ML
│   ├── quantum-cudaq/     # Python/CUDA-Q — GPU quantum
│   ├── pqc-crypto/        # Python — post-quantum crypto
│   ├── cache-store/       # Python — Redis operations
│   ├── vector-db/         # Python — Qdrant operations
│   ├── analytics/         # Python — DuckDB/Iceberg
│   └── edge-gateway/      # TypeScript/Hono — CF Workers
├── pkg/                   # Shared libraries
│   ├── python/            # Shared Python package (cfzt)
│   ├── rust/              # Shared Rust crate
│   ├── ts/                # Shared TypeScript package
│   └── go/                # Shared Go module
├── proto/                 # gRPC/Protobuf contracts
├── deploy/                # Deployment manifests
│   ├── k8s/               # Kubernetes (Kustomize)
│   ├── istio/             # Istio service mesh
│   └── helm/              # Helm charts
├── infra/                 # Infrastructure as Code
│   ├── terraform/         # Terraform (multi-cloud)
│   ├── pulumi/            # Pulumi (Python)
│   └── dispatch/          # Cloud dispatch configs
├── tests/                 # Test suites
│   ├── robot/             # Robot Framework
│   │   ├── owasp/         # OWASP Top 10 tests
│   │   ├── functional/    # Functional tests
│   │   └── performance/   # Performance tests
│   └── ...                # pytest/cargo test/vitest
├── observability/         # Monitoring & observability
│   ├── otel/              # OpenTelemetry config
│   ├── prometheus/        # Prometheus + alerts
│   ├── grafana/           # Grafana dashboards
│   ├── ai/                # AI observability (W&B, Phoenix)
│   └── security/          # Security monitoring
├── docker/                # Dockerfiles
├── docs/                  # Documentation
│   ├── architecture/      # Architecture decisions (ADRs)
│   ├── api/               # OpenAPI specs
│   ├── guides/            # Developer guides
│   └── runbooks/          # Operations runbooks
├── .github/workflows/     # CI/CD pipelines
├── PLAN.md                # Master plan (1050 todos)
├── SECURITY.md            # Security policy
├── CONTRIBUTING.md        # Contributing guide
└── Makefile               # Build/test/lint targets
```

## Deployment

### Docker Compose (Local)
```bash
docker compose up -d
```

### Kubernetes (Production)
```bash
kubectl apply -k deploy/k8s/
```

### Helm
```bash
helm install cfzt deploy/helm/cfzt/ -f deploy/helm/cfzt/values-production.yaml
```

### Multi-Cloud (via GitHub Actions)
1. Go to Actions → Deploy
2. Select cloud provider (AWS/GCP/Azure/Cloudflare/etc.)
3. Select environment (dev/staging/production)
4. Toggle quantum services
5. Run workflow

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Security Model](docs/architecture/security-model.md)
- [Quantum Integration](docs/architecture/quantum-integration.md)
- [API Specifications](docs/api/)
- [Developer Guides](docs/guides/)
- [Operations Runbooks](docs/runbooks/)

## License

[MIT](LICENSE)

---

> Built with love by [quantumworld-dpdns-io](https://github.com/quantumworld-dpdns-io) | Privacy-first | Quantum-ready | Post-quantum secure
