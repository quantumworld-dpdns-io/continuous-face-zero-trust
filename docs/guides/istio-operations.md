# Istio Operations Guide

## Overview

This guide covers Istio operations for the CFZT system.

## Prerequisites

- Kubernetes 1.25+
- Istio 1.20+
- istioctl

## Installation

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Install Istio
istioctl install --set profile=default

# Verify installation
istioctl verify-install
```

## Configuration

### 1. Peer Authentication

```yaml
# k8s/istio/peer-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: cfzt
spec:
  mtls:
    mode: STRICT
```

### 2. Authorization Policy

```yaml
# k8s/istio/authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: auth-service
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: auth-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/cfzt/sa/edge-gateway"
    to:
    - operation:
        methods: ["POST", "GET"]
        paths: ["/api/v1/auth/*"]
```

### 3. Virtual Service

```yaml
# k8s/istio/virtual-service.yaml
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
        subset: v1
      weight: 90
    - destination:
        host: auth-service
        subset: v2
      weight: 10
    timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
```

### 4. Destination Rule

```yaml
# k8s/istio/destination-rule.yaml
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
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRetries: 3
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

## Operations

### 1. Check Status

```bash
# Check Istio status
istioctl proxy-status

# Check proxy config
istioctl proxy-config cluster <pod-name> -n cfzt

# Check proxy routes
istioctl proxy-config routes <pod-name> -n cfzt
```

### 2. Debug Issues

```bash
# Check proxy logs
kubectl logs <pod-name> -n cfzt -c istio-proxy --tail=100

# Check proxy config dump
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump

# Check proxy stats
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats
```

### 3. Restart Proxy

```bash
# Restart sidecar proxy
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request POST /quit

# Or restart pod
kubectl delete pod <pod-name> -n cfzt
```

### 4. Upgrade Istio

```bash
# Upgrade Istio
istioctl upgrade --set profile=default

# Verify upgrade
istioctl verify-install
```

## Monitoring

### 1. Prometheus

```yaml
# k8s/istio/service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: istio-mesh-monitor
  namespace: istio-system
spec:
  selector:
    matchLabels:
      istio: pilot
  endpoints:
  - port: http-monitoring
    interval: 15s
```

### 2. Grafana

```bash
# Access Grafana
kubectl port-forward -n istio-system svc/grafana 3000:3000

# Or use Istio dashboard
open http://localhost:3000/d/istio
```

### 3. Jaeger

```bash
# Access Jaeger
kubectl port-forward -n istio-system svc/jaeger 16686:16686

# Or use Istio tracing
open http://localhost:16686
```

## Troubleshooting

### 1. mTLS Issues

```bash
# Check mTLS status
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /certs

# Check certificate validity
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- openssl x509 -in /etc/certs/cert-chain.pem -noout -dates
```

### 2. Routing Issues

```bash
# Check virtual service
kubectl get virtualservice -n cfzt -o yaml

# Check destination rule
kubectl get destinationrule -n cfzt -o yaml

# Check routes
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump | grep -A 20 "routes"
```

### 3. Latency Issues

```bash
# Check proxy latency
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep request_duration

# Check upstream latency
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep upstream_rq_time
```

## Best Practices

### 1. Resource Limits

```yaml
# k8s/istio/proxy-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio-proxy-config
  namespace: cfzt
data:
  config: |
    concurrency: 2
    image:
      imageType: DEFAULT
    tracing:
      sampling: 10
```

### 2. Health Checks

```yaml
# k8s/istio/health-check.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: cfzt
spec:
  template:
    spec:
      containers:
      - name: istio-proxy
        readinessProbe:
          httpGet:
            path: /healthz/ready
            port: 15021
          initialDelaySeconds: 1
          periodSeconds: 3
        livenessProbe:
          httpGet:
            path: /healthz/alive
            port: 15021
          initialDelaySeconds: 1
          periodSeconds: 3
```

### 3. Resource Requests

```yaml
# k8s/istio/resource-requests.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: cfzt
spec:
  template:
    spec:
      containers:
      - name: istio-proxy
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 2000m
            memory: 1Gi
```

## Resources

- [Istio Documentation](https://istio.io/latest/docs/)
- [Istio Best Practices](https://istio.io/latest/docs/ops/best-practices/)
- [Istio Troubleshooting](https://istio.io/latest/docs/ops/common-problems/)
