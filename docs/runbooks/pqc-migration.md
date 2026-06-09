# PQC Migration Step-by-Step Guide

## Overview

This runbook provides step-by-step instructions for migrating from classical cryptography to post-quantum cryptography.

## Pre-Migration Checklist

- [ ] Backup all cryptographic keys
- [ ] Verify PQC library versions
- [ ] Test PQC algorithms in staging
- [ ] Update client libraries
- [ ] Notify stakeholders
- [ ] Schedule maintenance window

## Migration Phases

### Phase 1: Preparation (1 week)

#### 1.1 Backup Current Keys
```bash
# Backup classical keys
aws s3 cp s3://cfzt-keys/classical/ ./backup/classical/ --recursive

# Backup to secondary cloud
gsutil -m cp -r ./backup/classical/ gs://cfzt-keys-backup/classical/
```

#### 1.2 Verify PQC Libraries
```bash
# Check liboqs version
cargo search liboqs-rust

# Check Kyber implementation
cargo test --release kyber

# Check Dilithium implementation
cargo test --release dilithium
```

#### 1.3 Test in Staging
```bash
# Deploy to staging
kubectl apply -f k8s/staging/

# Run PQC tests
cargo test --release --features pqc

# Run integration tests
pytest tests/integration/test_pqc.py
```

### Phase 2: Hybrid Mode (2 weeks)

#### 2.1 Enable Hybrid Key Exchange
```rust
// Update key exchange configuration
let config = KeyExchangeConfig {
    classical: Some(X25519Config::default()),
    pqc: Some(KyberConfig::new(KyberVariant::Kyber1024)),
    mode: HybridMode::BothRequired,
};
```

#### 2.2 Enable Hybrid Signatures
```rust
// Update signature configuration
let config = SignatureConfig {
    classical: Some(Ed25519Config::default()),
    pqc: Some(DilithiumConfig::new(DilithiumVariant::Dilithium5)),
    mode: HybridMode::BothRequired,
};
```

#### 2.3 Update Certificate Chain
```bash
# Generate PQC certificates
cfzt-cli certificate generate \
  --algorithm kyber-1024 \
  --validity 90d \
  --output /etc/certs/pqc.pem

# Update Istio certificates
kubectl create secret generic pqc-certs \
  --from-file=tls.crt=/etc/certs/pqc.pem \
  --from-file=tls.key=/etc/certs/pqc-key.pem \
  -n cfzt
```

#### 2.4 Deploy Hybrid Services
```bash
# Deploy PQC crypto service
kubectl apply -f k8s/pqc-crypto/

# Verify service is running
kubectl get pods -n cfzt -l app=pqc-crypto-service

# Test PQC operations
curl -X POST http://pqc-crypto-service:8087/api/v1/crypto/kem/encapsulate \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "kyber-1024"}'
```

### Phase 3: PQC Primary (4 weeks)

#### 3.1 Switch to PQC Primary
```rust
// Update configuration to PQC primary
let config = KeyExchangeConfig {
    classical: Some(X25519Config::default()),
    pqc: Some(KyberConfig::new(KyberVariant::Kyber1024)),
    mode: HybridMode::PQCPrimary,
};
```

#### 3.2 Monitor Performance
```bash
# Watch PQC metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/pqc-migration

# Monitor latency
curl -s http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99,sum(rate(pqc_keygen_duration_seconds_bucket[5m]))by(le))
```

#### 3.3 Validate Security
```bash
# Run security scans
trivy image pqc-crypto-service:latest

# Run Penetration tests
pytest tests/security/test_pqc.py

# Check for vulnerabilities
cargo audit
```

### Phase 4: PQC Only (2 weeks)

#### 4.1 Remove Classical Algorithms
```rust
// Update configuration to PQC only
let config = KeyExchangeConfig {
    classical: None,
    pqc: Some(KyberConfig::new(KyberVariant::Kyber1024)),
    mode: HybridMode::PQCOnly,
};
```

#### 4.2 Update Client Libraries
```python
# Python client
from cfzt import PQCClient

client = PQCClient(algorithm="kyber-1024")
shared_secret = client.exchange_key(server_public_key)
```

```go
// Go client
import "github.com/cfzt/pqc-go"

client := pqc.NewClient(pqc.Kyber1024)
sharedSecret, err := client.ExchangeKey(serverPublicKey)
```

#### 4.3 Final Validation
```bash
# Run full test suite
pytest tests/

# Run performance tests
robot tests/robot/performance/

# Run security tests
robot tests/robot/security/
```

## Rollback Procedure

### If Issues Occur

#### 1. Immediate Rollback
```bash
# Revert to classical algorithms
kubectl patch configmap pqc-config -n cfzt --type=merge -p '{"data":{"mode":"classical"}}'

# Restart services
kubectl rollout restart deployment/pqc-crypto-service -n cfzt
```

#### 2. Partial Rollback
```bash
# Revert to hybrid mode
kubectl patch configmap pqc-config -n cfzt --type=merge -p '{"data":{"mode":"hybrid"}}'

# Restart services
kubectl rollout restart deployment/pqc-crypto-service -n cfzt
```

#### 3. Full Rollback
```bash
# Restore classical keys
aws s3 cp s3://cfzt-keys/classical/ /etc/certs/ --recursive

# Revert all configurations
git checkout main -- k8s/

# Apply classical configuration
kubectl apply -f k8s/classical/
```

## Monitoring

### Key Metrics
```yaml
# PQC metrics to watch
- pqc_keygen_duration_seconds
- pqc_encapsulate_duration_seconds
- pqc_sign_duration_seconds
- pqc_verify_duration_seconds
- pqc_hybrid_operations_total
- pqc_fallback_total
```

### Alerts
```yaml
groups:
- name: pqc-migration
  rules:
  - alert: PQCLatencyHigh
    expr: histogram_quantile(0.99, rate(pqc_keygen_duration_seconds_bucket[5m])) > 0.05
    for: 5m
    labels:
      severity: warning
    
  - alert: PQCFallbackHigh
    expr: rate(pqc_fallback_total[5m]) > 10
    for: 5m
    labels:
      severity: warning
```

## Troubleshooting

### Common Issues

#### 1. Key Generation Failures
```bash
# Check liboqs
cargo test --release kyber

# Check entropy
cat /proc/sys/kernel/random/entropy_avail
```

#### 2. Performance Issues
```bash
# Profile PQC operations
cargo bench --release

# Check CPU usage
top -p $(pgrep -d, pqc-crypto)
```

#### 3. Compatibility Issues
```bash
# Check client version
cfzt-cli version

# Check protocol version
curl -s http://pqc-crypto-service:8087/api/v1/crypto/algorithms | jq .
```

## Post-Migration

### 1. Verify Recovery
```bash
# Test PQC operations
curl -X POST http://pqc-crypto-service:8087/api/v1/crypto/kem/encapsulate \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "kyber-1024"}'

# Test signing
curl -X POST http://pqc-crypto-service:8087/api/v1/crypto/sign \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "dilithium-5", "message": "test"}'
```

### 2. Monitor Metrics
```bash
# Watch PQC metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/pqc-migration
```

### 3. Document Migration
- Update architecture documentation
- Update security documentation
- Create migration report
- Schedule post-mortem

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Preparation | 1 week | Backup, test, notify |
| Hybrid Mode | 2 weeks | Deploy, monitor, validate |
| PQC Primary | 4 weeks | Switch, monitor, validate |
| PQC Only | 2 weeks | Remove classical, validate |
| **Total** | **9 weeks** | |

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Security team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #pqc-migration
- PagerDuty: PQC Migration Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
