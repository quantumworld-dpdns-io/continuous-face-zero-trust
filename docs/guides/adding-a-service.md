# Adding a New Microservice

## Overview

This guide covers adding a new microservice to the CFZT system.

## Steps

### 1. Create Service Directory

```bash
# Create directory structure
mkdir -p services/new-service
cd services/new-service

# Initialize project
# For Go
go mod init github.com/cfzt/new-service

# For Python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# For Rust
cargo init
```

### 2. Create Dockerfile

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server ./cmd/server

FROM alpine:3.18
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/server .

EXPOSE 8080
CMD ["./server"]
```

### 3. Create Kubernetes Manifests

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: new-service
  namespace: cfzt
  labels:
    app: new-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: new-service
  template:
    metadata:
      labels:
        app: new-service
    spec:
      containers:
      - name: new-service
        image: cfzt/new-service:latest
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 8081
          name: grpc
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: new-service
  namespace: cfzt
spec:
  selector:
    app: new-service
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  - name: grpc
    port: 8081
    targetPort: 8081
```

### 4. Create Istio Configuration

```yaml
# k8s/istio/peer-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: new-service
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: new-service
  mtls:
    mode: STRICT
```

```yaml
# k8s/istio/authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: new-service
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: new-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/cfzt/sa/edge-gateway"
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/*"]
```

```yaml
# k8s/istio/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: new-service
  namespace: cfzt
spec:
  hosts:
  - new-service
  http:
  - route:
    - destination:
        host: new-service
        subset: v1
      weight: 100
    timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
```

### 5. Create API Definition

```protobuf
// proto/new-service.proto
syntax = "proto3";

package cfzt.newservice;

service NewService {
  rpc GetResource(GetResourceRequest) returns (GetResourceResponse);
  rpc CreateResource(CreateResourceRequest) returns (CreateResourceResponse);
}

message GetResourceRequest {
  string id = 1;
}

message GetResourceResponse {
  string id = 1;
  string name = 2;
  string created_at = 3;
}

message CreateResourceRequest {
  string name = 1;
}

message CreateResourceResponse {
  string id = 1;
  bool success = 2;
}
```

### 6. Create OpenAPI Specification

```yaml
# api/openapi.yaml
openapi: 3.1.0
info:
  title: New Service API
  version: 1.0.0

paths:
  /api/v1/resources/{id}:
    get:
      summary: Get resource
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Resource found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'

  /api/v1/resources:
    post:
      summary: Create resource
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResourceRequest'
      responses:
        '201':
          description: Resource created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateResourceResponse'

components:
  schemas:
    Resource:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        created_at:
          type: string
          format: date-time

    CreateResourceRequest:
      type: object
      properties:
        name:
          type: string

    CreateResourceResponse:
      type: object
      properties:
        id:
          type: string
        success:
          type: boolean
```

### 7. Create Tests

```python
# tests/test_new_service.py
import pytest
from cfzt.new_service import NewServiceClient

@pytest.fixture
def client():
    return NewServiceClient()

def test_get_resource(client):
    response = client.get_resource("test-id")
    assert response.id == "test-id"

def test_create_resource(client):
    response = client.create_resource(name="test-resource")
    assert response.success
    assert response.id is not None
```

```robot
# tests/robot/functional/new_service.robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io

*** Test Cases ***
Get Resource
    [Documentation]    Test getting a resource
    ${response}=    Send Request    GET    /api/v1/resources/test-id
    Should Be Equal As Strings    ${response}[status]    200

Create Resource
    [Documentation]    Test creating a resource
    ${response}=    Send Request    POST    /api/v1/resources
    ...    body=${{"name": "test-resource"}}
    Should Be Equal As Strings    ${response}[status]    201
```

### 8. Create Monitoring Configuration

```yaml
# k8s/monitoring/service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: new-service
  namespace: cfzt
spec:
  selector:
    matchLabels:
      app: new-service
  endpoints:
  - port: http
    interval: 15s
    path: /metrics
```

```yaml
# k8s/monitoring/prometheus-rule.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: new-service
  namespace: cfzt
spec:
  groups:
  - name: new-service
    rules:
    - alert: NewServiceHighErrorRate
      expr: rate(http_requests_total{namespace="cfzt",app="new-service",status=~"5.."}[5m]) / rate(http_requests_total{namespace="cfzt",app="new-service"}[5m]) > 0.05
      for: 5m
      labels:
        severity: warning
```

### 9. Create CI/CD Configuration

```yaml
# .github/workflows/new-service.yml
name: New Service CI

on:
  push:
    branches: [main]
    paths:
      - 'services/new-service/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/new-service/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd services/new-service
          go test ./...

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: |
          cd services/new-service
          docker build -t cfzt/new-service:${{ github.sha }} .
      - name: Push to registry
        run: |
          docker push cfzt/new-service:${{ github.sha }}
```

### 10. Update Documentation

```markdown
# New Service

## Overview
Brief description of the new service.

## API
- [OpenAPI Specification](../api/new-service-api.yaml)
- [gRPC Service Definition](../api/grpc-services.md)

## Configuration
- Environment variables
- Configuration files

## Development
- Local setup
- Testing

## Deployment
- Kubernetes manifests
- CI/CD pipeline
```

### 11. Create Pull Request

```bash
# Stage changes
git add services/new-service/
git add k8s/new-service/
git add api/new-service-api.yaml
git add tests/robot/functional/new_service.robot
git add .github/workflows/new-service.yml

# Commit
git commit -m "feat: add new-service microservice"

# Push
git push origin feature/new-service

# Create PR
gh pr create --title "feat: add new-service microservice" --body "Adds new-service microservice"
```

## Checklist

- [ ] Service directory created
- [ ] Dockerfile created
- [ ] Kubernetes manifests created
- [ ] Istio configuration created
- [ ] API definition created
- [ ] OpenAPI specification created
- [ ] Tests created
- [ ] Monitoring configuration created
- [ ] CI/CD configuration created
- [ ] Documentation updated
- [ ] Pull request created
