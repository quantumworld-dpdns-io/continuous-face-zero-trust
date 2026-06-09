# General Incident Response Playbook

## Overview

This runbook covers general incident response procedures for the CFZT system.

## Incident Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| P1 | Critical | 5 minutes | CISO, VP Engineering |
| P2 | High | 15 minutes | Engineering Manager |
| P3 | Medium | 30 minutes | Team Lead |
| P4 | Low | 2 hours | On-call Engineer |

## Incident Response Phases

### 1. Detection & Triage (5 minutes)

```bash
# Check alert
kubectl get alerts -n monitoring

# Check service status
kubectl get pods -n cfzt

# Check logs
kubectl logs -n cfzt -l app=<service> --tail=100

# Check metrics
kubectl port-forward -n monitoring svc/prometheus 9090:9090
open http://localhost:9090
```

### 2. Containment (15 minutes)

```bash
# Isolate affected service
kubectl scale deployment/<service> -n cfzt --replicas=0

# Block network traffic
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: incident-isolation
  namespace: cfzt
spec:
  podSelector:
    matchLabels:
      app: <service>
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress: []
EOF

# Notify team
curl -X POST https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX \
  -H 'Content-type: application/json' \
  -d '{"text":"🚨 INCIDENT DETECTED - Immediate response required"}'
```

### 3. Investigation (30 minutes)

```bash
# Collect logs
kubectl logs -n cfzt -l app=<service> --since=1h > /tmp/incident-logs.txt

# Collect metrics
kubectl port-forward -n monitoring svc/prometheus 9090:9090
curl -s http://localhost:9090/api/v1/query?query=rate(http_requests_total{namespace="cfzt"}[5m]) > /tmp/incident-metrics.txt

# Collect traces
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
open http://localhost:16686
```

### 4. Eradication (1 hour)

```bash
# Remove compromised resources
kubectl delete pod <pod-name> -n cfzt

# Rotate secrets
python -m cfzt.keys.rotate_all --reason "incident"

# Update security policies
kubectl apply -f k8s/security-policies/
```

### 5. Recovery (2 hours)

```bash
# Restore services
kubectl scale deployment/<service> -n cfzt --replicas=3

# Verify services
kubectl get pods -n cfzt
curl -s http://<service>:8081/health | jq .

# Monitor for recurrence
kubectl logs -n cfzt -l app=<service> --tail=100
```

### 6. Post-Incident (24 hours)

```markdown
## Incident Report

**Date:** 2024-01-01
**Severity:** P1
**Duration:** 2 hours

### Timeline
- 00:00 - Incident detected
- 00:05 - Triage completed
- 00:15 - Containment completed
- 00:30 - Investigation started
- 01:00 - Eradication completed
- 02:00 - Recovery completed

### Root Cause
- Vulnerability: API endpoint without authentication
- Misconfiguration: Network policy allowing public access

### Impact
- Affected Users: 1000
- Data Exposed: None
- Service Downtime: 2 hours

### Remediation
- Added authentication to API endpoint
- Updated network policies
- Implemented additional monitoring

### Lessons Learned
- Need better monitoring
- Need faster incident response
- Need better documentation
```

## Incident Response Checklist

### Pre-Incident

- [ ] Incident response plan documented
- [ ] Incident response team identified
- [ ] Communication channels established
- [ ] Tools and access configured
- [ ] Training completed

### During Incident

- [ ] Incident detected and triaged
- [ ] Containment implemented
- [ ] Investigation conducted
- [ ] Eradication completed
- [ ] Recovery implemented
- [ ] Communication sent

### Post-Incident

- [ ] Incident report completed
- [ ] Lessons learned documented
- [ ] Remediation actions tracked
- [ ] Monitoring improved
- [ ] Training updated

## Communication Templates

### Internal Notification

```markdown
Subject: [INCIDENT] Service Degradation - <Service Name>

**Incident ID:** <ID>
**Severity:** P1/P2/P3/P4
**Status:** Investigating/Contained/Recovered
**Affected Service:** <Service Name>
**Impact:** <Impact Description>
**Next Update:** <Time>

**Action Items:**
- [ ] <Action 1>
- [ ] <Action 2>
- [ ] <Action 3>
```

### External Notification

```markdown
Subject: Service Status Update

**Status:** Investigating
**Affected Service:** <Service Name>
**Impact:** <Impact Description>
**Workaround:** <Workaround if available>
**Next Update:** <Time>

We are currently investigating an issue affecting <Service Name>. We will provide updates as they become available.
```

## Escalation Matrix

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Team lead |
| 15-30 min | Engineering manager |
| 30-60 min | CISO / VP Engineering |
| 60+ min | CEO / Board |

## Communication Channels

### Internal
- Slack: #incidents
- PagerDuty: Incident Response
- Email: incidents@cfzt.io

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
- Twitter: @cfzt_status

## Post-Incident Review

### Review Checklist

- [ ] Timeline reviewed
- [ ] Root cause identified
- [ ] Impact assessed
- [ ] Remediation actions defined
- [ ] Lessons learned documented
- [ ] Action items assigned
- [ ] Follow-up scheduled

### Review Meeting

- **Attendees:** Incident response team, engineering leads, management
- **Duration:** 1 hour
- **Agenda:**
  1. Incident timeline
  2. Root cause analysis
  3. Impact assessment
  4. Remediation actions
  5. Lessons learned
  6. Action items
