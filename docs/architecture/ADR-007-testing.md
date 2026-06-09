# ADR-007: Test Strategy

## Status

Accepted

## Context

We need a comprehensive testing strategy that covers unit, integration, end-to-end, performance, and security testing.

## Decision

### Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E       │  10%
                    │  (Robot)    │
                    ├─────────────┤
                    │ Integration │  20%
                    │  (pytest,   │
                    │   go test)  │
                    ├─────────────┤
                    │    Unit     │  70%
                    │  (pytest,   │
                    │   go test,  │
                    │   cargo test)│
                    └─────────────┘
```

### Testing Tools

| Level | Language | Tool | Coverage Target |
|-------|----------|------|-----------------|
| Unit | Python | pytest | 90% |
| Unit | Go | go test | 90% |
| Unit | Rust | cargo test | 90% |
| Integration | Python | pytest + testcontainers | 80% |
| Integration | Go | go test + testcontainers | 80% |
| E2E | All | Robot Framework | Critical paths |
| Performance | All | Robot Framework + k6 | SLA validation |
| Security | All | OWASP ZAP, Bandit | OWASP Top 10 |

### Test Categories

#### 1. Unit Tests

```python
# Python Unit Test Example
class TestFaceEmbedding:
    def test_embedding_generation(self):
        """Test face embedding generation."""
        model = ArcFaceModel()
        image = load_test_image("face_001.jpg")
        
        embedding = model.embed(image)
        
        assert embedding.shape == (512,)
        assert np.linalg.norm(embedding) == pytest.approx(1.0, abs=1e-6)
    
    def test_embedding_similarity(self):
        """Test embedding similarity calculation."""
        model = ArcFaceModel()
        image1 = load_test_image("face_001.jpg")
        image2 = load_test_image("face_001.jpg")  # Same person
        
        emb1 = model.embed(image1)
        emb2 = model.embed(image2)
        
        similarity = cosine_similarity(emb1, emb2)
        assert similarity > 0.95
```

```go
// Go Unit Test Example
func TestAuthService_Login(t *testing.T) {
    service := NewAuthService(mockDB, mockRedis, mockFaceML)
    
    req := &pb.LoginRequest{
        UserId:    "user-123",
        DeviceId:  "device-456",
        FaceImage: loadTestImage("face_001.jpg"),
    }
    
    resp, err := service.Login(context.Background(), req)
    
    assert.NoError(t, err)
    assert.NotEmpty(t, resp.Token)
    assert.Greater(t, resp.RiskScore, 0.0)
}
```

```rust
// Rust Unit Test Example
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kyber_key_generation() {
        let keypair = kyber::keypair();
        
        assert_eq!(keypair.public_key().len(), 1568);
        assert_eq!(keypair.private_key().len(), 3168);
    }
    
    #[test]
    fn test_kyber_encapsulation() {
        let keypair = kyber::keypair();
        let (ciphertext, shared_secret) = kyber::encapsulate(keypair.public_key());
        
        let decrypted_secret = kyber::decapsulate(&ciphertext, keypair.private_key());
        
        assert_eq!(shared_secret, decrypted_secret);
    }
}
```

#### 2. Integration Tests

```python
# Integration Test Example
@pytest.mark.integration
class TestAuthFlow:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.auth_service = AuthServiceClient()
        self.face_ml_service = FaceMLServiceClient()
        self.redis = RedisClient()
    
    def test_complete_auth_flow(self):
        """Test complete authentication flow."""
        # Enroll
        enroll_resp = self.auth_service.enroll(
            user_id="test-user",
            face_images=load_test_images("test_user/")
        )
        assert enroll_resp.success
        
        # Login
        login_resp = self.auth_service.login(
            user_id="test-user",
            face_image=load_test_image("test_user/front.jpg")
        )
        assert login_resp.success
        assert login_resp.token
        
        # Continuous verify
        verify_resp = self.auth_service.verify(
            token=login_resp.token,
            face_image=load_test_image("test_user/front_30s.jpg")
        )
        assert verify_resp.success
        assert verify_resp.similarity > 0.85
