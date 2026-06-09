# Robot Framework Test Debugging Guide

## Overview

This runbook covers debugging Robot Framework tests for the CFZT system.

## Common Issues

### 1. Test Failures

#### Symptoms
- Test fails with assertion error
- Test fails with timeout
- Test fails with connection error

#### Diagnosis
```bash
# Run test with debug output
robot --loglevel DEBUG tests/robot/functional/auth_flow.robot

# Run test with traceback
robot -- traceback tests/robot/functional/auth_flow.robot

# Run test with verbose output
robot --loglevel TRACE tests/robot/functional/auth_flow.robot
```

#### Resolution
```python
# Check test data
def check_test_data():
    """Check test data validity."""
    # Verify test images exist
    assert os.path.exists("tests/robot/test_data/faces/front.jpg")
    
    # Verify test user exists
    assert get_test_user("test_user_001") is not None
    
    # Verify test configuration
    assert get_test_config() is not None
```

### 2. Library Import Errors

#### Symptoms
- `ImportError: No module named 'xxx'`
- `AttributeError: 'module' object has no attribute 'xxx'`
- `TypeError: argument 'xxx': xxx is not a valid type`

#### Diagnosis
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Check library installation
pip list | grep robotframework

# Check library import
python -c "from cfzt.robot.libraries import CryptoLibrary"
```

#### Resolution
```bash
# Install missing dependencies
pip install -r requirements.txt

# Install library in development mode
pip install -e packages/python/cfzt-core/

# Check library path
export PYTHONPATH=$PYTHONPATH:$(pwd)/packages/python/cfzt-core/
```

### 3. Connection Errors

#### Symptoms
- `ConnectionRefusedError: [Errno 111] Connection refused`
- `TimeoutError: Connection timed out`
- `URLError: <urlopen error [Errno -2] Name or service not known>`

#### Diagnosis
```bash
# Check service status
kubectl get pods -n cfzt

# Check service endpoints
kubectl get endpoints -n cfzt

# Check network connectivity
kubectl exec -it <pod-name> -n cfzt -- curl -v http://<service>:<port>/health
```

#### Resolution
```bash
# Restart service
kubectl rollout restart deployment/<service> -n cfzt

# Check service logs
kubectl logs -n cfzt -l app=<service> --tail=100

# Check Istio proxy
kubectl logs -n cfzt -l app=<service> -c istio-proxy --tail=100
```

### 4. Assertion Errors

#### Symptoms
- `AssertionError: Expected xxx, got xxx`
- `AssertionError: True is not False`
- `AssertionError: 'xxx' != 'yyy'`

#### Diagnosis
```python
# Debug assertion
def debug_assertion(expected, actual):
    """Debug assertion failure."""
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    print(f"Type Expected: {type(expected)}")
    print(f"Type Actual: {type(actual)}")
    print(f"Equal: {expected == actual}")
```

#### Resolution
```python
# Fix assertion
def fix_assertion(expected, actual):
    """Fix assertion failure."""
    # Convert types
    if isinstance(expected, str) and isinstance(actual, int):
        actual = str(actual)
    
    # Normalize values
    if isinstance(expected, str):
        expected = expected.strip().lower()
        actual = actual.strip().lower()
    
    # Compare
    assert expected == actual, f"Expected {expected}, got {actual}"
```

### 5. Timeout Errors

#### Symptoms
- `TimeoutError: Operation timed out`
- `TimeoutError: Read timed out`
- `TimeoutError: Connection timed out`

#### Diagnosis
```bash
# Check timeout settings
grep -r "timeout" tests/robot/

# Check service response time
curl -w "@curl-format.txt" -o /dev/null -s http://<service>:<port>/health

# Check network latency
ping <service>
```

#### Resolution
```bash
# Increase timeout
robot --variable TIMEOUT:300 tests/robot/functional/auth_flow.robot

# Check service performance
kubectl top pods -n cfzt -l app=<service>

# Check resource limits
kubectl describe pod <pod-name> -n cfzt
```

## Debugging Tools

### 1. Robot Framework Debug Mode

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

### 2. Python Debug Mode

```python
# Add debug output
def debug_test():
    """Debug test."""
    import pdb; pdb.set_trace()
    
    # Or use breakpoint()
    breakpoint()
    
    # Or use logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("Debug message")
```

### 3. Network Debug

```bash
# Check network connectivity
kubectl exec -it <pod-name> -n cfzt -- curl -v http://<service>:<port>/health

# Check DNS resolution
kubectl exec -it <pod-name> -n cfzt -- nslookup <service>

# Check network policies
kubectl get networkpolicy -n cfzt
```

### 4. Log Analysis

```bash
# Collect logs
kubectl logs -n cfzt -l app=<service> --since=1h > /tmp/service-logs.txt

# Analyze logs
grep -i error /tmp/service-logs.txt
grep -i timeout /tmp/service-logs.txt
grep -i connection /tmp/service-logs.txt
```

## Common Fixes

### 1. Fix Import Errors

```bash
# Install missing dependencies
pip install -r requirements.txt

# Install library in development mode
pip install -e packages/python/cfzt-core/

# Check library path
export PYTHONPATH=$PYTHONPATH:$(pwd)/packages/python/cfzt-core/
```

### 2. Fix Connection Errors

```bash
# Restart service
kubectl rollout restart deployment/<service> -n cfzt

# Check service logs
kubectl logs -n cfzt -l app=<service> --tail=100

# Check Istio proxy
kubectl logs -n cfzt -l app=<service> -c istio-proxy --tail=100
```

### 3. Fix Assertion Errors

```python
# Fix assertion
def fix_assertion(expected, actual):
    """Fix assertion failure."""
    # Convert types
    if isinstance(expected, str) and isinstance(actual, int):
        actual = str(actual)
    
    # Normalize values
    if isinstance(expected, str):
        expected = expected.strip().lower()
        actual = actual.strip().lower()
    
    # Compare
    assert expected == actual, f"Expected {expected}, got {actual}"
```

### 4. Fix Timeout Errors

```bash
# Increase timeout
robot --variable TIMEOUT:300 tests/robot/functional/auth_flow.robot

# Check service performance
kubectl top pods -n cfzt -l app=<service>

# Check resource limits
kubectl describe pod <pod-name> -n cfzt
```

## Best Practices

### 1. Test Structure

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
Test Case Name
    [Documentation]    Test description
    [Tags]    tag1    tag2
    
    # Setup
    ${token}=    Setup Test
    
    # Execute
    ${result}=    Execute Test    ${token}
    
    # Verify
    Verify Result    ${result}
    
    # Teardown
    Teardown Test
```

### 2. Library Usage

```python
# Library example
class CryptoLibrary:
    def __init__(self):
        self.client = CryptoClient()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data."""
        return self.client.encrypt(data)
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        return self.client.decrypt(encrypted_data)
```

### 3. Error Handling

```python
# Error handling
def safe_execute(func, *args, **kwargs):
    """Safe execute function."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        raise
```

## Monitoring

### Key Metrics

```yaml
# Robot Framework metrics
- robot_test_total{suite, test, status}
- robot_test_duration_seconds{suite, test}
- robot_test_failure_total{suite, test, reason}
```

### Alerts

```yaml
groups:
- name: robot-framework
  rules:
  - alert: TestFailing
    expr: rate(robot_test_failure_total[5m]) > 0
    for: 5m
    labels:
      severity: warning
    
  - alert: TestSlow
    expr: rate(robot_test_duration_seconds[5m]) > 300
    for: 5m
    labels:
      severity: warning
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | Developer |
| 5-15 min | QA lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #robot-framework
- PagerDuty: Test Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
