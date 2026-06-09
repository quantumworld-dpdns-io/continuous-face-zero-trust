# ZK Circuit Upgrade Procedures

## Overview

This runbook covers upgrading ZK circuits (Groth16, PLONK) for the CFZT system.

## Circuit Types

| Circuit | Purpose | Size | Proving Time | Verification Time |
|---------|---------|------|--------------|-------------------|
| face_matching | Face embedding verification | 200 bytes | 500ms | 10ms |
| liveness_check | Liveness detection proof | 400 bytes | 800ms | 15ms |
| age_verification | Age range proof | 500 bytes | 1000ms | 20ms |
| membership_proof | Group membership | 1.5KB | 2000ms | 50ms |

## Pre-Update Checklist

- [ ] Backup current circuits
- [ ] Test new circuits in staging
- [ ] Generate new trusted setup parameters
- [ ] Update circuit hash registry
- [ ] Notify stakeholders
- [ ] Schedule maintenance window

## Update Procedure

### 1. Backup Current Circuits

```bash
# Backup circuit files
cp -r circuits/ ./backup/circuits-$(date +%Y%m%d)/

# Backup trusted setup parameters
cp -r params/ ./backup/params-$(date +%Y%m%d)/

# Upload to S3
aws s3 sync ./backup/ s3://cfzt-circuits/backup/
```

### 2. Compile New Circuits

```bash
# Compile Noir circuit
cd circuits/face_matching
nargo compile

# Compile ArkWorks circuit
cd circuits/face_matching_arkworks
cargo build --release

# Verify circuit
nargo verify
```

### 3. Generate Trusted Setup

```bash
# Generate new parameters
cargo run --release -- circuit setup \
    --circuit-name face_matching_v2 \
    --output ./params/face_matching_v2.params \
    --entropy "$(qrng generate --bits 256)"

# Contribute to ceremony
cargo run --release -- circuit contribute \
    --circuit-name face_matching_v2 \
    --params ./params/face_matching_v2.params \
    --entropy "$(qrng generate --bits 256)"

# Verify parameters
cargo run --release -- circuit verify \
    --circuit-name face_matching_v2 \
    --params ./params/face_matching_v2.params
```

### 4. Update Circuit Registry

```python
class CircuitRegistry:
    def update_circuit(self, name: str, version: str, circuit_path: str):
        """Update circuit in registry."""
        # Load new circuit
        circuit = self.load_circuit(circuit_path)
        
        # Verify circuit
        if not self.verify_circuit(circuit):
            raise CircuitVerificationError()
        
        # Update registry
        self.registry[name] = {
            "version": version,
            "hash": self.hash_circuit(circuit),
            "params": self.load_params(name, version),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Save registry
        self.save_registry()
```

### 5. Deploy New Circuits

```bash
# Deploy circuit to service
kubectl create configmap zk-circuits \
    --from-file=face_matching_v2=params/face_matching_v2.params \
    -n cfzt \
    --dry-run=client -o yaml | kubectl apply -f -

# Restart ZK proofs service
kubectl rollout restart deployment/zk-proofs-service -n cfzt

# Verify deployment
kubectl get pods -n cfzt -l app=zk-proofs-service
```

### 6. Update Client Libraries

```python
# Update client to use new circuit
from cfzt.zk import ZKClient

client = ZKClient()
client.update_circuit("face_matching", "v2")

# Test new circuit
proof = client.generate_proof(
    circuit="face_matching",
    witness={"embedding": embedding, "stored_hash": hash}
)
```

### 7. Verify Update

```bash
# Test proof generation
curl -X POST http://zk-proofs-service:8089/api/v1/zk/generate \
  -H "Content-Type: application/json" \
  -d '{"circuit": "face_matching_v2", "witness": {...}}'

# Test proof verification
curl -X POST http://zk-proofs-service:8089/api/v1/zk/verify \
  -H "Content-Type: application/json" \
  -d '{"circuit": "face_matching_v2", "proof": {...}}'
```

## Rollback Procedure

### If Update Fails

```bash
# Restore previous circuit files
cp -r ./backup/circuits-$(date +%Y%m%d)/ circuits/

# Restore previous parameters
cp -r ./backup/params-$(date +%Y%m%d)/ params/

# Update circuit registry
python -m cfzt.zk.registry rollback --version previous

# Restart service
kubectl rollout restart deployment/zk-proofs-service -n cfzt
```

## Monitoring

### Key Metrics

```yaml
# ZK circuit metrics
- zk_proof_generate_duration_seconds{circuit, version}
- zk_proof_verify_duration_seconds{circuit, version}
- zk_proof_generate_total{circuit, version}
- zk_proof_verify_total{circuit, version}
- zk_proof_size_bytes{circuit, version}
- zk_circuit_update_total{circuit}
```

### Alerts

```yaml
groups:
- name: zk-circuit-update
  rules:
  - alert: ZKProofGenerationSlow
    expr: histogram_quantile(0.99, rate(zk_proof_generate_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    
  - alert: ZKProofVerificationSlow
    expr: histogram_quantile(0.99, rate(zk_proof_verify_duration_seconds_bucket[5m])) > 0.05
    for: 5m
      severity: warning
```

## Troubleshooting

### Common Issues

#### 1. Circuit Compilation Errors
```bash
# Check Noir version
nargo --version

# Check ArkWorks version
cargo search arkworks

# Clean and rebuild
cargo clean
cargo build --release
```

#### 2. Trusted Setup Failures
```bash
# Check QRNG status
curl -s http://quantum-rng-service:8085/api/v1/quantum/rng/health

# Check entropy
cat /proc/sys/kernel/random/entropy_avail

# Generate entropy manually
qrng generate --bits 256 > /tmp/entropy.bin
```

#### 3. Proof Generation Failures
```bash
# Check witness validity
python -c "from cfzt.zk import verify_witness; verify_witness(witness)"

# Check circuit parameters
python -c "from cfzt.zk import load_params; load_params('face_matching_v2')"
```

## Post-Update

### 1. Verify Recovery
```bash
# Test proof generation
curl -X POST http://zk-proofs-service:8089/api/v1/zk/generate \
  -H "Content-Type: application/json" \
  -d '{"circuit": "face_matching_v2", "witness": {...}}'

# Test proof verification
curl -X POST http://zk-proofs-service:8089/api/v1/zk/verify \
  -H "Content-Type: application/json" \
  -d '{"circuit": "face_matching_v2", "proof": {...}}'
```

### 2. Monitor Metrics
```bash
# Watch ZK circuit metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/zk-circuits
```

### 3. Document Update
- Update circuit documentation
- Update security documentation
- Create update report

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Preparation | 1 day | Backup, test, notify |
| Compilation | 1 day | Compile, verify |
| Trusted Setup | 1 day | Generate, contribute, verify |
| Deployment | 1 hour | Deploy, update registry |
| Verification | 1 hour | Test, monitor |
| **Total** | **3 days** | |

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | ZK team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #zk-circuits
- PagerDuty: ZK Circuit Update Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
