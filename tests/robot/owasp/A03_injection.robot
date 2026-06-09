*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A03-TC01 SQL Injection
    [Documentation]    OWASP A03: SQL Injection attempt
    ${response}=    Test SQL Injection    ' OR 1=1 --
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    SQL injection blocked: ${response.status_code}

A03-TC02 NoSQL Injection (Redis)
    [Documentation]    OWASP A03: NoSQL injection attempt against Redis
    ${data}=    Create Dictionary    session_id={"$gt": ""}    {"$ne": ""}
    ${response}=    Make API Request    cache    /api/v1/cache/get    POST    data=${data}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    NoSQL injection blocked

A03-TC03 Command Injection
    [Documentation]    OWASP A03: OS command injection attempt
    ${response}=    Test SQL Injection    ; cat /etc/passwd
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Command injection blocked

A03-TC04 SSRF Prevention
    [Documentation]    OWASP A03: Server-Side Request Forgery
    ${data}=    Create Dictionary    url=http://169.254.169.254/latest/meta-data/
    ${response}=    Make API Request    auth    /api/v1/auth/login    POST    data=${data}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    SSRF attempt blocked
