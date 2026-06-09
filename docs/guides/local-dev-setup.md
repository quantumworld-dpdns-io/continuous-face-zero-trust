# Local Development Setup Guide

## Overview

This guide covers setting up a local development environment for the CFZT system.

## Prerequisites

- macOS/Linux (Windows via WSL2)
- Docker Desktop 4.0+
- Kubernetes (minikube or kind)
- Python 3.10+
- Go 1.21+
- Rust 1.70+
- Node.js 18+
- Java 17+ (for Kafka)

## Quick Start

```bash
# Clone repository
git clone https://github.com/cfzt/continuous-face-zero-trust.git
cd continuous-face-zero-trust

# Run setup script
./scripts/setup.sh

# Start services
docker-compose up -d

# Verify setup
curl http://localhost:8081/health
```

## Detailed Setup

### 1. Install Dependencies

```bash
# macOS
brew install docker kubernetes-cli kustomize helm istioctl
brew install python@3.10 go rust node java

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose kubectl kustomize helm
sudo snap install go --classic
sudo snap install rust --classic
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Configure Docker

```bash
# Start Docker Desktop
open -a Docker

# Verify Docker
docker --version
docker-compose --version
```

### 3. Configure Kubernetes

```bash
# Start minikube
minikube start --cpus 4 --memory 8192 --driver docker

# Or start kind
kind create cluster --name cfzt --config kind-config.yaml

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### 4. Install Istio

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Install Istio
istioctl install --set profile=demo

# Enable sidecar injection
kubectl label namespace default istio-injection=enabled
```

### 5. Start Infrastructure

```bash
# Start Redis
kubectl apply -f k8s/infrastructure/redis.yaml

# Start CockroachDB
kubectl apply -f k8s/infrastructure/cockroachdb.yaml

# Start Qdrant
kubectl apply -f k8s/infrastructure/qdrant.yaml

# Start Kafka
kubectl apply -f k8s/infrastructure/kafka.yaml

# Verify infrastructure
kubectl get pods -n cfzt
```

### 6. Build Services

```bash
# Build Auth Service (Go)
cd services/auth-service
go build -o bin/auth-service ./cmd/server

# Build Face ML Service (Python)
cd services/face-ml-service
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8083

# Build PQC Crypto Service (Rust)
cd services/pqc-crypto-service
cargo build --release

# Build ZK Proofs Service (Rust)
cd services/zk-proofs-service
cargo build --release

# Build Quantum RNG Service (Python)
cd services/quantum-rng-service
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8085
```

### 7. Start Services

```bash
# Start all services
docker-compose up -d

# Or start individually
docker-compose up -d auth-service
docker-compose up -d face-ml-service
docker-compose up -d pqc-crypto-service
docker-compose up -d zk-proofs-service
docker-compose up -d quantum-rng-service

# Verify services
kubectl get pods -n cfzt
curl http://localhost:8081/health
curl http://localhost:8083/health
curl http://localhost:8087/health
curl http://localhost:8089/health
curl http://localhost:8085/health
```

### 8. Run Tests

```bash
# Run unit tests
pytest tests/unit/
go test ./...
cargo test

# Run integration tests
pytest tests/integration/

# Run Robot Framework tests
robot tests/robot/functional/

# Run performance tests
robot tests/robot/performance/
```

## IDE Configuration

### VS Code

```json
{
  "recommendations": [
    "golang.go",
    "ms-python.python",
    "rust-lang.rust-analyzer",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint"
  ]
}
```

### IntelliJ IDEA

1. Install Go plugin
2. Install Python plugin
3. Install Rust plugin
4. Configure Docker plugin
5. Configure Kubernetes plugin

## Debugging

### Go Service

```bash
# Debug with Delve
dlv debug ./cmd/server

# Attach to running process
dlv attach <pid>
```

### Python Service

```bash
# Debug with pdb
python -m pdb -m uvicorn main:app --reload --port 8083

# Debug with VS Code
# Add launch.json configuration
```

### Rust Service

```bash
# Debug with lldb
rust-lldb target/release/pqc-crypto-service

# Debug with VS Code
# Add launch.json configuration
```

## Common Issues

### Docker Issues

```bash
# Reset Docker
docker system prune -a
docker volume prune

# Restart Docker Desktop
open -a Docker --wait
```

### Kubernetes Issues

```bash
# Reset minikube
minikube delete
minikube start

# Reset kind
kind delete cluster --name cfzt
kind create cluster --name cfzt --config kind-config.yaml
```

### Port Conflicts

```bash
# Check port usage
lsof -i :8081
lsof -i :8083
lsof -i :8087

# Kill process on port
kill -9 <pid>
```

## Environment Variables

```bash
# Database
export COCKROACHDB_HOST=localhost
export COCKROACHDB_PORT=26257
export COCKROACHDB_USER=root
export COCKROACHDB_PASSWORD=

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Kafka
export KAFKA_BROKERS=localhost:9092

# Qdrant
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# Quantum RNG
export QRNG_HOST=localhost
export QRNG_PORT=8085

# PQC Crypto
export PQC_HOST=localhost
export PQC_PORT=8087

# ZK Proofs
export ZK_HOST=localhost
export ZK_PORT=8089
```

## Documentation

- [Architecture Overview](../architecture/overview.md)
- [API Documentation](../api/)
- [Runbooks](../runbooks/)
- [Contributing Guide](CONTRIBUTING-UPDATED.md)
