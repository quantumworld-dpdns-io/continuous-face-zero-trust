# Monitoring Bootstrap Guide

## Overview

This runbook covers setting up monitoring for the CFZT system.

## Monitoring Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Metrics | Prometheus + Grafana | Metrics collection and visualization |
| Logging | Fluentd + Elasticsearch | Log aggregation and search |
| Tracing | Jaeger + OpenTelemetry | Distributed tracing |
| Alerting | Alertmanager + PagerDuty | Alert management |

## Setup Procedure

### 1. Install Prometheus

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set alertmanager.enabled=true
```

### 2. Install Jaeger

```bash
# Add Helm repo
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update

# Install Jaeger
helm install jaeger jaegertracing/jaeger \
  --namespace monitoring \
  --set collector.replicas=3 \
  --set query.replicas=2
```

### 3. Install Fluentd

```bash
# Add Helm repo
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update

# Install Fluentd
helm install fluentd fluent/fluentd \
  --namespace monitoring \
  --set output.host=elasticsearch \
  --set output.port=9200
```

### 4. Install Elasticsearch

```bash
# Add Helm repo
helm repo add elastic https://helm.elastic.co
helm repo update

# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch \
  --namespace monitoring \
  --set replicas=3 \
  --set minimumMasterNodes=2
```

### 5. Configure ServiceMonitor

```yaml
# ServiceMonitor for CFZT services
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cfzt-services
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: cfzt
  namespaceSelector:
    matchNames:
    - cfzt
  endpoints:
  - port: http-metrics
    interval: 15s
    path: /metrics
```

### 6. Configure Alert Rules

```yaml
# Alert rules for CFZT
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cfzt-alerts
  namespace: monitoring
spec:
  groups:
  - name: cfzt
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{namespace="cfzt",status=~"5.."}[5m]) / rate(http_requests_total{namespace="cfzt"}[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate in CFZT services"
    
    - alert: HighLatency
      expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{namespace="cfzt"}[5m])) > 0.2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High latency in CFZT services"
```

### 7. Configure Grafana Dashboards

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
            "expr": "sum(rate(http_requests_total{namespace=\"cfzt\"}[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{namespace=\"cfzt\",status=~\"5..\"}[5m])) / sum(rate(http_requests_total{namespace=\"cfzt\"}[5m]))",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "P99 Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace=\"cfzt\"}[5m])) by (le, service))",
            "legendFormat": "{{service}}"
          }
        ]
      }
    ]
  }
}
```

### 8. Configure Alertmanager

```yaml
# Alertmanager configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    
    route:
      group_by: ['alertname', 'severity']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'pagerduty'
    
    receivers:
    - name: 'pagerduty'
      pagerduty_configs:
      - service_key: '<pagerduty-key>'
    
    inhibit_rules:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['alertname', 'namespace']
```

### 9. Configure Fluentd

```yaml
# Fluentd configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: monitoring
data:
  fluent.conf: |
    <source>
      @type tail
      @id in_tail_container_logs
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      exclude_path ["/var/log/containers/fluentd*"]
      read_from_head true
      <parse>
        @type multi_format
        <pattern>
          format json
          time_key time
          time_format %Y-%m-%dT%H:%M:%S.%NZ
          keep_time_key true
        </pattern>
        <pattern>
          format regexp
          expression /^(?<time>.+) (?<stream>stdout|stderr) [^ ]* (?<log>.*)$/
          time_format %Y-%m-%dT%H:%M:%S.%N%:z
        </pattern>
      </parse>
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
    </filter>
    
    <match kubernetes.**>
      @type elasticsearch
      @id out_es
      @log_level info
      include_tag_key true
      host elasticsearch
      port 9200
      logstash_format true
      logstash_prefix kubernetes
      logstash_dateformat %Y.%m.%d
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.buffer
        flush_mode interval
        flush_thread_count 2
        flush_interval 5s
        retry_type exponential_backoff
        retry_forever true
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

### 10. Configure OpenTelemetry

```yaml
# OpenTelemetry Collector configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: monitoring
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    
    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
    
    exporters:
      jaeger:
        endpoint: jaeger:14250
        tls:
          insecure: true
    
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [jaeger]
```

## Verification

### 1. Verify Prometheus

```bash
# Check Prometheus status
kubectl get pods -n monitoring -l app=prometheus

# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
open http://localhost:9090/targets
```

### 2. Verify Grafana

```bash
# Check Grafana status
kubectl get pods -n monitoring -l app=grafana

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
open http://localhost:3000
```

### 3. Verify Jaeger

```bash
# Check Jaeger status
kubectl get pods -n monitoring -l app=jaeger

# Access Jaeger UI
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
open http://localhost:16686
```

### 4. Verify Elasticsearch

```bash
# Check Elasticsearch status
kubectl get pods -n monitoring -l app=elasticsearch

# Check Elasticsearch health
kubectl port-forward -n monitoring svc/elasticsearch 9200:9200
curl -s http://localhost:9200/_cluster/health | jq .
```

## Monitoring Checklist

### Daily

- [ ] Check Prometheus targets
- [ ] Check Grafana dashboards
- [ ] Check Jaeger traces
- [ ] Check Elasticsearch indices
- [ ] Check alert status

### Weekly

- [ ] Review alert history
- [ ] Review performance trends
- [ ] Review cost trends
- [ ] Update dashboards
- [ ] Update alert rules

### Monthly

- [ ] Review monitoring coverage
- [ ] Review and optimize queries
- [ ] Review and optimize dashboards
- [ ] Review and optimize alerts
- [ ] Review and optimize retention

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Platform team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #monitoring
- PagerDuty: Monitoring Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
