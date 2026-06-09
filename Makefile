.PHONY: help lint test build deploy quantum-sim format check-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: lint-python lint-rust lint-ts lint-go ## Run all linters

lint-python:
	@echo "==> Linting Python..."
	ruff check services/ pkg/python/
	ruff format --check services/ pkg/python/

lint-rust:
	@echo "==> Linting Rust..."
	cd services/zk-proofs && cargo clippy -- -D warnings
	cd pkg/rust && cargo clippy -- -D warnings

lint-ts:
	@echo "==> Linting TypeScript..."
	cd services/edge-gateway && npx biome check src/

lint-go:
	@echo "==> Linting Go..."
	cd pkg/go && golangci-lint run ./...

format: format-python format-rust format-ts ## Run all formatters

format-python:
	ruff format services/ pkg/python/

format-rust:
	cd services/zk-proofs && cargo fmt
	cd pkg/rust && cargo fmt

format-ts:
	cd services/edge-gateway && npx biome format --write src/

test: test-python test-rust test-ts test-go test-robot ## Run all tests

test-python:
	python -m pytest tests/ services/*/tests/ -x --tb=short

test-rust:
	cd services/zk-proofs && cargo test
	cd pkg/rust && cargo test

test-ts:
	cd services/edge-gateway && npx vitest run

test-go:
	cd pkg/go && go test ./...

test-robot:
	robot --outputdir test-results tests/robot/

test-owasp:
	robot --outputdir test-results/owasp tests/robot/owasp/

test-security: test-owasp ## Run OWASP Top 10 security tests

test-performance:
	robot --outputdir test-results/perf tests/robot/performance/

build: build-services build-docker ## Build all services

build-services:
	@echo "==> Building all services..."
	$(MAKE) -C services/auth-api build
	$(MAKE) -C services/face-ml build
	$(MAKE) -C services/zk-proofs build
	$(MAKE) -C services/quantum-rng build
	$(MAKE) -C services/pqc-crypto build

build-docker:
	docker compose build

quantum-sim: ## Run quantum simulations locally
	@echo "==> Running quantum simulations..."
	python -m services.quantum_rng.app.rng.local_simulator

deploy: ## Deploy to configured target
	@echo "==> Deploying..."
	./scripts/deploy.sh

check-all: lint test ## Run all checks
	@echo "==> All checks passed!"
