# Robot Framework Test Writing Guide

## Overview

This guide covers writing Robot Framework tests for the CFZT system.

## Test Structure

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
${TIMEOUT}    300

*** Test Cases ***
Test Case Name
    [Documentation]    Test description
    [Tags]    tag1    tag2
    [Timeout]    ${TIMEOUT}
    
    # Setup
    ${token}=    Setup Test
    
    # Execute
    ${result}=    Execute Test    ${token}
    
    # Verify
    Verify Result    ${result}
    
    # Teardown
    Teardown Test
```

## Writing Tests

### 1. Functional Tests

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_001

*** Test Cases ***
Login Test
    [Documentation]    Test user login
    [Tags]    auth    login
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][token]

Enrollment Test
    [Documentation]    Test user enrollment
    [Tags]    auth    enrollment
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}", "face_images": ["${CURDIR}/../test_data/faces/"]}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
```

### 2. Performance Tests

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TARGET_LATENCY_MS}    200
${CONCURRENT_USERS}    1000

*** Test Cases ***
Auth Latency Under Load
    [Documentation]    Verify auth latency <200ms under load
    [Tags]    performance    latency
    
    ${results}=    Run Concurrent Requests
    ...    ${CONCURRENT_USERS}
    ...    ${BASE_URL}/api/v1/auth/login
    ...    method=POST
    ...    body=${LOGIN_PAYLOAD}
    
    ${p99_latency}=    Calculate P99    ${results}[latencies]
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

Face Inference Latency
    [Documentation]    Verify face inference <100ms
    [Tags]    performance    latency
    
    ${results}=    Run Concurrent Requests
    ...    ${CONCURRENT_USERS}
    ...    ${BASE_URL}/api/v1/face/embed
    ...    method=POST
    ...    body=${EMBED_PAYLOAD}
    
    ${p99_latency}=    Calculate P99    ${results}[latencies]
    Should Be True    ${p99_latency} < 100
```

### 3. Security Tests

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io

*** Test Cases ***
SQL Injection Prevention
    [Documentation]    Verify SQL injection is prevented
    [Tags]    security    injection
    
    ${payload}=    Set Variable    ' OR '1'='1
    ${response}=    Send Request    POST    /api/v1/auth/login    body=${payload}
    Should Be Equal As Strings    ${response}[status]    400

XSS Prevention
    [Documentation]    Verify XSS is prevented
    [Tags]    security    xss
    
    ${payload}=    Set Variable    <script>alert('xss')</script>
    ${response}=    Send Request    POST    /api/v1/auth/login    body=${payload}
    Should Not Contain    ${response}[body]    <script>

CSRF Protection
    [Documentation]    Verify CSRF protection
    [Tags]    security    csrf
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    headers=${{"Origin": "https://evil.com"}}
    Should Be Equal As Strings    ${response}[status]    403
```

## Custom Libraries

### 1. CryptoLibrary

```python
# CryptoLibrary.py
import hashlib
import hmac
from cryptography.fernet import Fernet

class CryptoLibrary:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def hash_data(self, data: str) -> str:
        """Hash data."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generate_hmac(self, data: str, key: str) -> str:
        """Generate HMAC."""
        return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
```

### 2. FaceMLLibrary

```python
# FaceMLLibrary.py
import requests
import base64

class FaceMLLibrary:
    def __init__(self, base_url: str = "http://localhost:8083"):
        self.base_url = base_url
    
    def detect_faces(self, image_path: str) -> list:
        """Detect faces in image."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            f"{self.base_url}/api/v1/face/detect",
            json={"image": image_data}
        )
        return response.json()["faces"]
    
    def generate_embedding(self, image_path: str) -> list:
        """Generate face embedding."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            f"{self.base_url}/api/v1/face/embed",
            json={"image": image_data}
        )
        return response.json()["embedding"]
    
    def compare_faces(self, embedding1: list, embedding2: list) -> float:
        """Compare face embeddings."""
        response = requests.post(
            f"{self.base_url}/api/v1/face/compare",
            json={"embedding1": embedding1, "embedding2": embedding2}
        )
        return response.json()["similarity"]
    
    def check_liveness(self, image_path: str) -> dict:
        """Check liveness."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            f"{self.base_url}/api/v1/face/liveness",
            json={"image": image_data}
        )
        return response.json()
```

### 3. SecurityLibrary

```python
# SecurityLibrary.py
import requests

class SecurityLibrary:
    def __init__(self, base_url: str = "https://api.cfzt.io"):
        self.base_url = base_url
    
    def send_request(self, method: str, path: str, **kwargs) -> dict:
        """Send HTTP request."""
        url = f"{self.base_url}{path}"
        response = requests.request(method, url, **kwargs)
        return {
            "status": response.status_code,
            "body": response.json() if response.headers.get("content-type") == "application/json" else response.text,
            "headers": dict(response.headers)
        }
    
    def test_sql_injection(self, path: str) -> dict:
        """Test SQL injection."""
        payload = "' OR '1'='1"
        return self.send_request("POST", path, json={"input": payload})
    
    def test_xss(self, path: str) -> dict:
        """Test XSS."""
        payload = "<script>alert('xss')</script>"
        return self.send_request("POST", path, json={"input": payload})
    
    def test_csrf(self, path: str) -> dict:
        """Test CSRF."""
        return self.send_request("POST", path, headers={"Origin": "https://evil.com"})
```

## Best Practices

### 1. Test Organization

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
# Group related tests
# Use descriptive names
# Add documentation
# Add tags for filtering
# Set appropriate timeouts
```

### 2. Data-Driven Tests

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io

*** Test Cases ***
Login Test With Multiple Users
    [Documentation]    Test login with multiple users
    [Tags]    auth    login    data-driven
    
    ${users}=    Create List    user1    user2    user3
    FOR    ${user}    IN    @{users}
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${user}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][token]
    END
```

### 3. Error Handling

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io

*** Test Cases ***
Login Test With Invalid Credentials
    [Documentation]    Test login with invalid credentials
    [Tags]    auth    login    negative
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "invalid_user", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Invalid credentials
```

### 4. Cleanup

```robot
*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_001

*** Test Cases ***
Login Test With Cleanup
    [Documentation]    Test login with cleanup
    [Tags]    auth    login
    
    # Setup
    ${token}=    Login User    ${TEST_USER}
    
    # Execute
    ${response}=    Send Request    GET    /api/v1/sessions/current
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    
    # Verify
    Should Be Equal As Strings    ${response}[status]    200
    
    # Cleanup
    Logout User    ${token}
```

## Running Tests

```bash
# Run all tests
robot tests/robot/functional/

# Run specific test
robot --test "Login Test" tests/robot/functional/

# Run tests with tag
robot --include auth tests/robot/functional/

# Run tests with variable
robot --variable BASE_URL:http://localhost:8081 tests/robot/functional/

# Run tests with log level
robot --loglevel DEBUG tests/robot/functional/
```

## Debugging

```bash
# Run with debug output
robot --loglevel DEBUG tests/robot/functional/auth_flow.robot

# Run with traceback
robot -- traceback tests/robot/functional/auth_flow.robot

# Run with verbose output
robot --loglevel TRACE tests/robot/functional/auth_flow.robot

# Run with dry run
robot --dryrun tests/robot/functional/auth_flow.robot
```

## Resources

- [Robot Framework Documentation](https://robotframework.org/robotframework/)
- [Robot Framework Libraries](https://robotframework.org/#libraries)
- [Robot Framework Tools](https://github.com/robotframework/Tools)
