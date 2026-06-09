#!/bin/bash
set -euo pipefail

echo "=== Continuous Face Zero Trust — Development Setup ==="

echo "[1/6] Checking tool versions..."
command -v python3 >/dev/null 2>&1 || { echo "Python 3.12+ required"; exit 1; }
command -v cargo >/dev/null 2>&1 || { echo "Rust toolchain required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 22+ required"; exit 1; }
command -v go >/dev/null 2>&1 || { echo "Go 1.22+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }

echo "[2/6] Installing Python dependencies..."
pip install -e "pkg/python/[dev]" 2>/dev/null || true
pip install ruff pre-commit robotframework robotframework-requests

echo "[3/6] Installing Rust dependencies..."
cd services/zk-proofs && cargo fetch && cd ../..
cd pkg/rust && cargo fetch && cd ../..

echo "[4/6] Installing Node.js dependencies..."
cd services/edge-gateway && npm install && cd ../..

echo "[5/6] Installing Go dependencies..."
cd pkg/go && go mod download && cd ../..

echo "[6/6] Setting up pre-commit hooks..."
pre-commit install 2>/dev/null || true

echo ""
echo "=== Setup Complete ==="
echo "Run 'docker compose up -d' to start all services"
echo "Run 'make test' to run all tests"
echo "Run 'make test-owasp' to run OWASP security tests"
