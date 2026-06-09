# ADR-005: Istio Service Mesh Adoption

## Status

Accepted

## Context

We need a service mesh to provide mTLS, traffic management, and observability across our microservices.

## Decision

### Service Mesh Selection

| Feature | Istio | Linkerd | Consul |
|---------|-------|---------|--------|
| mTLS | ✅ | ✅ | ✅ |
| Traffic Management | ✅ | ❌ | ✅ |
| Observability | ✅ | ✅ | ✅ |
| Wasm Extensions | ✅ | ❌ | ✅ |
| Multi-cluster | ✅ | ✅ | ✅ |
| Learning Curve | Medium | Low | Medium |
| Performance Overhead | ~1ms | ~0.5ms | ~0.8ms |
| Community | Large | Medium | Medium |

**Selected: Istio**

**Rationale:**
- Most feature-complete
- Strong multi-cluster support
- Wasm extensibility
- Large community and ecosystem

### Installation Profile

```bash
# Install Istio with production profile
istioctl install --set profile=default \
  --set values.pilot.resources.requests.cpu=500m \
  --set values.pilot.resources.requests.memory=2Gi \
  --set values.global.proxy.resources.requests.cpu=100m \
  --set values.global.proxy.resources.requests.memory=128Mi \
  --set values.global.proxy.resources.limits.cpu=2000m \
  --set values.global.proxy.resources.limits.memory=1Gi \
  --set meshConfig.enableTracing=true \
  --set meshConfig.defaultConfig.tracing.sampling=10
```

### Configuration

```yaml
# Peer Authentication (mTLS)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: cfzt
spec:
  mtls:
    mode: STRICT

---
# Authorization Policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: cfzt
spec:
  {}

---
# Request Authentication
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: auth-service
  jwtRules:
  - issuer: "https://auth.cfzt.io"
    jwksUri: "https://auth.cfzt.io/.well-known/jwks.json"
```

### Traffic Management

```yaml
# Circuit Breaking
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: auth-service
  namespace: cfzt
spec:
  host: auth-service.cfzt.svc.cluster.local
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

---
# Virtual Service
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

### Observability

```yaml
# Telemetry
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: mesh-telemetry
  namespace: istio-system
spec:
  metrics:
  - providers:
    - name: prometheus
  accessLogging:
  - providers:
    - name: envoy
  tracing:
  - providers:
    - name: jaeger
    randomSamplingPercentage: 10
```

## Consequences

### Positive
- Strong security with mTLS everywhere
- Rich traffic management capabilities
- Comprehensive observability
- Multi-cluster support

### Negative
- Performance overhead (~1ms per hop)
- Increased resource consumption
- Complex debugging
- Steep learning curve

### Risks
- Istio upgrades may break services
- Sidecar injection failures
- Certificate rotation issues
- Memory leaks in sidecars

## Alternatives Considered

### Linkerd
- Pros: Simpler, lower overhead
- Cons: Fewer features, less extensibility

### Consul Connect
- Pros: Service discovery integration
- Cons: Weaker traffic management

### No Service Mesh
- Pros: No overhead, simpler
- Cons: Manual mTLS, no traffic management

## Review Date

2025-03-01
