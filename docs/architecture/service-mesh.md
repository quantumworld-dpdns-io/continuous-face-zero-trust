# Istio Service Mesh Architecture

## Overview

The CFZT system uses Istio as its service mesh to provide mTLS, traffic management, security policies, and observability across all microservices.

## Service Mesh Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ISTIO SERVICE MESH                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Ingress Gateway                                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │
│  │  │ Envoy   │  │ TLS      │  │ Rate     │  │ WAF      │         │ │
│  │  │ Proxy   │  │ Termin.  │  │ Limiter  │  │ Filter   │         │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│  ┌───────────────────────────┼───────────────────────────────────────┐ │
│  │                           │                                       │ │
│  │  ┌──────────────┐  ┌─────┴──────┐  ┌──────────────┐             │ │
│  │  │ auth-service │  │face-ml-svc │  │pqc-crypto-svc│             │ │
│  │  │              │  │            │  │              │             │ │
│  │  │ ┌──────────┐ │  │ ┌────────┐ │  │ ┌──────────┐ │             │ │
│  │  │ │  Envoy   │ │  │ │  Envoy │ │  │ │  Envoy   │ │             │ │
│  │  │ │  Sidecar │ │  │ │ Sidecar│ │  │ │  Sidecar │ │             │ │
│  │  │ └──────────┘ │  │ └────────┘ │  │ └──────────┘ │             │ │
│  │  └──────────────┘  └────────────┘  └──────────────┘             │ │
│  │                           │                                       │ │
│  │  ┌──────────────┐  ┌─────┴──────┐  ┌──────────────┐             │ │
│  │  │zk-proofs-svc │  │vector-db-svc│ │cache-store-svc│            │ │
│  │  │              │  │            │  │              │             │ │
│  │  │ ┌──────────┐ │  │ ┌────────┐ │  │ ┌──────────┐ │             │ │
│  │  │ │  Envoy   │ │  │ │  Envoy │ │  │ │  Envoy   │ │             │ │
│  │  │ │  Sidecar │ │  │ │ Sidecar│ │  │ │  Sidecar │ │             │ │
│  │  │ └──────────┘ │  │ └────────┘ │  │ └──────────┘ │             │ │
│  │  └──────────────┘  └────────────┘  └──────────────┘             │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Istio Control Plane                                               │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │
│  │  │  Istiod  │  │ Citadel  │  │  Galley  │  │  Pilot   │         │ │
│  │  │ (Config) │  │  (Cert)  │  │ (Validate)│  │  (xDS)   │         │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## mTLS Configuration

### Strict mTLS Mode

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: cfzt
spec:
  mtls:
    mode: STRICT
```

### Per-Service mTLS

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: face-ml-service
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: face-ml-service
  mtls:
    mode: STRICT
  portLevelMtls:
    8083:  # HTTP port
      mode: DISABLE  # For health checks only
```

## Authorization Policies

### Service-to-Service Access

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: auth-service-policy
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
        - "cluster.local/ns/cfzt/sa/analytics-service"
    to:
    - operation:
        methods: ["POST", "GET"]
        paths: ["/api/v1/auth/*", "/api/v1/sessions/*"]
  - from:
    - source:
        principals:
        - "cluster.local/ns/cfzt/sa/face-ml-service"
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/auth/verify"]
```

### Deny All Default

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: cfzt
spec:
  {}
```

## Traffic Management

### Circuit Breaking

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: auth-service-circuit-breaker
  namespace: cfzt
spec:
  host: auth-service.cfzt.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
        maxRetries: 3
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

### Load Balancing

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: auth-service-lb
  namespace: cfzt
spec:
  host: auth-service.cfzt.svc.cluster.local
  trafficPolicy:
    loadBalancer:
      simple: LEAST_REQUEST
    connectionPool:
      tcp:
        maxConnections: 100
```

### Retries and Timeouts

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: auth-service-vs
  namespace: cfzt
spec:
  hosts:
  - auth-service
  http:
  - route:
    - destination:
        host: auth-service
        subset: v1
      weight: 100
    timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: gateway-error,connect-failure,refused-stream
```

### Canary Deployments

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: auth-service-canary
  namespace: cfzt
spec:
  hosts:
  - auth-service
  http:
  - route:
    - destination:
        host: auth-service
        subset: stable
      weight: 90
    - destination:
        host: auth-service
        subset: canary
      weight: 10
```

## Security Policies

### Request Authentication

```yaml
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
    forwardOriginalToken: true
```

### IP Allowlisting

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: ip-allowlist
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: edge-gateway
  action: ALLOW
  rules:
  - from:
    - source:
        ipBlocks:
        - "10.0.0.0/8"
        - "172.16.0.0/12"
    to:
    - operation:
        paths: ["/api/v1/*"]
```

## Observability

### Telemetry Configuration

```yaml
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

### Service Monitor (Prometheus)

```yaml
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

## Istio Configuration

### Istioctl Install Profile

```bash
istioctl install --set profile=default \
  --set values.pilot.resources.requests.cpu=500m \
  --set values.pilot.resources.requests.memory=2Gi \
  --set values.global.proxy.resources.requests.cpu=100m \
  --set values.global.proxy.resources.requests.memory=128Mi \
  --set values.global.proxy.resources.limits.cpu=2000m \
  --set values.global.proxy.resources.limits.memory=1Gi
```

### Namespace Labels

```bash
kubectl label namespace cfzt istio-injection=enabled
```

### Proxy Configuration

```yaml
apiVersion: networking.istio.io/v1beta1
kind: ProxyConfig
metadata:
  name: default
  namespace: cfzt
spec:
  concurrency: 2
  image:
    imageType: DEFAULT
  tracing:
    sampling: 10
    openCensusAgentAddress: "oc-collector.observability:55678"
```
