# Redis Cluster Split Brain Recovery

## Severity: High

## Impact
- Session cache inconsistency
- Rate limiting failures
- Potential session hijacking

## Detection
- Alert: `redis_cluster_split_brain`
- Alert: `redis_cluster_slots_not_covered`
- Alert: `redis_cluster_state_fail`

## Immediate Actions

### 1. Assess Cluster Status (2 minutes)
```bash
# Check cluster status
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster info

# Check nodes
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster nodes

# Check slots coverage
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster slots
```

### 2. Identify Split Brain (2 minutes)
```bash
# Check master nodes
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster nodes | grep master

# Check for multiple masters per slot
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster slots | grep -E "^[0-9]+"

# Check cluster state
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster info | grep cluster_state
```

### 3. Check Network (1 minute)
```bash
# Check inter-node connectivity
kubectl exec -it redis-0 -n cfzt -- redis-cli -h redis-1 ping
kubectl exec -it redis-0 -n cfzt -- redis-cli -h redis-2 ping

# Check DNS resolution
kubectl exec -it redis-0 -n cfzt -- nslookup redis-1.cfzt.svc.cluster.local
```

## Resolution Steps

### Scenario 1: Simple Split Brain
```bash
# Identify the minority partition
# Stop Redis on minority nodes
kubectl exec -it redis-3 -n cfzt -- redis-cli cluster forget <node-id>
kubectl exec -it redis-3 -n cfzt -- redis-cli shutdown

# Resync cluster
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster replicate <master-node-id>
```

### Scenario 2: Slot Conflict
```bash
# Fix slot assignment
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster setslot <slot> migrating <target-node-id>
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster setslot <slot> node <target-node-id>

# Verify slots
kubectl exec -it redis-0 -n cfzt -- redis-cli cluster slots
```

### Scenario 3: Complete Cluster Failure
```bash
# Stop all Redis instances
kubectl rollout restart statefulset/redis -n cfzt

# Wait for pods to be ready
kubectl wait --for=condition=ready pod/redis-0 -n cfzt --timeout=60s
kubectl wait --for=condition=ready pod/redis-1 -n cfzt --timeout=60s
kubectl wait --for=condition=ready pod/redis-2 -n cfzt --timeout=60s

# Recreate cluster
kubectl exec -it redis-0 -n cfzt -- redis-cli --cluster create \
  redis-0:6379 redis-1:6379 redis-2:6379 \
  --cluster-replicas 1
```

### Scenario 4: Network Partition Recovery
```bash
# Check network policies
kubectl get networkpolicy -n cfzt | grep redis

# Verify Istio proxy
kubectl logs -n cfzt -l app=redis -c istio-proxy --tail=50

# Restart Istio proxy
kubectl exec -it redis-0 -n cfzt -c istio-proxy -- pilot-agent request POST /quit
```

## Data Recovery

### Check for Data Loss
```bash
# Check key count per node
kubectl exec -it redis-0 -n cfzt -- redis-cli dbsize
kubectl exec -it redis-1 -n cfzt -- redis-cli dbsize
kubectl exec -it redis-2 -n cfzt -- redis-cli dbsize

# Check RDB files
kubectl exec -it redis-0 -n cfzt -- ls -la /data/dump.rdb
```

### Restore from Backup
```bash
# Stop Redis
kubectl exec -it redis-0 -n cfzt -- redis-cli shutdown

# Restore RDB file
kubectl cp backup/dump.rdb cfzt/redis-0:/data/dump.rdb

# Start Redis
kubectl rollout restart statefulset/redis -n cfzt
```

### Rebuild Sessions
```python
class SessionRebuilder:
    def rebuild_sessions(self):
        """Rebuild sessions from database."""
        # Get active sessions from CockroachDB
        sessions = self.db.query("SELECT * FROM sessions WHERE status = 'active'")
        
        for session in sessions:
            # Rebuild cache
            self.redis.setex(
                f"session:{session.id}",
                session.ttl,
                session.serialize()
            )
```

## Post-Incident

### 1. Verify Recovery
```bash
# Test session operations
curl -X POST http://auth-service:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","face_image":"base64..."}'

# Test cache operations
kubectl exec -it redis-0 -n cfzt -- redis-cli set test "value"
kubectl exec -it redis-0 -n cfzt -- redis-cli get test
```

### 2. Monitor Metrics
```bash
# Watch Redis metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/redis-cluster
```

### 3. Document Incident
- Create incident report
- Update runbook if needed
- Schedule post-mortem

## Prevention

### Cluster Configuration
```yaml
# Redis StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: cfzt
spec:
  serviceName: redis
  replicas: 6
  selector:
    matchLabels:
      app: redis
  template:
    spec:
      containers:
      - name: redis
        image: redis:7.0
        command:
        - redis-server
        - --cluster-enabled
        - "yes"
        - --cluster-node-timeout
        - "5000"
        - --appendonly
        - "yes"
        - --appendfsync
        - "everysec"
        ports:
        - containerPort: 6379
          name: redis
        - containerPort: 16379
          name: gossip
        volumeMounts:
        - name: data
          mountPath: /data
```

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: redis-network-policy
  namespace: cfzt
spec:
  podSelector:
    matchLabels:
      app: redis
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
      port: 6379
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
    - protocol: TCP
      port: 16379
```

### Health Monitoring
```python
class RedisHealthMonitor:
    def check_cluster_health(self) -> ClusterHealth:
        """Check Redis cluster health."""
        return ClusterHealth(
            nodes=self.get_node_count(),
            slots_covered=self.check_slots_coverage(),
            state=self.get_cluster_state(),
            failures=self.get_failures()
        )
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
- PagerDuty: Redis Cluster Split Brain

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
