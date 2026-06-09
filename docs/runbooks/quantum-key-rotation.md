# Quantum Key Rotation

## Overview

This runbook covers key rotation for quantum cryptographic keys (QKD keys, QRNG-derived keys).

## Key Types

| Key Type | Source | Rotation Period | Storage |
|----------|--------|-----------------|---------|
| QKD Key | Quantum Channel | 60 seconds | HSM |
| QRNG Seed | Hardware QRNG | Daily | HSM |
| Quantum-Derived Session Key | QKD + QRNG | Per-session | Redis |
| Quantum-Derived DEK | QKD | Monthly | KMS |

## Pre-Rotation Checklist

- [ ] Verify QRNG hardware status
- [ ] Check QKD channel health
- [ ] Backup current quantum keys
- [ ] Test new key generation
- [ ] Notify stakeholders

## QKD Key Rotation

### 1. QKD Key Exchange

```python
class QKDKeyRotator:
    def __init__(self):
        self.qkd_client = QKDClient()
        self.hsm = HSMClient()
    
    def rotate_qkd_key(self):
        """Rotate QKD key via quantum channel."""
        # Exchange new key via QKD
        new_key = self.qkd_client.exchange_key()
        
        # Verify key integrity
        if not self.verify_key(new_key):
            raise KeyIntegrityError()
        
        # Store in HSM
        self.hsm.store_key("qkd-current", new_key)
        
        # Update services
        self.update_services(new_key)
        
        # Archive old key
        self.archive_old_key()
```

### 2. QKD Key Verification

```python
def verify_qkd_key(self, key: bytes) -> bool:
    """Verify QKD key integrity."""
    # Check key length
    if len(key) != 256:  # 256-bit key
        return False
    
    # Check entropy
    entropy = self.calculate_entropy(key)
    if entropy < 0.95:  # Min-entropy threshold
        return False
    
    # Check for known biases
    if self.has_bias(key):
        return False
    
    return True
```

### 3. QKD Key Distribution

```python
class QKDKeyDistributor:
    def distribute_key(self, key: bytes):
        """Distribute QKD key to services."""
        services = [
            "auth-service",
            "face-ml-service",
            "pqc-crypto-service",
            "zk-proofs-service",
        ]
        
        for service in services:
            # Distribute via secure channel
            self.distribute_to_service(service, key)
            
            # Verify distribution
            if not self.verify_distribution(service, key):
                raise KeyDistributionError(service)
```

## QRNG Key Rotation

### 1. QRNG Seed Rotation

```python
class QRNGSeedRotator:
    def rotate_seed(self):
        """Rotate QRNG seed."""
        # Generate new seed from hardware QRNG
        new_seed = self.qrng.generate(bits=256)
        
        # Verify seed quality
        if not self.verify_seed(new_seed):
            raise SeedQualityError()
        
        # Store in HSM
        self.hsm.store_seed("qrng-seed", new_seed)
        
        # Update QRNG service
        self.update_qrng_service(new_seed)
        
        # Archive old seed
        self.archive_old_seed()
```

### 2. QRNG Seed Verification

```python
def verify_seed(self, seed: bytes) -> bool:
    """Verify QRNG seed quality."""
    # Run NIST 800-90B tests
    tests = [
        self.frequency_monobit,
        self.frequency_block,
        self.cumulative_sum,
        self.longest_run,
        self.serial_correlation,
        self.approximate_entropy,
    ]
    
    for test in tests:
        if not test(seed):
            return False
    
    return True
```

## Quantum-Derived Key Rotation

### 1. Session Key Rotation

```python
class QuantumSessionKeyRotator:
    def rotate_session_key(self, session_id: str):
        """Rotate session key using quantum randomness."""
        # Get QKD key
        qkd_key = self.qkd.get_current_key()
        
        # Get QRNG entropy
        qrng_entropy = self.qrng.generate(bits=256)
        
        # Derive session key
        session_key = self.derive_key(qkd_key, qrng_entropy)
        
        # Store session key
        self.store_session_key(session_id, session_key)
        
        # Update session
        self.update_session(session_id, session_key)
```

### 2. DEK Rotation

