# Compliance Checklist

## Overview

This runbook covers compliance requirements for SOC2, HIPAA, and GDPR.

## Compliance Frameworks

| Framework | Scope | Audit Frequency | Last Audit |
|-----------|-------|-----------------|------------|
| SOC 2 Type II | Security, Availability, Confidentiality | Annual | 2024-01-01 |
| HIPAA | PHI Protection | Annual | 2024-01-01 |
| GDPR | EU Data Protection | Continuous | 2024-01-01 |

## SOC 2 Compliance

### Security

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| CC6.1 | Logical access controls | ✅ | RBAC, mTLS, network policies |
| CC6.2 | Authentication mechanisms | ✅ | Biometric + device authentication |
| CC6.3 | Authorization | ✅ | Least privilege, network policies |
| CC6.6 | Encryption | ✅ | AES-256, TLS 1.3, PQC |
| CC6.7 | Key management | ✅ | HSM, rotation, escrow |
| CC7.1 | Vulnerability management | ✅ | Scanning, patching |
| CC7.2 | Monitoring | ✅ | Audit logs, alerts |
| CC8.1 | Change management | ✅ | CI/CD, approvals |

### Availability

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| A1.1 | Capacity planning | ✅ | Monitoring, auto-scaling |
| A1.2 | Environmental protections | ✅ | Multi-cloud, redundancy |
| A1.3 | Recovery procedures | ✅ | Backup, DR testing |

### Confidentiality

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| C1.1 | Data classification | ✅ | Data labels, access controls |
| C1.2 | Data disposal | ✅ | Cryptographic erasure |

## HIPAA Compliance

### Technical Safeguards

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| §164.312(a) | Access control | ✅ | RBAC, MFA |
| §164.312(b) | Audit controls | ✅ | Immutable logs |
| §164.312(c) | Integrity | ✅ | Digital signatures, ZK proofs |
| §164.312(d) | Authentication | ✅ | Biometric + device |
| §164.312(e) | Transmission security | ✅ | TLS 1.3, mTLS |

### Administrative Safeguards

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| §164.308(a)(1) | Risk analysis | ✅ | Annual assessment |
| §164.308(a)(2) | workforce training | ✅ | Annual training |
| §164.308(a)(3) | Information access | ✅ | Least privilege |
| §164.308(a)(4) | Security incident | ✅ | Incident response plan |
| §164.308(a)(5) | Security awareness | ✅ | Phishing tests |
| §164.308(a)(6) | Contingency plan | ✅ | Backup, DR testing |

### Physical Safeguards

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| §164.310(a)(1) | Facility access | ✅ | Cloud provider controls |
| §164.310(a)(2) | Workstation use | ✅ | Device management |
| §164.310(a)(3) | Device controls | ✅ | MDM, encryption |
| §164.310(d)(1) | Device security | ✅ | MDM, encryption |

## GDPR Compliance

### Data Protection Principles

| Principle | Requirement | Status | Evidence |
|-----------|-------------|--------|----------|
| Art. 5(1)(a) | Lawfulness, fairness, transparency | ✅ | Consent management |
| Art. 5(1)(b) | Purpose limitation | ✅ | Data minimization |
| Art. 5(1)(c) | Data minimization | ✅ | No raw images |
| Art. 5(1)(d) | Accuracy | ✅ | Data validation |
| Art. 5(1)(e) | Storage limitation | ✅ | Retention policies |
| Art. 5(1)(f) | Integrity/confidentiality | ✅ | Encryption |

### Data Subject Rights

| Right | Requirement | Status | Evidence |
|-------|-------------|--------|----------|
| Art. 15 | Right of access | ✅ | Data export API |
| Art. 16 | Right to rectification | ✅ | Data update API |
| Art. 17 | Right to erasure | ✅ | Cryptographic erasure |
| Art. 18 | Right to restriction | ✅ | Data freeze API |
| Art. 20 | Right to data portability | ✅ | Export API |
| Art. 21 | Right to object | ✅ | Consent withdrawal |

### Security of Processing

| Control | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| Art. 25 | Privacy by design | ✅ | ZK proofs, no raw images |
| Art. 26 | Joint controllers | ✅ | DPA agreements |
| Art. 27 | Representatives | ✅ | EU representative |
| Art. 28 | Processors | ✅ | DPA agreements |
| Art. 29 | Processing under authority | ✅ | Access controls |
| Art. 30 | Records of processing | ✅ | Processing register |
| Art. 31 | Cooperation with authority | ✅ | Response procedures |
| Art. 32 | Security of processing | ✅ | Defense in depth |
| Art. 33 | Breach notification | ✅ | Incident response |
| Art. 34 | Communication of breach | ✅ | User notification |
| Art. 35 | DPIA | ✅ | Privacy impact assessment |
| Art. 36 | Prior consultation | ✅ | Authority consultation |
| Art. 37 | DPO | ✅ | DPO appointed |
| Art. 38 | DPO position | ✅ | Independent DPO |
| Art. 39 | DPO tasks | ✅ | DPO responsibilities |

## Audit Procedures

### Pre-Audit

- [ ] Review compliance checklist
- [ ] Gather evidence
- [ ] Prepare documentation
- [ ] Schedule audit
- [ ] Notify stakeholders

### During Audit

- [ ] Provide access to systems
- [ ] Answer auditor questions
- [ ] Provide evidence
- [ ] Document findings

### Post-Audit

- [ ] Review findings
- [ ] Create remediation plan
- [ ] Implement fixes
- [ ] Update documentation
- [ ] Schedule follow-up

## Evidence Collection

### Technical Evidence

```bash
# Collect logs
kubectl logs -n cfzt --since=30d > /tmp/audit-logs.txt

# Collect metrics
kubectl port-forward -n monitoring svc/prometheus 9090:9090
curl -s http://localhost:9090/api/v1/query?query=rate(http_requests_total{namespace="cfzt"}[5m]) > /tmp/audit-metrics.txt

# Collect configurations
kubectl get all -n cfzt -o yaml > /tmp/audit-config.yaml
```

### Administrative Evidence

```bash
# Collect policies
cp -r policies/ /tmp/audit-policies/

# Collect procedures
cp -r procedures/ /tmp/audit-procedures/

# Collect training records
cp -r training/ /tmp/audit-training/
```

## Monitoring

### Key Metrics

```yaml
# Compliance metrics
- compliance_check_total{framework, control}
- compliance_violation_total{framework, control}
- audit_finding_total{framework, severity}
```

### Alerts

```yaml
groups:
- name: compliance
  rules:
  - alert: ComplianceViolation
    expr: rate(compliance_violation_total[5m]) > 0
    for: 5m
    labels:
      severity: critical
    
  - alert: AuditFinding
    expr: rate(audit_finding_total{severity="critical"}[5m]) > 0
    for: 5m
    labels:
      severity: critical
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | Compliance officer |
| 5-15 min | CISO |
| 15-30 min | Legal counsel |
| 30+ min | CEO |

## Communication

### Internal
- Slack: #compliance
- PagerDuty: Compliance Issues

### External
- Status page: status.cfzt.io
- Email: compliance@cfzt.io
