# Biometric Breach Response Plan

## Overview

This runbook covers response procedures for biometric data breaches.

## Breach Types

| Type | Severity | Impact | Response Time |
|------|----------|--------|---------------|
| Embedding Exposure | High | User identification risk | 15 minutes |
| Raw Image Exposure | Critical | Complete biometric compromise | 5 minutes |
| Liveness Data Exposure | Medium | Spoofing risk | 30 minutes |
| ZK Proof Exposure | Low | Proof reuse risk | 1 hour |

## Immediate Actions

### 1. Contain the Breach (5 minutes)

```bash
# Isolate affected services
kubectl scale deployment/face-ml-service -n cfzt --replicas=0

# Block network traffic
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: breach-isolation
  namespace: cfzt
spec:
  podSelector:
    matchLabels:
      app: face-ml-service
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress: []
EOF

# Revoke all active sessions
kubectl exec -it redis-0 -n cfzt -- redis-cli DEL session:*

# Notify security team
curl -X POST https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX \
  -H 'Content-type: application/json' \
  -d '{"text":"🚨 BIOMETRIC BREACH DETECTED - Immediate response required"}'
```

### 2. Assess Impact (15 minutes)

```bash
# Check affected users
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="SELECT user_id, created_at FROM users WHERE embedding_exposed = true;"

# Check breach scope
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="SELECT COUNT(*) FROM audit_logs WHERE event_type = 'biometric_breach';"

# Check data exposure
kubectl exec -it qdrant-0 -n cfzt -- curl -s http://localhost:6333/collections/face_embeddings | jq .
```

### 3. Notify Affected Users (30 minutes)

```python
class BreachNotifier:
    def notify_users(self, affected_users: List[str]):
        """Notify affected users."""
        for user_id in affected_users:
            # Send email notification
            self.send_email(
                user_id=user_id,
                subject="Security Alert: Biometric Data Breach",
                template="biometric_breach_notification.html"
            )
            
            # Send push notification
            self.send_push(
                user_id=user_id,
                message="Security alert: Your biometric data may have been compromised. Please re-enroll."
            )
            
            # Log notification
            self.log_notification(user_id)
```

### 4. Rotate Keys (1 hour)

```bash
# Rotate all encryption keys
python -m cfzt.keys.rotate_all --reason "biometric_breach"

# Rotate QKD keys
python -m cfzt.quantum.rotate_qkd --reason "biometric_breach"

# Rotate QRNG seeds
python -m cfzt.quantum.rotate_seed --reason "biometric_breach"
```

### 5. Revoke ZK Proofs (2 hours)

```bash
# Revoke all ZK proofs
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="UPDATE zk_proofs SET revoked = true WHERE created_at > '2024-01-01';"

# Clear ZK proof cache
kubectl exec -it redis-0 -n cfzt -- redis-cli DEL zk:proof:*
```

### 6. Force Re-enrollment (24 hours)

```python
class ReEnrollmentManager:
    def force_reenrollment(self, affected_users: List[str]):
        """Force affected users to re-enroll."""
        for user_id in affected_users:
            # Invalidate current enrollment
            self.invalidate_enrollment(user_id)
            
            # Send re-enrollment request
            self.send_reenrollment_request(user_id)
            
            # Set deadline
            self.set_reenrollment_deadline(user_id, deadline=timedelta(days=7))
```

## Investigation

### 1. Forensic Analysis

```bash
# Collect logs
kubectl logs -n cfzt -l app=face-ml-service --since=24h > /tmp/face-ml-logs.txt
kubectl logs -n cfzt -l app=auth-service --since=24h > /tmp/auth-logs.txt

# Check access patterns
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="SELECT * FROM audit_logs WHERE event_type = 'embedding_access' AND created_at > NOW() - INTERVAL '24 hours';"

# Check network traffic
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /config_dump | grep -A 20 "routes"
```

### 2. Identify Attack Vector

```bash
# Check for unauthorized access
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="SELECT * FROM audit_logs WHERE event_type = 'unauthorized_access';"

# Check for data exfiltration
kubectl exec -it redis-0 -n cfzt -- redis-cli MONITOR | grep "embedding"

# Check for API abuse
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep request
```