```python
class QuantumDEKRotator:
    def rotate_dek(self):
        """Rotate DEK using quantum randomness."""
        # Get QKD key
        qkd_key = self.qkd.get_current_key()
        
        # Get QRNG entropy
        qrng_entropy = self.qrng.generate(bits=256)
        
        # Derive DEK
        dek = self.derive_dek(qkd_key, qrng_entropy)
        
        # Re-encrypt data
        self.reencrypt_data(dek)
        
        # Store new DEK
        self.store_dek(dek)
        
        # Archive old DEK
        self.archive_old_dek()
```

## Automated Rotation

### CronJob for Quantum Key Rotation

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: quantum-key-rotation
  namespace: cfzt
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes for QKD
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: quantum-key-rotation
            image: cfzt/quantum-key-rotation:latest
            command:
            - /bin/sh
            - -c
            - |
              # Rotate QKD key
              python -m cfzt.quantum.rotate_qkd
              
              # Rotate QRNG seed (daily)
              if [ $(date +%H) -eq 0 ] && [ $(date +%M) -eq 0 ]; then
                python -m cfzt.quantum.rotate_seed
              fi
            env:
            - name: QKD_ENDPOINT
              value: "qkd-trust-node.cfzt.io:443"
            - name: QRNG_ENDPOINT
              value: "qrng-service:8084"
          restartPolicy: OnFailure
```

### Rotation Script

```python
#!/usr/bin/env python
"""Quantum key rotation script."""

import argparse
import logging
from cfzt.quantum import QKDKeyRotator, QRNGSeedRotator

def main():
    parser = argparse.ArgumentParser(description="Rotate quantum keys")
    parser.add_argument("--key-type", required=True, choices=["qkd", "seed", "all"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if args.key_type == "qkd" or args.key_type == "all":
        logger.info("Rotating QKD key...")
        if not args.dry_run:
            rotator = QKDKeyRotator()
            rotator.rotate_qkd_key()
    
    if args.key_type == "seed" or args.key_type == "all":
        logger.info("Rotating QRNG seed...")
        if not args.dry_run:
            rotator = QRNGSeedRotator()
            rotator.rotate_seed()
    
    logger.info("Quantum key rotation complete")

if __name__ == "__main__":
    main()
```

## Monitoring

### Key Metrics

```yaml
# Quantum key rotation metrics
- qkd_key_rotation_success_total
- qkd_key_rotation_failure_total
- qkd_key_age_seconds
- qrng_seed_rotation_success_total
- qrng_seed_rotation_failure_total
- qrng_seed_age_seconds
- quantum_key_entropy_bits
```

### Alerts

```yaml
groups:
- name: quantum-key-rotation
  rules:
  - alert: QKDKeyRotationFailed
    expr: rate(qkd_key_rotation_failure_total[5m]) > 0
    for: 5m
    labels:
      severity: critical
    
  - alert: QKDKeyAgeHigh
    expr: qkd_key_age_seconds > 120
    for: 5m
    labels:
      severity: warning
    
  - alert: QRNGSeedAgeHigh
    expr: qrng_seed_age_seconds > 86400
    for: 5m
    labels:
      severity: warning
    
  - alert: QuantumKeyEntropyLow
    expr: quantum_key_entropy_bits < 0.95
    for: 5m
    labels:
      severity: critical
```

## Rollback

### If Rotation Fails

```bash
# Restore previous QKD key
kubectl exec -it hsm-0 -n cfzt -- hsm-cli restore-key qkd-previous

# Restore previous QRNG seed
kubectl exec -it hsm-0 -n cfzt -- hsm-cli restore-seed qrng-previous

# Restart services
kubectl rollout restart deployment -n cfzt
```

## Post-Rotation

### 1. Verify Recovery
```bash
# Test QKD key exchange
curl -X POST http://quantum-rng-service:8085/api/v1/quantum/qkd/exchange \
  -H "Content-Type: application/json" \
  -d '{"key_size": 256}'

# Test QRNG generation
curl -X POST http://quantum-rng-service:8085/api/v1/quantum/rng/generate \
  -H "Content-Type: application/json" \
  -d '{"num_bits": 256}'
```

### 2. Monitor Metrics
```bash
# Watch quantum key rotation metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/quantum-keys
```

### 3. Document Rotation
- Update key inventory
- Update security documentation
- Create rotation report

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Quantum team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #quantum-keys
- PagerDuty: Quantum Key Rotation Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
