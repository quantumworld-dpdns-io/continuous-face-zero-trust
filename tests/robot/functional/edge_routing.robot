*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
Edge Gateway Health Check
    [Documentation]    Test edge gateway health check
    [Tags]    edge    health    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/edge/health
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Equal As Strings    ${response}[body][status]    healthy
    Should Not Be Empty    ${response}[body][version]
    Should Be True    ${response}[body][uptime] > 0
    Should Not Be Empty    ${response}[body][region]

Edge Gateway Configuration
    [Documentation]    Test edge gateway configuration
    [Tags]    edge    config    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/edge/config
    ...    headers=${{"Authorization": "Bearer test_token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][rate_limiting]
    Should Not Be Empty    ${response}[body][waf]
    Should Not Be Empty    ${response}[body][tls]

Edge Gateway Routes
    [Documentation]    Test edge gateway routes
    [Tags]    edge    routes    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/edge/routes
    ...    headers=${{"Authorization": "Bearer test_token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][routes]

Edge Gateway Metrics
    [Documentation]    Test edge gateway metrics
    [Tags]    edge    metrics    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/edge/metrics
    ...    headers=${{"Authorization": "Bearer test_token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][requests_total] >= 0
    Should Be True    ${response}[body][requests_per_second] >= 0
    Should Be True    ${response}[body][error_rate] >= 0
    Should Be True    ${response}[body][latency_p99] >= 0
    Should Be True    ${response}[body][active_connections] >= 0

Edge Gateway Rate Limiting
    [Documentation]    Test edge gateway rate limiting
    [Tags]    edge    rate_limit    positive
    [Timeout]    ${TIMEOUT}
    
    # Send multiple requests
    FOR    ${i}    IN RANGE    10
        ${response}=    Send Request    GET    /api/v1/edge/health
        
        Should Be Equal As Strings    ${response}[status]    200
    END

Edge Gateway WAF
    [Documentation]    Test edge gateway WAF
    [Tags]    edge    waf    positive
    [Timeout]    ${TIMEOUT}
    
    # Test SQL injection
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "' OR '1'='1", "face_image": "test"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    
    # Test XSS
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "<script>alert('xss')</script>", "face_image": "test"}}
    
    Should Be Equal As Strings    ${response}[status]    400

Edge Gateway TLS
    [Documentation]    Test edge gateway TLS
    [Tags]    edge    tls    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/edge/config
    ...    headers=${{"Authorization": "Bearer test_token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Equal As Strings    ${response}[body][tls][version]    1.3
    Should Be True    ${response}[body][tls][pqc_enabled]

Edge Gateway Performance
    [Documentation]    Test edge gateway performance
    [Tags]    edge    performance
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    GET    /api/v1/edge/health
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 50
