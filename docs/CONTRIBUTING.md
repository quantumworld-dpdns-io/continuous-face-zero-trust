# Contributing to Continuous Face Zero Trust

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone and setup
git clone https://github.com/quantumworld-dpdns-io/continuous-face-zero-trust.git
cd continuous-face-zero-trust
./scripts/dev-setup.sh

# Start all services
docker compose up -d

# Run tests
make test

# Run OWASP security tests
make test-owasp
```

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(auth-api): add continuous verification endpoint
fix(face-ml): correct embedding normalization
quantum(qkd): implement BB84 protocol
security(pqc): add Kyber KEM integration
```

### Allowed Types
`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `quantum`, `security`, `zkp`, `pqc`, `face-ml`, `infra`

### Allowed Scopes
`auth-api`, `face-ml`, `zk-proofs`, `quantum-rng`, `quantum-qkd`, `quantum-ml`, `pqc-crypto`, `cache-store`, `vector-db`, `analytics`, `edge-gateway`, `proto`, `pkg`, `deploy`, `ci`, `docs`, `tests`, `terraform`, `pulumi`, `helm`, `istio`, `observability`

## Pull Request Process

1. Fork the repository
2. Create feature branch from `main`
3. Make changes with clear, descriptive commits
4. Ensure all CI checks pass
5. Add tests for new functionality
6. Update documentation if needed
7. Request review

## Architecture

See [docs/architecture/overview.md](docs/architecture/overview.md) for system architecture.

## Testing

- **Unit tests**: `make test`
- **OWASP security tests**: `make test-owasp`
- **Performance tests**: `make test-performance`
- **Robot Framework**: `robot tests/robot/`

## License

MIT — see [LICENSE](LICENSE)
