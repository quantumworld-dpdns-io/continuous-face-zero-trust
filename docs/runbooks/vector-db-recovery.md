# Qdrant Vector DB Recovery Procedures

## Severity: High

## Impact
- Face embedding search unavailable
- User identification fails
- Continuous verification cannot match faces

## Detection
- Alert: `qdrant_unavailable`
- Alert: `qdrant_search_latency_high`
- Alert: `qdrant_storage_full`

## Immediate Actions

### 1. Assess Cluster Status (2 minutes)
```bash
# Check Qdrant pods
kubectl get pods -n cfzt -l app=vector-db

# Check Qdrant health
kubectl exec -it qdrant-0 -n cfzt -- curl -s http://localhost:6333/healthz

# Check storage
kubectl exec -it qdrant-0 -n cfzt -- df -h /qdrant/storage
```

### 2. Check Logs (2 minutes)
```bash
# Qdrant logs
kubectl logs -n cfzt -l app=vector-db --tail=100

# Check for errors
kubectl logs -n cfzt -l app=vector-db | grep -i error
```

### 3. Check Network (1 minute)
```bash
# Check connectivity
kubectl exec -it qdrant-0 -n cfzt -- curl -s http://qdrant-1:6333/healthz

# Check Istio proxy
kubectl logs -n cfzt -l app=vector-db -c istio-proxy --tail=50
```

## Resolution Steps

### Scenario 1: Pod Crash Loop
```bash
# Check pod status
kubectl describe pod qdrant-0 -n cfzt

# Check events
kubectl get events -n cfzt --field-selector involvedObject.name=qdrant-0

# Restart pod
kubectl delete pod qdrant-0 -n cfzt

# Check storage permissions
kubectl exec -it qdrant-0 -n cfzt -- ls -la /qdrant/storage
```

### Scenario 2: Storage Full
```bash
# Check storage usage
kubectl exec -it qdrant-0 -n cfzt -- du -sh /qdrant/storage

# Delete old snapshots
kubectl exec -it qdrant-0 -n cfzt -- rm -f /qdrant/storage/snapshots/old_*

# Compact storage
kubectl exec -it qdrant-0 -n cfzt -- curl -X POST http://localhost:6333/collections/face_embeddings/snapshots

# Scale storage
kubectl patch pvc qdrant-data-qdrant-0 -n cfzt -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'
```

### Scenario 3: Collection Corruption
```bash
# Check collection status
kubectl exec -it qdrant-0 -n cfzt -- curl -s http://localhost:6333/collections/face_embeddings | jq .

# Recreate collection
kubectl exec -it qdrant-0 -n cfzt -- curl -X PUT http://localhost:6333/collections/face_embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 512,
      "distance": "Cosine"
    }
  }'

# Restore from backup
kubectl exec -it qdrant-0 -n cfzt -- curl -X POST http://localhost:6333/collections/face_embeddings/snapshots/upload
```

### Scenario 4: Network Issues
```bash
# Check network policies
kubectl get networkpolicy -n cfzt | grep vector-db

# Verify Istio proxy
kubectl logs -n cfzt -l app=vector-db -c istio-proxy --tail=50

# Restart Istio proxy
kubectl exec -it qdrant-0 -n cfzt -c istio-proxy -- pilot-agent request POST /quit
```

## Data Recovery

### Restore from Snapshot
```bash
# List snapshots
kubectl exec -it qdrant-0 -n cfzt -- curl -s http://localhost:6333/collections/face_embeddings/snapshots | jq .

# Restore snapshot
kubectl exec -it qdrant-0 -n cfzt -- curl -X POST http://localhost:6333/collections/face_embeddings/snapshots/<snapshot_name>/restore
```

### Rebuild Embeddings
```python
class EmbeddingRebuilder:
    def rebuild_embeddings(self):
        """Rebuild embeddings from CockroachDB."""
        # Get all users with embeddings
        users = self.db.query("SELECT user_id, embedding_hash FROM users WHERE embedding_hash IS NOT NULL")
        
        for user in users:
            # Regenerate embedding (requires face images)
            embedding = self.face_ml.embed(user.face_image)
            
            # Upsert to Qdrant
            self.qdrant.upsert(
                collection="face_embeddings",
                points=[{
                    "id": user.user_id,
                    "vector": embedding.tolist(),
                    "payload": {"user_id": user.user_id}
                }]
            )
```

### Verify Data Integrity
```python
class DataIntegrityChecker:
    def check_integrity(self):
        """Check data integrity between systems."""
        # Count users in CockroachDB
        db_count = self.db.query("SELECT COUNT(*) FROM users").scalar()
        
        # Count embeddings in Qdrant
        qdrant_count = self.qdrant.get_collection("face_embeddings").points_count
        
        if db_count != qdrant_count:
            self.alert(f"Data mismatch: DB={db_count}, Qdrant={qdrant_count}")
            return False
        
        return True
```

## Post-Incident

### 1. Verify Recovery
```bash
# Test embedding search
curl -X POST http://vector-db-service:8091/api/v1/vector/search \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.1,0.2,...],"limit":10}'

# Test embedding upsert
curl -X POST http://vector-db-service:8091/api/v1/vector/upsert \
  -H "Content-Type: application/json" \
  -d '{"id":"test","vector":[0.1,0.2,...]}'
```

### 2. Monitor Metrics
```bash
# Watch Qdrant metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/vector-db
```

### 3. Document Incident
- Create incident report
- Update runbook if needed
- Schedule post-mortem

## Prevention

### Storage Management
```yaml
# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qdrant-data-qdrant-0
  namespace: cfzt
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast
  resources:
    requests:
      storage: 100Gi
```

### Backup Schedule
```yaml
# CronJob for snapshots
apiVersion: batch/v1
kind: CronJob
metadata:
  name: qdrant-snapshot
  namespace: cfzt
spec:
  schedule: "0 */6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: snapshot
            image: curlimages/curl
            command:
            - /bin/sh
            - -c
            - |
              curl -X POST http://qdrant-0:6333/collections/face_embeddings/snapshots
          restartPolicy: OnFailure
```

### Replication
```yaml
# Qdrant replication config
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: cfzt
spec:
  serviceName: qdrant
  replicas: 3
  selector:
    matchLabels:
      app: qdrant
  template:
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.7.0
        ports:
        - containerPort: 6333
          name: http
        - containerPort: 6334
          name: grpc
        volumeMounts:
        - name: data
          mountPath: /qdrant/storage
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Database team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #incidents
- PagerDuty: Vector DB Recovery

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
