# Performance Optimization Guide

## Overview

This runbook covers performance optimization for the CFZT system across all services.

## Performance Metrics

### Service Performance

| Service | Metric | Target | Current |
|---------|--------|--------|---------|
| Auth Service | Latency (p99) | <200ms | 150ms |
| Face ML | Inference (p99) | <100ms | 80ms |
| PQC Crypto | Operations (p99) | <50ms | 40ms |
| ZK Proofs | Proving (p99) | <500ms | 400ms |
| Quantum RNG | Throughput | >1000 req/s | 1200 req/s |

### Infrastructure Performance

| Resource | Metric | Target | Current |
|----------|--------|--------|---------|
| CPU | Utilization | <70% | 60% |
| Memory | Utilization | <80% | 70% |
| Network | Latency | <1ms | 0.5ms |
| Storage | IOPS | >10000 | 12000 |

## Performance Monitoring

### 1. Latency Monitoring

```bash
# Check request latency
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep request_duration

# Check upstream latency
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep upstream_rq_time

# Check application latency
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep request_duration
```

### 2. Throughput Monitoring

```bash
# Check request rate
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep request_rate

# Check connection rate
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep connection_rate

# Check application throughput
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep throughput
```

### 3. Error Rate Monitoring

```bash
# Check error rate
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep error_rate

# Check 5xx errors
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /stats | grep 5xx

# Check application errors
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep error
```

## Performance Optimization Scripts

### 1. Latency Optimizer

```python
class LatencyOptimizer:
    def optimize(self) -> List[dict]:
        """Generate latency optimization recommendations."""
        recommendations = []
        
        # Check connection pool settings
        connection_pool = self.check_connection_pool()
        if connection_pool["utilization"] > 80:
            recommendations.append({
                "setting": "connection_pool",
                "current": connection_pool["size"],
                "recommended": connection_pool["size"] * 1.5,
                "impact": "reduce_connection_overhead",
            })
        
        # Check timeout settings
        timeouts = self.check_timeouts()
        if timeouts["p99"] > 200:
            recommendations.append({
                "setting": "timeout",
                "current": timeouts["current"],
                "recommended": timeouts["current"] * 0.8,
                "impact": "reduce_wait_time",
            })
        
        # Check retry settings
        retries = self.check_retries()
        if retries["rate"] > 0.1:
            recommendations.append({
                "setting": "retries",
                "current": retries["attempts"],
                "recommended": retries["attempts"] - 1,
                "impact": "reduce_retry_overhead",
            })
        
        return recommendations
```

### 2. Throughput Optimizer

```python
class ThroughputOptimizer:
    def optimize(self) -> List[dict]:
        """Generate throughput optimization recommendations."""
        recommendations = []
        
        # Check batch size
        batch_size = self.check_batch_size()
        if batch_size["utilization"] < 50:
            recommendations.append({
                "setting": "batch_size",
                "current": batch_size["size"],
                "recommended": batch_size["size"] * 2,
                "impact": "increase_throughput",
            })
        
        # Check concurrency
        concurrency = self.check_concurrency()
        if concurrency["utilization"] < 50:
            recommendations.append({
                "setting": "concurrency",
                "current": concurrency["level"],
                "recommended": concurrency["level"] * 2,
                "impact": "increase_parallelism",
            })
        
        # Check caching
        cache_hit_rate = self.check_cache_hit_rate()
        if cache_hit_rate < 0.9:
            recommendations.append({
                "setting": "cache",
                "current": cache_hit_rate,
                "recommended": 0.95,
                "impact": "reduce_database_load",
            })
        
        return recommendations
```

### 3. Resource Optimizer

```python
class ResourceOptimizer:
    def optimize(self) -> List[dict]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        # Check CPU requests
        cpu_requests = self.check_cpu_requests()
        if cpu_requests["utilization"] < 50:
            recommendations.append({
                "resource": "cpu",
                "current": cpu_requests["request"],
                "recommended": cpu_requests["request"] * 0.8,
                "impact": "reduce_cost",
            })
        
        # Check memory requests
        memory_requests = self.check_memory_requests()
        if memory_requests["utilization"] < 50:
            recommendations.append({
                "resource": "memory",
                "current": memory_requests["request"],
                "recommended": memory_requests["request"] * 0.8,
                "impact": "reduce_cost",
            })
        
        # Check storage requests
        storage_requests = self.check_storage_requests()
        if storage_requests["utilization"] < 50:
            recommendations.append({
                "resource": "storage",
                "current": storage_requests["request"],
                "recommended": storage_requests["request"] * 0.8,
                "impact": "reduce_cost",
            })
        
        return recommendations
```

