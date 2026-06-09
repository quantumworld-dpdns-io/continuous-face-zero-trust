# Cloud Failover Procedures

## Overview

This runbook covers failover procedures across multiple cloud providers (AWS, GCP, Azure).

## Failover Scenarios

| Scenario | Source | Target | RTO | RPO |
|----------|--------|--------|-----|-----|
| AWS Regional Outage | AWS | GCP | 15 min | 1 min |
| GCP Regional Outage | GCP | AWS | 15 min | 1 min |
| Azure Regional Outage | Azure | AWS | 15 min | 1 min |
| Complete AWS Outage | AWS | GCP + Azure | 30 min | 5 min |

## Pre-Failover Checklist

- [ ] Verify target cloud health
- [ ] Check data replication status
- [ ] Notify stakeholders
- [ ] Schedule maintenance window
- [ ] Backup current state

## Failover Procedure

### 1. Assess Situation (5 minutes)

```bash
# Check AWS health
aws health describe-events --region us-east-1

# Check GCP health
gcloud compute operations list --filter="status=PENDING"

# Check Azure health
az monitor activity-log list --query "[?level.value=='Critical']"

# Check DNS resolution
dig api.cfzt.io
```

### 2. Initiate Failover (10 minutes)

```bash
# Update DNS to point to GCP
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.cfzt.io",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "GCP_LOAD_BALANCER_IP"}]
      }
    }]
  }'

# Verify DNS propagation
dig api.cfzt.io +short
```

### 3. Promote Database Replicas (15 minutes)

```bash
# Promote GCP Cloud SQL replica
gcloud sql instances promote-replica cfzt-primary-gcp --region=us-central1

# Update connection strings
kubectl patch configmap db-config -n cfzt --type=merge -p '{"data":{"host":"cfzt-primary-gcp.us-central1.sqlproxy.googleapis.com"}}'

# Restart services
kubectl rollout restart deployment -n cfzt
```

### 4. Sync Secrets (20 minutes)

```bash
# Sync AWS secrets to GCP
for secret in $(aws secretsmanager list-secrets --query "SecretList[?contains(Name, 'cfzt/')].Name" --output text); do
  value=$(aws secretsmanager get-secret-value --secret-id $secret --query SecretString --output text)
  gcloud secrets create $secret --data-file=<(echo $value) --replication-policy=user-managed
done

# Verify secrets
gcloud secrets list --filter="name:cfzt"
```

### 5. Warm Caches (25 minutes)

```bash
# Warm Redis cache in GCP
kubectl exec -it redis-0 -n cfzt -- redis-cli BGREWRITEAOF

# Pre-populate session cache
python -m cfzt.cache.warm --target=gcp

# Verify cache
kubectl exec -it redis-0 -n cfzt -- redis-cli DBSIZE
```

### 6. Verify Services (30 minutes)

```bash
# Check all services
kubectl get pods -n cfzt

# Test authentication
curl -X POST https://api.cfzt.io/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","face_image":"base64..."}'

# Test face ML
curl -X POST https://api.cfzt.io/api/v1/face/detect \
  -H "Content-Type: application/json" \
  -d '{"image":"base64..."}'
```

## Post-Failover

### 1. Monitor Stability (1 hour)

```bash
# Watch metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/multi-cloud

# Monitor error rates
curl -s http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])
```

### 2. Update Monitoring (2 hours)

```bash
# Update Prometheus targets
kubectl patch configmap prometheus-config -n monitoring --type=merge -p '{"data":{"prometheus.yml":"..."}'

# Restart Prometheus
kubectl rollout restart deployment/prometheus -n monitoring
```

### 3. Document Incident (24 hours)

```markdown
## Failover Report

**Date:** 2024-01-01
**Source:** AWS us-east-1
**Target:** GCP us-central1
**Duration:** 30 minutes

### Timeline
- 00:00 - AWS outage detected
- 00:05 - Failover initiated
- 00:15 - Database promoted
- 00:20 - Secrets synced
- 00:25 - Caches warmed
- 00:30 - Services verified

### Root Cause
- AWS us-east-1 regional outage

### Lessons Learned
- Need faster DNS propagation
- Improve secret sync automation
- Add more health checks
```

## Failback Procedure

### 1. Verify AWS Recovery (1 hour)

```bash
# Check AWS health
aws health describe-events --region us-east-1

# Check AWS services
aws eks describe-cluster --name cfzt --region us-east-1
```

### 2. Sync Data Back (2 hours)

```bash
# Sync CockroachDB data
cockroach sql --execute="BACKUP INTO 'gs://cfzt-backup/';"

# Restore to AWS
cockroach sql --execute="RESTORE FROM LATEST IN 's3://cfzt-backup/';"

# Sync Redis data
kubectl exec -it redis-0 -n cfzt -- redis-cli BGSAVE
kubectl cp redis-0:/data/dump.rdb ./redis-backup.rdb
```

### 3. Switch Back (3 hours)

```bash
# Update DNS to point back to AWS
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.cfzt.io",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "AWS_LOAD_BALANCER_IP"}]
      }
    }]
  }'

# Verify DNS propagation
dig api.cfzt.io +short
```

### 4. Verify Recovery (4 hours)

```bash
# Check all services
kubectl get pods -n cfzt

# Test authentication
curl -X POST https://api.cfzt.io/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","face_image":"base64..."}'
```

## Monitoring

### Key Metrics

```yaml
# Multi-cloud metrics
- cloud_health_status{provider, region}
- cloud_failover_total{source, target}
- cloud_failback_total{source, target}
- cloud_sync_duration_seconds{source, target}
```

### Alerts

```yaml
groups:
- name: multi-cloud
  rules:
  - alert: CloudProviderDown
    expr: cloud_health_status == 0
    for: 5m
    labels:
      severity: critical
    
  - alert: FailoverInProgress
    expr: cloud_failover_total > 0
    for: 5m
    labels:
      severity: warning
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Platform team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #multi-cloud
- PagerDuty: Cloud Failover

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
