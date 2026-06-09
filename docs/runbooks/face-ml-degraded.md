# Face ML Service Degraded - Incident Playbook

## Severity: High

## Impact
- Face detection/embedding latency increased
- Liveness detection accuracy reduced
- Continuous verification may timeout

## Detection
- Alert: `face_ml_latency_high`
- Alert: `face_ml_error_rate > 10%`
- Alert: `face_ml_gpu_utilization > 90%`

## Immediate Actions

### 1. Assess Impact (2 minutes)
```bash
# Check service status
kubectl get pods -n cfzt -l app=face-ml-service

# Check GPU utilization
nvidia-smi

# Check resource usage
kubectl top pods -n cfzt -l app=face-ml-service
```

### 2. Check Logs (2 minutes)
```bash
# Service logs
kubectl logs -n cfzt -l app=face-ml-service --tail=100

# Check for OOM kills
kubectl get events -n cfzt --field-selector reason=OOMKilling
```

### 3. Check Model Loading (1 minute)
```bash
# Check if model is loaded
kubectl exec -it <pod-name> -n cfzt -- curl -s http://localhost:8083/health | jq .

# Check model version
kubectl exec -it <pod-name> -n cfzt -- cat /models/version.txt
```

## Resolution Steps

### Scenario 1: GPU Memory Exhaustion
```bash
# Check GPU memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Clear GPU cache
kubectl exec -it <pod-name> -n cfzt -- python -c "import torch; torch.cuda.empty_cache()"

# Restart pod to free GPU memory
kubectl delete pod <pod-name> -n cfzt
```

### Scenario 2: Model Loading Failure
```bash
# Check model files
kubectl exec -it <pod-name> -n cfzt -- ls -la /models/

# Verify model integrity
kubectl exec -it <pod-name> -n cfzt -- python -c "import torch; torch.load('/models/arcface.pt')"

# Re-download model
kubectl exec -it <pod-name> -n cfzt -- python scripts/download_models.py
```

### Scenario 3: High Load
```bash
# Scale up replicas
kubectl scale deployment/face-ml-service -n cfzt --replicas=4

# Check HPA
kubectl get hpa -n cfzt -l app=face-ml-service

# Manually scale if needed
kubectl patch hpa face-ml-service -n cfzt -p '{"spec":{"maxReplicas":8}}'
```

### Scenario 4: Network Issues
```bash
# Check Istio proxy
kubectl logs -n cfzt -l app=face-ml-service -c istio-proxy --tail=50

# Check mTLS
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /certs

# Restart Istio proxy
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request POST /quit
```

## Performance Tuning

### Model Optimization
```python
# Enable model optimization
model = ArcFaceModel()
model.optimize()  # Enable ONNX optimization
model.quantize()  # Enable quantization
model.warmup()    # Pre-load model
```

### Batch Processing
```python
# Enable batch processing
config = FaceMLConfig(
    batch_size=32,
    max_batch_wait_ms=10,
    num_workers=4
)
```

### Caching
```python
# Enable embedding cache
cache = EmbeddingCache(
    redis_url="redis://redis:6379",
    ttl_seconds=300,
    max_size=10000
)
```

## Post-Incident

### 1. Verify Recovery
```bash
# Test face detection
curl -X POST http://face-ml-service:8083/api/v1/face/detect \
  -H "Content-Type: application/json" \
  -d '{"image":"base64..."}'

# Test embedding generation
curl -X POST http://face-ml-service:8083/api/v1/face/embed \
  -H "Content-Type: application/json" \
  -d '{"image":"base64..."}'
```

### 2. Monitor Metrics
```bash
# Watch inference latency
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/face-ml
```

### 3. Document Incident
- Create incident report
- Update runbook if needed
- Schedule post-mortem

## Prevention

### Resource Limits
```yaml
resources:
  requests:
    cpu: 2000m
    memory: 4Gi
    nvidia.com/gpu: 1
  limits:
    cpu: 4000m
    memory: 8Gi
    nvidia.com/gpu: 1
```

### HPA Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: face-ml-service
  namespace: cfzt
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: face-ml-service
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: nvidia.com/gpu
      target:
        type: Utilization
        averageUtilization: 80
```

### Model Versioning
```yaml
# Model registry
apiVersion: v1
kind: ConfigMap
metadata:
  name: face-ml-models
  namespace: cfzt
data:
  arcface-version: "v1.2.0"
  retinface-version: "v2.0.1"
  liveness-version: "v1.1.0"
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | ML team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #incidents
- PagerDuty: Face ML Degraded

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
