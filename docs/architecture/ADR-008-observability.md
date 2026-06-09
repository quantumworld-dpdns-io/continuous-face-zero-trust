# ADR-008: Observability Stack

## Status

Accepted

## Context

We need comprehensive observability for monitoring, debugging, and optimizing our distributed system.

## Decision

### Observability Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Metrics | Prometheus + Grafana | Industry standard, rich ecosystem |
| Logging | Fluentd + Elasticsearch + Kibana | Scalability, searchability |
| Tracing | Jaeger + OpenTelemetry | Distributed tracing, vendor-neutral |
| Alerting | Alertmanager + PagerDuty | Integration, escalation |
| Profiling | Pyroscope | Continuous profiling |

### Three Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Metrics (Prometheus)                                       ││
│  │  ├── Request rate, error rate, latency (RED)               ││
│  │  ├── Resource utilization (CPU, memory, disk)              ││
│  │  ├── Business metrics (auth success rate, risk scores)     ││
│  │  └── Custom metrics (face similarity, ZK proof time)       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Logs (Elasticsearch)                                       ││
│  │  ├── Application logs (structured JSON)                    ││
│  │  ├── Access logs (nginx/envoy)                              ││
│  │  ├── Audit logs (security events)                          ││
│  │  └── Error logs (stack traces, context)                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Traces (Jaeger)                                            ││
│  │  ├── Request traces (end-to-end)                           ││
│  │  ├── Service dependencies                                   ││
│  │  ├── Latency breakdown                                      ││
│  │  └── Error propagation                                      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Metrics Configuration

```yaml
# Prometheus Configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8080']
    metrics_path: /metrics

  - job_name: 'face-ml-service'
    static_configs:
      - targets: ['face-ml-service:8082']
    metrics_path: /metrics

  - job_name: 'istio-proxy'
    static_configs:
      - targets: ['istio-proxy:15090']
    metrics_path: /stats/prometheus
```

### Key Metrics

```yaml
# Auth Service Metrics
- auth_requests_total{method, endpoint, status}
- auth_request_duration_seconds{method, endpoint}
- auth_login_success_total
- auth_login_failure_total{reason}
- auth_session_active_total
- auth_risk_score_bucket{le}
- auth_continuous_verify_total{action}

# Face ML Metrics
- face_detect_total{status}
- face_detect_duration_seconds
- face_embed_total{status}
- face_embed_duration_seconds
- face_compare_total{status}
- face_compare_duration_seconds
- face_similarity_bucket{le}
- face_gpu_utilization_percent

# PQC Crypto Metrics
- pqc_keygen_total{algorithm}
- pqc_keygen_duration_seconds{algorithm}
- pqc_encapsulate_total{algorithm}
- pqc_encapsulate_duration_seconds{algorithm}
- pqc_sign_total{algorithm}
- pqc_sign_duration_seconds{algorithm}

# ZK Proofs Metrics
- zk_proof_generate_total{circuit}
- zk_proof_generate_duration_seconds{circuit}
- zk_proof_verify_total{circuit}
- zk_proof_verify_duration_seconds{circuit}
- zk_proof_size_bytes{circuit}

# Quantum RNG Metrics
- qrng_generate_total{source}
- qrng_generate_duration_seconds{source}
- qrng_entropy_pool_size_bits
- qrng_health_check_total{result}
- qrng_fallback_total
```

### Alert Rules

```yaml
groups:
- name: cfzt-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Error rate exceeds 5%"
      
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "P99 latency exceeds 200ms"
      
  - alert: HighGPUUtilization
    expr: face_gpu_utilization_percent > 90
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "GPU utilization exceeds 90%"
      
  - alert: QRNGDegraded
    expr: qrng_health_check_total{result="fail"} > 3
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "QRNG health check failing"
      
  - alert: ZKProofSlow
    expr: histogram_quantile(0.99, rate(zk_proof_generate_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "ZK proof generation exceeds 500ms"
```

### Dashboard Configuration

```json
{
  "dashboard": {
    "title": "CFZT System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "P99 Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))",
            "legendFormat": "{{service}}"
          }
        ]
      }
    ]
  }
}
```

### Distributed Tracing

```python
# OpenTelemetry Configuration
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

def setup_tracing(service_name: str):
    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name
    }))
    
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent",
        agent_port=6831,
    )
    
    provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

# Usage
tracer = setup_tracing("auth-service")

def login(request):
    with tracer.start_as_current_span("login") as span:
        span.set_attribute("user_id", request.user_id)
        
        # Child span for face verification
        with tracer.start_as_current_span("face_verify") as child_span:
            result = verify_face(request.face_image)
            child_span.set_attribute("similarity", result.similarity)
        
        return response
```

### Log Configuration

```json
{
  "logging": {
    "version": 1,
    "formatters": {
      "json": {
        "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "formatter": "json",
        "stream": "ext://sys.stdout"
      },
      "elasticsearch": {
        "class": "elasticsearch.client.Elasticsearch",
        "hosts": ["elasticsearch:9200"],
        "index": "cfzt-logs"
      }
    },
    "root": {
      "level": "INFO",
      "handlers": ["console", "elasticsearch"]
    }
  }
}
```

## Consequences

### Positive
- Comprehensive visibility into system behavior
- Fast incident detection and resolution
- Performance optimization insights
- Security audit capabilities

### Negative
- Storage costs for metrics and logs
- Performance overhead from tracing
- Complexity of distributed tracing
- Alert fatigue potential

### Risks
- Monitoring gaps
- Alert storms
- Storage capacity issues
- Privacy concerns with logs

## Alternatives Considered

### Datadog
- Pros: All-in-one, managed
- Cons: Expensive, vendor lock-in

### New Relic
- Pros: APM features, easy setup
- Cons: Cost, limited customization

### Self-hosted (ELK Stack)
- Pros: Full control, no vendor lock-in
- Cons: Operational overhead

## Review Date

2025-03-01
