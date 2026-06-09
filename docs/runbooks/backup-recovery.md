# Backup and Disaster Recovery

## Overview

This runbook covers backup and disaster recovery procedures for the CFZT system.

## Backup Types

| Type | Frequency | Retention | Storage |
|------|-----------|-----------|---------|
| Full Backup | Weekly | 30 days | S3/GCS/Azure Blob |
| Incremental Backup | Daily | 7 days | S3/GCS/Azure Blob |
| WAL Backup | Continuous | 7 days | S3/GCS/Azure Blob |
| Snapshot | Hourly | 24 hours | EBS/PD/Azure Disk |

## Backup Procedures

### 1. CockroachDB Backup

```bash
# Full backup
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="BACKUP INTO 's3://cfzt-backup/cockroachdb/full/?AUTH=implicit' AS OF SYSTEM TIME '-10s';"

# Incremental backup
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="BACKUP INTO LATEST IN 's3://cfzt-backup/cockroachdb/incremental/?AUTH=implicit' AS OF SYSTEM TIME '-10s';"

# WAL backup
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="BACKUP INTO 's3://cfzt-backup/cockroachdb/wal/?AUTH=implicit' AS OF SYSTEM TIME '-10s' WITH revision_history;"
```

### 2. Redis Backup

```bash
# Create RDB snapshot
kubectl exec -it redis-0 -n cfzt -- redis-cli BGSAVE

# Copy RDB file
kubectl cp redis-0:/data/dump.rdb ./backup/redis-$(date +%Y%m%d).rdb

# Upload to S3
aws s3 cp ./backup/redis-$(date +%Y%m%d).rdb s3://cfzt-backup/redis/
```

### 3. Qdrant Backup

```bash
# Create snapshot
kubectl exec -it qdrant-0 -n cfzt -- curl -X POST http://localhost:6333/collections/face_embeddings/snapshots

# Download snapshot
kubectl cp qdrant-0:/qdrant/storage/snapshots/face_embeddings ./backup/qdrant-$(date +%Y%m%d)

# Upload to S3
aws s3 cp ./backup/qdrant-$(date +%Y%m%d) s3://cfzt-backup/qdrant/ --recursive
```

### 4. Kubernetes Resources Backup

```bash
# Backup all resources
kubectl get all -n cfzt -o yaml > ./backup/kubernetes-$(date +%Y%m%d).yaml

# Backup secrets
kubectl get secrets -n cfzt -o yaml > ./backup/secrets-$(date +%Y%m%d).yaml

# Backup configmaps
kubectl get configmaps -n cfzt -o yaml > ./backup/configmaps-$(date +%Y%m%d).yaml

# Upload to S3
aws s3 cp ./backup/kubernetes-$(date +%Y%m%d).yaml s3://cfzt-backup/kubernetes/
aws s3 cp ./backup/secrets-$(date +%Y%m%d).yaml s3://cfzt-backup/kubernetes/
aws s3 cp ./backup/configmaps-$(date +%Y%m%d).yaml s3://cfzt-backup/kubernetes/
```

## Recovery Procedures

### 1. CockroachDB Recovery

```bash
# Restore from full backup
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="RESTORE FROM LATEST IN 's3://cfzt-backup/cockroachdb/full/?AUTH=implicit';"

# Restore from specific backup
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach sql \
  --execute="RESTORE FROM 's3://cfzt-backup/cockroachdb/full/20240101/?AUTH=implicit';"
```

### 2. Redis Recovery

```bash
# Stop Redis
kubectl exec -it redis-0 -n cfzt -- redis-cli SHUTDOWN

# Copy RDB file
kubectl cp ./backup/redis-$(date +%Y%m%d).rdb redis-0:/data/dump.rdb

# Start Redis
kubectl rollout restart statefulset/redis -n cfzt
```

### 3. Qdrant Recovery

```bash
# Stop Qdrant
kubectl exec -it qdrant-0 -n cfzt -- curl -X POST http://localhost:6333/collections/face_embeddings/snapshots/$(snapshot_name)/restore

# Restart Qdrant
kubectl rollout restart statefulset/qdrant -n cfzt
```

### 4. Kubernetes Resources Recovery

```bash
# Restore resources
kubectl apply -f ./backup/kubernetes-$(date +%Y%m%d).yaml -n cfzt

# Restore secrets
kubectl apply -f ./backup/secrets-$(date +%Y%m%d).yaml -n cfzt

# Restore configmaps
kubectl apply -f ./backup/configmaps-$(date +%Y%m%d).yaml -n cfzt
```

## Disaster Recovery Scenarios

### Scenario 1: Single Pod Failure

```bash
# Check pod status
kubectl get pods -n cfzt

# Delete failed pod
kubectl delete pod <pod-name> -n cfzt

# Verify new pod is running
kubectl get pods -n cfzt -l app=<service>
```

### Scenario 2: Node Failure

```bash
# Check node status
kubectl get nodes

# Cordon failed node
kubectl cordon <node-name>

# Drain failed node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Verify pods are rescheduled
kubectl get pods -n cfzt
```

### Scenario 3: Regional Outage

```bash
# Initiate failover to secondary region
python -m cfzt.failover.initiate --target=gcp

# Verify services are running
kubectl get pods -n cfzt

# Test services
curl -s http://api.cfzt.io/health | jq .
```

### Scenario 4: Complete Data Loss

```bash
# Restore from full backup
python -m cfzt.restore.full --backup=latest

# Verify data integrity
python -m cfzt.data.verify_integrity

# Test services
curl -s http://api.cfzt.io/health | jq .
```

## Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single Pod Failure | 5 minutes | 0 |
| Node Failure | 15 minutes | 0 |
| Regional Outage | 30 minutes | 1 minute |
| Complete Data Loss | 2 hours | 5 minutes |

## Monitoring

### Key Metrics

```yaml
# Backup metrics
- backup_success_total{type}
- backup_failure_total{type}
- backup_duration_seconds{type}
- backup_size_bytes{type}

# Recovery metrics
- recovery_success_total{scenario}
- recovery_failure_total{scenario}
- recovery_duration_seconds{scenario}
```

### Alerts

```yaml
groups:
- name: backup-recovery
  rules:
  - alert: BackupFailed
    expr: rate(backup_failure_total[5m]) > 0
    for: 5m
    labels:
      severity: critical
    
  - alert: BackupNotRunning
    expr: time() - backup_last_success_timestamp > 86400
    for: 5m
    labels:
      severity: warning
```

## Backup Schedule

### Daily

- [ ] Full backup of CockroachDB
- [ ] Incremental backup of Redis
- [ ] Snapshot of Qdrant
- [ ] Backup of Kubernetes resources

### Weekly

- [ ] Full backup of all data stores
- [ ] Test restore from backup
- [ ] Review backup logs
- [ ] Update backup procedures

### Monthly

- [ ] Full disaster recovery drill
- [ ] Review and update RTO/RPO
- [ ] Review and update procedures
- [ ] Train team on procedures

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Platform team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #backup-recovery
- PagerDuty: Backup/Recovery Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
