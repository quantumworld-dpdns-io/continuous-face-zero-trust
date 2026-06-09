# Contributing Guide

## Overview

This guide covers contributing to the CFZT system.

## Getting Started

### 1. Fork Repository

```bash
# Fork repository on GitHub
git clone https://github.com/<your-username>/continuous-face-zero-trust.git
cd continuous-face-zero-trust
git remote add upstream https://github.com/cfzt/continuous-face-zero-trust.git
```

### 2. Setup Development Environment

```bash
# Run setup script
./scripts/setup.sh

# Start services
docker-compose up -d

# Verify setup
curl http://localhost:8081/health
```

### 3. Create Branch

```bash
# Create feature branch
git checkout -b feature/my-feature

# Or create bugfix branch
git checkout -b bugfix/my-bugfix
```

## Development Workflow

### 1. Code Style

```bash
# Python
ruff format .
ruff check .

# Go
gofmt -w .
golangci-lint run

# Rust
cargo fmt
cargo clippy
```

### 2. Testing

```bash
# Run unit tests
pytest tests/unit/
go test ./...
cargo test

# Run integration tests
pytest tests/integration/

# Run Robot Framework tests
robot tests/robot/functional/
```

### 3. Commit

```bash
# Stage changes
git add .

# Commit with conventional commits
git commit -m "feat: add new feature"
git commit -m "fix: fix bug"
git commit -m "docs: update documentation"
```

### 4. Push

```bash
# Push to remote
git push origin feature/my-feature
```

### 5. Create Pull Request

```bash
# Create PR
gh pr create --title "feat: add new feature" --body "Adds new feature"

# Or create PR with template
gh pr create --template .github/PULL_REQUEST_TEMPLATE.md
```

## Code Review

### 1. Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance acceptable

### 2. Review Process

1. Create PR
2. Request review from team
3. Address feedback
4. Get approval
5. Merge

## Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Robot Framework tests pass

## Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security issues
```

## Release Process

### 1. Version Bumping

```bash
# Bump version
npm version minor
# Or
python -m bump2version minor
# Or
cargo bump minor
```

### 2. Create Release

```bash
# Create release branch
git checkout -b release/v1.0.0

# Push release branch
git push origin release/v1.0.0

# Create release tag
git tag v1.0.0
git push origin v1.0.0
```

### 3. Deploy Release

```bash
# Deploy to staging
./scripts/deploy-staging.sh

# Deploy to production
./scripts/deploy-production.sh
```

## Issue Templates

### Bug Report

```markdown
## Bug Report

**Describe the bug**
A clear description of the bug

**To reproduce**
Steps to reproduce the behavior

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment**
- OS: [e.g. macOS, Linux]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]

**Additional context**
Add any other context about the problem
```

### Feature Request

```markdown
## Feature Request

**Is your feature request related to a problem?**
A clear description of the problem

**Describe the solution you'd like**
A clear description of what you want to happen

**Describe alternatives you've considered**
A clear description of any alternative solutions

**Additional context**
Add any other context about the feature request
```

## Code Review Checklist

### Security

- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection

### Performance

- [ ] No N+1 queries
- [ ] Proper indexing
- [ ] Caching where appropriate
- [ ] No memory leaks

### Code Quality

- [ ] DRY principle
- [ ] Single responsibility
- [ ] Proper error handling
- [ ] Logging

### Testing

- [ ] Unit tests
- [ ] Integration tests
- [ ] Edge cases covered
- [ ] Error cases covered

## Resources

- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Code Review Best Practices](https://github.com/thomvaill/log4brains/blob/master/docs/contributing/code-review.md)
