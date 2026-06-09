# Istio Troubleshooting Guide

## Common Issues

### 1. mTLS Connection Failures

#### Symptoms
- Services cannot communicate
- 503 errors in access logs
- `SSL handshake failed` errors

#### Diagnosis
```bash
# Check mTLS status
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /certs

# Check PeerAuthentication
kubectl get peerauthentication -n cfzt

# Check AuthorizationPolicy
kubectl get authorizationpolicy -n cfzt

# Check proxy config
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump
```

#### Resolution
```bash
# Verify mTLS mode
kubectl get peerauthentication default -n cfzt -o yaml

# Check certificate validity
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- openssl x509 -in /etc/certs/cert-chain.pem -noout -dates

# Restart proxy to refresh certs
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request POST /quit
```

### 2. Traffic Routing Issues

#### Symptoms
- Requests going to wrong service version
- Load balancing not working
- Timeouts on specific routes

#### Diagnosis
```bash
# Check VirtualService
kubectl get virtualservice -n cfzt -o yaml

# Check DestinationRule
kubectl get destinationrule -n cfzt -o yaml

# Check routing rules
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump | grep -A 20 "routes"
```

#### Resolution
```bash
# Verify route configuration
kubectl describe virtualservice <name> -n cfzt

# Check service endpoints
kubectl get endpoints <service-name> -n cfzt

# Restart Istiod to reload config
kubectl rollout restart deployment/istiod -n istio-system
```

### 3. Circuit Breaker Issues

#### Symptoms
- Requests failing with 503
- `Connection pool exhausted` errors
- Service unreachable

#### Diagnosis
```bash
# Check DestinationRule
kubectl get destinationrule <name> -n cfzt -o yaml

# Check circuit breaker status
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump | grep -A 10 "circuit_breakers"

# Check outlier detection
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep outlier
```

#### Resolution
```bash
# Adjust circuit breaker settings
kubectl patch destinationrule <name> -n cfzt --type=merge -p '{"spec":{"trafficPolicy":{"connectionPool":{"http":{"http1MaxPendingRequests":200,"http2MaxRequests":2000}}}}}'

# Reset outlier detection
kubectl patch destinationrule <name> -n cfzt --type=merge -p '{"spec":{"trafficPolicy":{"outlierDetection":{"consecutive5xxErrors":10}}}}'
```

### 4. Latency Issues

#### Symptoms
- High request latency
- Slow response times
- Timeouts

#### Diagnosis
```bash
# Check proxy latency
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep request_duration

# Check upstream latency
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep upstream_rq_time

# Check connection pool
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump | grep -A 10 "connection_pool"
```

#### Resolution
```bash
# Increase connection pool
kubectl patch destinationrule <name> -n cfzt --type=merge -p '{"spec":{"trafficPolicy":{"connectionPool":{"tcp":{"maxConnections":200},"http":{"http1MaxPendingRequests":200,"http2MaxRequests":2000}}}}}'

# Adjust timeouts
kubectl patch virtualservice <name> -n cfzt --type=merge -p '{"spec":{"http":[{"timeout":"10s","retries":{"attempts":3,"perTryTimeout":"3s"}}]}}'
```

### 5. Certificate Issues

#### Symptoms
- `certificate expired` errors
- `SSL certificate problem` errors
- mTLS handshake failures

#### Diagnosis
```bash
# Check certificate validity
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- openssl x509 -in /etc/certs/cert-chain.pem -noout -text

# Check certificate rotation
kubectl get secret -n cfzt | grep istio

# Check Istio CA
kubectl get configmap -n istio-system istio-ca-root-cert -o yaml
```

#### Resolution
```bash
# Force certificate rotation
kubectl delete secret -n cfzt <secret-name>

# Restart pod to get new cert
kubectl delete pod <pod-name> -n cfzt

# Verify new cert
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /certs
```

### 6. Sidecar Injection Issues

#### Symptoms
- Pods missing sidecar
- 503 errors
- Services not reachable

#### Diagnosis
```bash
# Check namespace label
kubectl get namespace cfzt -o jsonpath='{.metadata.labels}'

# Check pod status
kubectl get pods -n cfzt -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'

# Check injection webhook
kubectl get mutatingwebhookconfiguration -n istio-system
```

#### Resolution
```bash
# Add injection label
kubectl label namespace cfzt istio-injection=enabled

# Restart pods to inject sidecar
kubectl rollout restart deployment/<deployment-name> -n cfzt

# Verify injection
kubectl get pods -n cfzt -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'
```

## Debugging Commands

### Proxy Debug
```bash
# Get proxy config
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /config_dump

# Get proxy stats
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats

# Get proxy clusters
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /clusters

# Get proxy routes
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /routes
```

### Istiod Debug
```bash
# Check Istiod status
kubectl get pods -n istio-system -l app=istiod

# Check Istiod logs
kubectl logs -n istio-system -l app=istiod --tail=100

# Check Istiod config
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request GET /config_dump
```

### Network Debug
```bash
# Test connectivity
kubectl exec -it <pod-name> -n cfzt -- curl -v http://<service-name>:<port>/health

# Check network policies
kubectl get networkpolicy -n cfzt

# Check service endpoints
kubectl get endpoints <service-name> -n cfzt
```

## Common Fixes

### Restart All Proxies
```bash
# Restart all sidecar proxies
kubectl rollout restart deployment -n cfzt
```

### Flush Proxy Config
```bash
# Flush proxy config cache
kubectl exec -it istiod-0 -n istio-system -- pilot-agent request POST /quit
```

### Reset Certificates
```bash
# Delete all Istio secrets
kubectl delete secret -n cfzt -l istio=ca-root

# Restart all pods
kubectl rollout restart deployment -n cfzt
```

## Monitoring

### Key Metrics
```bash
# Proxy metrics
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep istio

# Request metrics
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep request

# Error metrics
kubectl exec -it <pod-name> -n cfzt -c istio-proxy -- pilot-agent request GET /stats | grep error
```

### Grafana Dashboards
```bash
# Istio dashboard
open http://grafana:3000/d/istio

# Service dashboard
open http://grafana:3000/d/service
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
- Slack: #incidents
- PagerDuty: Istio Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
