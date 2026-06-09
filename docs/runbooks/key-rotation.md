# Key Rotation Procedures

## Overview

This runbook covers key rotation for both classical and post-quantum cryptographic keys.

## Key Types

| Key Type | Algorithm | Rotation Period | Storage |
|----------|-----------|-----------------|---------|
| Master Key | AES-256 | Annual | HSM |
| DEK | AES-256-GCM | Monthly | KMS |
| KEK | RSA-4096 | Quarterly | KMS |
| Session Key | X25519 | Per-session | Redis |
| PQC Key | Kyber-1024 | Quarterly | KMS |
| PQC Signature | Dilithium-5 | Quarterly | KMS |

## Pre-Rotation Checklist

- [ ] Backup current keys
- [ ] Verify new key generation
- [ ] Test decryption with new keys
- [ ] Notify stakeholders
- [ ] Schedule maintenance window

## Classical Key Rotation

### 1. AWS KMS Key Rotation

```bash
# Enable automatic rotation
aws kms enable-key-rotation --key-id <key-id>

# Manual rotation
aws kms create-key --description "New master key"
aws kms create-alias --alias-name alias/cfzt-master-new --target-key-id <new-key-id>
aws kms update-alias --alias-name alias/cfzt-master --target-key-id <new-key-id>
```

### 2. Database Key Rotation

```python
class KeyRotator:
    def rotate_database_keys(self):
        """Rotate database encryption keys."""
        # Generate new DEK
        new_dek = self.kms.generate_data_key(
            KeyId="alias/cfzt-dek",
            KeySpec="AES_256"
        )
        
        # Re-encrypt data with new key
        for table in ["users", "sessions", "embeddings"]:
            self.reencrypt_table(table, new_dek)
        
        # Store new key reference
        self.store_key_reference(new_dek)
        
        # Archive old key
        self.archive_old_key()
```

### 3. Redis Key Rotation

```bash
# Generate new Redis password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update Redis password
kubectl exec -it redis-0 -n cfzt -- redis-cli CONFIG SET requirepass $NEW_PASSWORD

# Update application configuration
kubectl patch configmap redis-config -n cfzt --type=merge -p "{\"data\":{\"password\":\"$NEW_PASSWORD\"}}"

# Restart applications
kubectl rollout restart deployment -n cfzt
```

### 4. TLS Certificate Rotation

```bash
# Generate new certificate
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout new-tls.key -out new-tls.crt \
  -subj "/CN=api.cfzt.io"

# Update Kubernetes secret
kubectl create secret generic tls-secret \
  --from-file=tls.crt=new-tls.crt \
  --from-file=tls.key=new-tls.key \
  -n cfzt \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart Istio gateway
kubectl rollout restart deployment/istio-ingressgateway -n istio-system
```

## Post-Quantum Key Rotation

### 1. Kyber Key Rotation

```rust
use pqc_kyber::*;

fn rotate_kyber_key() -> Result<(), Box<dyn std::error::Error>> {
    // Generate new keypair
    let keypair = keypair();
    
    // Store new public key
    store_public_key(keypair.public_key())?;
    
    // Re-encrypt data with new key
    reencrypt_data(keypair.public_key())?;
    
    // Archive old key
    archive_old_key()?;
    
    Ok(())
}
```

### 2. Dilithium Key Rotation

```rust
use pqc_dilithium::*;

fn rotate_dilithium_key() -> Result<(), Box<dyn std::error::Error>> {
    // Generate new keypair
    let keypair = keypair();
    
    // Store new public key
    store_public_key(keypair.public_key())?;
    
    // Update certificate
    update_certificate(keypair.public_key())?;
    
    // Archive old key
    archive_old_key()?;
    
    Ok(())
}
```

### 3. QKD Key Rotation

```python
class QKDKeyRotator:
    def rotate_qkd_keys(self):
        """Rotate QKD keys."""
        # Exchange new key via QKD
        new_key = self.qkd.exchange_key()
        
        # Verify key integrity
        if not self.verify_key(new_key):
            raise KeyIntegrityError()
        
        # Store new key
        self.store_key(new_key)
        
        # Update services
        self.update_services(new_key)
        
        # Archive old key
        self.archive_old_key()
```

## Automated Rotation

### CronJob for Key Rotation

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: key-rotation
  namespace: cfzt
spec:
  schedule: "0 0 1 * *"  # Monthly
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: key-rotation
            image: cfzt/key-rotation:latest
            command:
            - /bin/sh
            - -c
            - |
              # Rotate DEK
              python -m cfzt.keys.rotate_dek
              
              # Rotate KEK
              python -m cfzt.keys.rotate_kek
              
              # Rotate PQC keys
              python -m cfzt.keys.rotate_pqc
            env:
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret-access-key
          restartPolicy: OnFailure
```

### Rotation Script

```python
#!/usr/bin/env python
"""Key rotation script."""

import argparse
import logging
from cfzt.keys import KeyManager

def main():
    parser = argparse.ArgumentParser(description="Rotate cryptographic keys")
    parser.add_argument("--key-type", required=True, choices=["dek", "kek", "pqc", "all"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    manager = KeyManager()
    
    if args.key_type == "dek" or args.key_type == "all":
        logger.info("Rotating DEK...")
        if not args.dry_run:
            manager.rotate_dek()
    
    if args.key_type == "kek" or args.key_type == "all":
        logger.info("Rotating KEK...")
        if not args.dry_run:
            manager.rotate_kek()
    
    if args.key_type == "pqc" or args.key_type == "all":
        logger.info("Rotating PQC keys...")
        if not args.dry_run:
            manager.rotate_pqc()
    
    logger.info("Key rotation complete")

if __name__ == "__main__":
    main()
```

## Monitoring

### Key Metrics

```yaml
# Key rotation metrics
- key_rotation_success_total{key_type}
- key_rotation_failure_total{key_type}
- key_age_days{key_type}
- key_usage_count{key_type}
```

### Alerts

```yaml
groups:
- name: key-rotation
  rules:
  - alert: KeyRotationFailed
    expr: rate(key_rotation_failure_total[5m]) > 0
    for: 5m
    labels:
      severity: critical
    
  - alert: KeyAgeHigh
    expr: key_age_days > 90
    for: 5m
    labels:
      severity: warning
```

## Rollback

### If Rotation Fails

```bash
# Restore previous key
aws kms disable-key --key-id <old-key-id>
aws kms enable-key --key-id <old-key-id>

# Update application configuration
kubectl patch configmap crypto-config -n cfzt --type=merge -p '{"data":{"key_id":"<old-key-id>"}}'

# Restart services
kubectl rollout restart deployment -n cfzt
```

## Post-Rotation

### 1. Verify Recovery
```bash
# Test encryption/decryption
curl -X POST http://pqc-crypto-service:8087/api/v1/crypto/encrypt \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "kyber-1024", "data": "test"}'

# Test signing/verification
curl -X POST http://pqc-crypto-service:8087/api/v1/crypto/sign \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "dilithium-5", "message": "test"}'
```

### 2. Monitor Metrics
```bash
# Watch key rotation metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/key-rotation
```

### 3. Document Rotation
- Update key inventory
- Update security documentation
- Create rotation report

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Security team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #key-rotation
- PagerDuty: Key Rotation Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
