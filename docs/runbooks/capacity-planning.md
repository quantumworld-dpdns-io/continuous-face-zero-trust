# Capacity Planning Guide

## Overview

This runbook covers capacity planning for the CFZT system across all services and infrastructure.

## Capacity Metrics

### Service Capacity

| Service | Current Load | Capacity | Threshold |
|---------|--------------|----------|-----------|
| Auth Service | 1000 req/s | 5000 req/s | 80% |
| Face ML | 500 req/s | 2000 req/s | 80% |
| PQC Crypto | 2000 req/s | 10000 req/s | 80% |
| ZK Proofs | 200 req/s | 1000 req/s | 80% |
| Quantum RNG | 1000 req/s | 5000 req/s | 80% |

### Infrastructure Capacity

| Resource | Current | Capacity | Threshold |
|----------|---------|----------|-----------|
| CPU | 100 cores | 400 cores | 80% |
| Memory | 500 GB | 2 TB | 80% |
| Storage | 5 TB | 20 TB | 80% |
| Network | 10 Gbps | 40 Gbps | 80% |

## Capacity Monitoring

### 1. CPU Utilization

```bash
# Check CPU usage
kubectl top nodes

# Check pod CPU usage
kubectl top pods -n cfzt

# Check CPU requests/limits
kubectl describe nodes | grep -A 5 "Allocated resources"
```

### 2. Memory Utilization

```bash
# Check memory usage
kubectl top nodes --sort-by=memory

# Check pod memory usage
kubectl top pods -n cfzt --sort-by=memory

# Check memory requests/limits
kubectl describe nodes | grep -A 5 "Allocated resources"
```

### 3. Storage Utilization

```bash
# Check storage usage
kubectl exec -it cockroachdb-0 -n cfzt -- df -h /cockroach/cockroach-data

# Check Qdrant storage
kubectl exec -it qdrant-0 -n cfzt -- df -h /qdrant/storage

# Check Redis storage
kubectl exec -it redis-0 -n cfzt -- redis-cli INFO memory
```

### 4. Network Utilization

```bash
# Check network bandwidth
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep bytes

# Check request rate
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep request
```

## Capacity Planning Scripts

### 1. Capacity Forecast

```python
class CapacityForecaster:
    def forecast(self, metric: str, days: int) -> dict:
        """Forecast capacity usage."""
        # Get historical data
        history = self.get_history(metric, days=30)
        
        # Calculate trend
        trend = self.calculate_trend(history)
        
        # Forecast future usage
        forecast = []
        for day in range(1, days + 1):
            predicted = trend * day + history[-1]
            forecast.append({
                "day": day,
                "predicted": predicted,
                "upper_bound": predicted * 1.2,
                "lower_bound": predicted * 0.8,
            })
        
        return forecast
```

### 2. Scaling Recommendations

```python
class ScalingRecommender:
    def recommend(self) -> List[dict]:
        """Generate scaling recommendations."""
        recommendations = []
        
        # Check CPU
        cpu_usage = self.get_cpu_usage()
        if cpu_usage > 80:
            recommendations.append({
                "resource": "cpu",
                "current": cpu_usage,
                "recommended": cpu_usage * 1.5,
                "action": "scale_up",
            })
        
        # Check memory
        memory_usage = self.get_memory_usage()
        if memory_usage > 80:
            recommendations.append({
                "resource": "memory",
                "current": memory_usage,
                "recommended": memory_usage * 1.5,
                "action": "scale_up",
            })
        
        # Check storage
        storage_usage = self.get_storage_usage()
        if storage_usage > 80:
            recommendations.append({
                "resource": "storage",
                "current": storage_usage,
                "recommended": storage_usage * 2,
                "action": "expand",
            })
        
        return recommendations
```

### 3. Cost Optimization

```python
class CostOptimizer:
    def optimize(self) -> List[dict]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Check for idle resources
        idle_resources = self.find_idle_resources()
        for resource in idle_resources:
            recommendations.append({
                "resource": resource,
                "action": "downscale",
                "savings": self.calculate_savings(resource),
            })
        
        # Check for spot instance opportunities
        spot_opportunities = self.find_spot_opportunities()
        for opportunity in spot_opportunities:
            recommendations.append({
                "resource": opportunity,
                "action": "convert_to_spot",
                "savings": self.calculate_spot_savings(opportunity),
            })
        
        return recommendations
```

## Scaling Procedures

### 1. Horizontal Pod Autoscaling

```yaml
# HPA for Auth Service
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
  namespace: cfzt
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Vertical Pod Autoscaling

```yaml
# VPA for Face ML Service
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: face-ml-service-vpa
  namespace: cfzt
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: face-ml-service
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: face-ml-service
      minAllowed:
        cpu: 1000m
        memory: 2Gi
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
```

### 3. Cluster Autoscaling

```yaml
# Cluster Autoscaler
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      containers:
      - name: cluster-autoscaler
        image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.27.0
        command:
        - ./cluster-autoscaler
        - --v=4
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/cfzt
```

## Capacity Planning Checklist

### Monthly Review

- [ ] Review CPU utilization trends
- [ ] Review memory utilization trends
- [ ] Review storage utilization trends
- [ ] Review network utilization trends
- [ ] Review cost trends
- [ ] Update capacity forecasts
- [ ] Update scaling policies
- [ ] Review and optimize resource requests/limits

### Quarterly Review

- [ ] Review infrastructure costs
- [ ] Review and optimize instance types
- [ ] Review and optimize storage classes
- [ ] Review and optimize network configurations
- [ ] Review and optimize backup strategies
- [ ] Review and optimize disaster recovery procedures

## Monitoring

### Key Metrics

```yaml
# Capacity metrics
- node_cpu_utilization_percent
- node_memory_utilization_percent
- node_storage_utilization_percent
- node_network_utilization_percent
- pod_cpu_utilization_percent
- pod_memory_utilization_percent
- pod_storage_utilization_percent
```

### Alerts

```yaml
groups:
- name: capacity
  rules:
  - alert: HighCPUUtilization
    expr: node_cpu_utilization_percent > 80
    for: 5m
    labels:
      severity: warning
    
  - alert: HighMemoryUtilization
    expr: node_memory_utilization_percent > 80
    for: 5m
    labels:
      severity: warning
    
  - alert: HighStorageUtilization
    expr: node_storage_utilization_percent > 80
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
- Slack: #capacity-planning
- PagerDuty: Capacity Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