## Performance Tuning Procedures

### 1. Connection Pool Tuning

```yaml
# Connection pool configuration
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: auth-service
  namespace: cfzt
spec:
  host: auth-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 200
        connectTimeout: 5s
      http:
        http1MaxPendingRequests: 200
        http2MaxRequests: 2000
        maxRequestsPerConnection: 10
        maxRetries: 3
```

### 2. Timeout Tuning

```yaml
# Timeout configuration
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: auth-service
  namespace: cfzt
spec:
  hosts:
  - auth-service
  http:
  - route:
    - destination:
        host: auth-service
    timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
```

### 3. Caching Tuning

```python
class CacheTuner:
    def tune(self):
        """Tune cache configuration."""
        # Check cache hit rate
        hit_rate = self.get_cache_hit_rate()
        
        if hit_rate < 0.9:
            # Increase cache size
            self.increase_cache_size()
            
            # Adjust TTL
            self.adjust_ttl()
            
            # Enable prefetching
            self.enable_prefetching()
```

### 4. Database Tuning

```python
class DatabaseTuner:
    def tune(self):
        """Tune database configuration."""
        # Check query performance
        slow_queries = self.get_slow_queries()
        
        for query in slow_queries:
            # Analyze query
            analysis = self.analyze_query(query)
            
            # Add index if needed
            if analysis["needs_index"]:
                self.add_index(analysis["table"], analysis["columns"])
            
            # Optimize query if needed
            if analysis["can_optimize"]:
                self.optimize_query(query)
```

### 5. GPU Tuning

```python
class GPUTuner:
    def tune(self):
        """Tune GPU configuration."""
        # Check GPU utilization
        utilization = self.get_gpu_utilization()
        
        if utilization < 50:
            # Reduce batch size
            self.reduce_batch_size()
            
            # Enable mixed precision
            self.enable_mixed_precision()
            
            # Optimize model
            self.optimize_model()
```

## Performance Testing

### 1. Load Testing

```python
class LoadTester:
    def run_load_test(self, rps: int, duration: int) -> dict:
        """Run load test."""
        # Start load test
        results = self.start_load_test(rps, duration)
        
        # Analyze results
        analysis = self.analyze_results(results)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(analysis)
        
        return {
            "results": results,
            "analysis": analysis,
            "recommendations": recommendations,
        }
```

### 2. Stress Testing

```python
class StressTester:
    def run_stress_test(self, max_rps: int, duration: int) -> dict:
        """Run stress test."""
        # Start stress test
        results = self.start_stress_test(max_rps, duration)
        
        # Find breaking point
        breaking_point = self.find_breaking_point(results)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(breaking_point)
        
        return {
            "results": results,
            "breaking_point": breaking_point,
            "recommendations": recommendations,
        }
```

### 3. Endurance Testing

```python
class EnduranceTester:
    def run_endurance_test(self, rps: int, duration: int) -> dict:
        """Run endurance test."""
        # Start endurance test
        results = self.start_endurance_test(rps, duration)
        
        # Check for memory leaks
        memory_leaks = self.check_memory_leaks(results)
        
        # Check for performance degradation
        degradation = self.check_performance_degradation(results)
        
        return {
            "results": results,
            "memory_leaks": memory_leaks,
            "degradation": degradation,
        }
```

## Performance Monitoring

### Key Metrics

```yaml
# Performance metrics
- request_latency_seconds{service, endpoint, method}
- request_rate{service, endpoint, method}
- error_rate{service, endpoint, method, status}
- cpu_utilization_percent{service, pod}
- memory_utilization_percent{service, pod}
- gpu_utilization_percent{service, pod}
```

### Alerts

```yaml
groups:
- name: performance
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(request_latency_seconds_bucket[5m])) > 0.2
    for: 5m
    labels:
      severity: warning
    
  - alert: HighErrorRate
    expr: rate(error_rate[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
    
  - alert: HighCPUUtilization
    expr: cpu_utilization_percent > 80
    for: 5m
    labels:
      severity: warning
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Performance team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #performance
- PagerDuty: Performance Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
