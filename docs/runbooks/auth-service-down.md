# Auth Service Down - Incident Playbook

## Severity: Critical

## Impact
- All authentication requests fail
- Users cannot log in or refresh sessions
- Continuous verification stops

## Detection
- Alert: `auth_service_down`
- Alert: `auth_error_rate > 5%`
- Users report login failures

## Immediate Actions

### 1. Assess Impact (2 minutes)
```bash
# Check service status
kubectl get pods -n cfzt -l app=auth-service

# Check recent deployments
kubectl rollout history deployment/auth-service -n cfzt

# Check resource usage
kubectl top pods -n cfzt -l app=auth-service
```

### 2. Check Dependencies (3 minutes)
```bash
# Check Redis connectivity
kubectl exec -it redis-0 -n cfzt -- redis-cli ping

# Check CockroachDB connectivity
kubectl exec -it cockroachdb-0 -n cfzt -- cockroach node status --insecure

# Check Face ML service
kubectl get pods -n cfzt -l app=face-ml-service

# Check PQC crypto service
kubectl get pods -n cfzt -l app=pqc-crypto-service
```

### 3. Check Logs (2 minutes)
```bash
# Auth service logs
kubectl logs -n cfzt -l app=auth-service --tail=100

# Istio proxy logs
kubectl logs -n cfzt -l app=auth-service -c istio-proxy --tail=100
```

## Resolution Steps

### Scenario 1: Pod Crash Loop
```bash
# Check pod status
kubectl describe pod <pod-name> -n cfzt

# Check events
kubectl get events -n cfzt --field-selector involvedObject.name=<pod-name>

# Restart pod
kubectl delete pod <pod-name> -n cfzt

# If persistent, rollback
kubectl rollout undo deployment/auth-service -n cfzt
```

### Scenario 2: Resource Exhaustion
```bash
# Check resource limits
kubectl describe pod <pod-name> -n cfzt

# Increase limits temporarily
kubectl patch deployment auth-service -n cfzt -p '{"spec":{"template":{"spec":{"containers":[{"name":"auth-service","resources":{"limits":{"memory":"2Gi","cpu":"2"}}}]}}}}'

# Scale up replicas
kubectl scale deployment/auth-service -n cfzt --replicas=5
```

### Scenario 3: Dependency Failure
```bash
# Redis failure
kubectl rollout restart statefulset/redis -n cfzt

# CockroachDB failure
kubectl rollout restart statefulset/cockroachdb -n cfzt

# Face ML failure (circuit breaker should isolate)
kubectl rollout restart deployment/face-ml-service -n cfzt
```

### Scenario 4: Configuration Error
```bash
# Check ConfigMap
kubectl get configmap -n cfzt auth-service-config -o yaml

# Check secrets
kubectl get secret -n cfzt auth-service-secrets -o yaml

# Rollback to previous config
kubectl rollout undo deployment/auth-service -n cfzt
```

## Post-Incident

### 1. Verify Recovery
```bash
# Check service health
curl -s http://auth-service:8081/health | jq .

# Test authentication
curl -X POST http://auth-service:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","face_image":"base64..."}'
```

### 2. Monitor for Recurrence
```bash
# Watch metrics
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/auth-service
```

### 3. Document Incident
- Create incident report
- Update runbook if needed
- Schedule post-mortem

## Prevention

### Probes Configuration
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8082
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8082
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Resource Limits
```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

### Circuit Breaker
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: auth-service-circuit-breaker
spec:
  host: auth-service
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #incidents
- PagerDuty: Auth Service Down

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