### 3. Root Cause Analysis

```python
class RootCauseAnalyzer:
    def analyze_breach(self, breach_data: dict) -> dict:
        """Analyze breach root cause."""
        # Check for vulnerabilities
        vulnerabilities = self.check_vulnerabilities(breach_data)
        
        # Check for misconfigurations
        misconfigurations = self.check_misconfigurations(breach_data)
        
        # Check for insider threats
        insider_threats = self.check_insider_threats(breach_data)
        
        return {
            "vulnerabilities": vulnerabilities,
            "misconfigurations": misconfigurations,
            "insider_threats": insider_threats,
            "root_cause": self.determine_root_cause(
                vulnerabilities, misconfigurations, insider_threats
            )
        }
```

## Recovery

### 1. Verify System Integrity

```bash
# Check all services
kubectl get pods -n cfzt

# Check data integrity
python -m cfzt.data.verify_integrity

# Check encryption
python -m cfzt.crypto.verify_encryption
```

### 2. Restore Services

```bash
# Remove network isolation
kubectl delete networkpolicy breach-isolation -n cfzt

# Scale up services
kubectl scale deployment/face-ml-service -n cfzt --replicas=3

# Verify services
curl -s http://face-ml-service:8083/health | jq .
```

### 3. Monitor for Recurrence

```bash
# Watch for suspicious activity
kubectl exec -it redis-0 -n cfzt -- redis-cli MONITOR | grep "embedding"

# Check for unauthorized access
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="SELECT * FROM audit_logs WHERE event_type = 'unauthorized_access' AND created_at > NOW() - INTERVAL '1 hour';"
```

## Compliance Reporting

### 1. Regulatory Notifications

```python
class ComplianceReporter:
    def report_breach(self, breach_data: dict):
        """Report breach to regulators."""
        # GDPR notification (72 hours)
        if self.is_gdpr_applicable(breach_data):
            self.report_to_gdpr(breach_data)
        
        # HIPAA notification (60 days)
        if self.is_hipaa_applicable(breach_data):
            self.report_to_hipaa(breach_data)
        
        # SOC 2 notification
        if self.is_soc2_applicable(breach_data):
            self.report_to_soc2(breach_data)
```

### 2. Documentation

```markdown
## Breach Report

**Date:** 2024-01-01
**Severity:** Critical
**Affected Users:** 1000
**Data Exposed:** Face embeddings

### Timeline
- 00:00 - Breach detected
- 00:05 - Services isolated
- 00:15 - Impact assessed
- 00:30 - Users notified
- 01:00 - Keys rotated
- 02:00 - ZK proofs revoked
- 24:00 - Re-enrollment completed

### Root Cause
- Vulnerability: API endpoint without authentication
- Misconfiguration: Network policy allowing public access

### Remediation
- Added authentication to API endpoint
- Updated network policies
- Implemented additional monitoring
```

## Prevention

### 1. Security Measures

```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: biometric-data-protection
  namespace: cfzt
spec:
  podSelector:
    matchLabels:
      app: face-ml-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: auth-service
    ports:
    - protocol: TCP
      port: 8082
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: vector-db-service
    ports:
    - protocol: TCP
      port: 8091
```

### 2. Monitoring

```yaml
# Security monitoring
groups:
- name: biometric-security
  rules:
  - alert: UnauthorizedEmbeddingAccess
    expr: rate(biometric_embedding_access_total{authorized="false"}[5m]) > 0
    for: 5m
    labels:
      severity: critical
    
  - alert: EmbeddingDataExfiltration
    expr: rate(biometric_embedding_export_total[5m]) > 10
    for: 5m
    labels:
      severity: critical
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | Security team |
| 5-15 min | CISO |
| 15-30 min | Legal team |
| 30+ min | CEO/Board |

## Communication

### Internal
- Slack: #security-incidents
- PagerDuty: Biometric Breach

### External
- Status page: status.cfzt.io
- Email: security@cfzt.io
- Legal: legal@cfzt.io