```

#### 3. End-to-End Tests (Robot Framework)

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_001

*** Test Cases ***
Complete Auth Flow
    [Documentation]    Test complete authentication flow
    ${token}=    Enroll User    ${TEST_USER}    ${CURDIR}/../test_data/faces/
    Should Not Be Empty    ${token}
    
    ${verify_result}=    Verify Identity    ${token}    ${CURDIR}/../test_data/faces/front.jpg
    Should Be True    ${verify_result}[success]
    Should Be True    ${verify_result}[similarity] > 0.85
```

#### 4. Performance Tests

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py

*** Variables ***
${TARGET_LATENCY_MS}    200
${CONCURRENT_USERS}    1000

*** Test Cases ***
Auth Latency Under Load
    [Documentation]    Verify auth latency <200ms under load
    ${results}=    Run Concurrent Requests
    ...    ${CONCURRENT_USERS}
    ...    ${BASE_URL}/api/v1/auth/login
    ...    method=POST
    ...    body=${LOGIN_PAYLOAD}
    
    ${p99_latency}=    Calculate P99    ${results}[latencies]
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}
```

#### 5. Security Tests

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Test Cases ***
SQL Injection Prevention
    [Documentation]    Verify SQL injection is prevented
    ${payload}=    Set Variable    ' OR '1'='1
    ${response}=    Send Request    POST    /api/v1/auth/login    body=${payload}
    Should Be Equal As Strings    ${response}[status]    400

XSS Prevention
    [Documentation]    Verify XSS is prevented
    ${payload}=    Set Variable    <script>alert('xss')</script>
    ${response}=    Send Request    POST    /api/v1/auth/login    body=${payload}
    Should Not Contain    ${response}[body]    <script>

CSRF Protection
    [Documentation]    Verify CSRF protection
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    headers=${{"Origin": "https://evil.com"}}
    Should Be Equal As Strings    ${response}[status]    403
```

### Test Data Management

```python
class TestDataManager:
    def __init__(self):
        self.test_images = self.load_test_images()
        self.test_users = self.create_test_users()
    
    def load_test_images(self) -> Dict[str, List[np.ndarray]]:
        """Load test face images."""
        return {
            "user_001": [
                load_image("test_data/user_001/front.jpg"),
                load_image("test_data/user_001/left.jpg"),
                load_image("test_data/user_001/right.jpg"),
            ],
            "user_002": [...],
        }
    
    def create_test_users(self) -> List[dict]:
        """Create test users."""
        return [
            {"user_id": "user_001", "name": "Test User 1"},
            {"user_id": "user_002", "name": "Test User 2"},
        ]
```

### CI/CD Integration

```yaml
# GitHub Actions Test Workflow
name: Tests
on: [push, pull_request]
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Python tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml
      - name: Run Go tests
        run: go test ./... -v -coverprofile=coverage.out
      - name: Run Rust tests
        run: cargo test --verbose
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      redis:
        image: redis:7.0
        ports: [6379:6379]
      cockroachdb:
        image: cockroachdb/cockroach:latest
        ports: [26257:26257]
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest tests/integration/ -v
  
  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - name: Run Robot Framework tests
        run: robot tests/robot/functional/
  
  performance-tests:
    runs-on: ubuntu-latest
    needs: e2e-tests
    steps:
      - uses: actions/checkout@v4
      - name: Run performance tests
        run: robot tests/robot/performance/
```

## Consequences

### Positive
- Comprehensive test coverage
- Automated testing in CI/CD
- Performance validation
- Security testing

### Negative
- Test maintenance overhead
- Slow test execution
- Flaky tests
- Test data management complexity

### Risks
- Test environment drift
- Flaky tests blocking deployments
- Insufficient test coverage
- Performance test reproducibility

## Alternatives Considered

### Manual Testing Only
- Pros: Human judgment
- Cons: Slow, error-prone, not scalable

### Property-Based Testing
- Pros: Finds edge cases
- Cons: Complex, slow

### Mutation Testing
- Pros: Validates test quality
- Cons: Slow, resource-intensive

## Review Date

2025-03-01
