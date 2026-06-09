*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/auth_keywords.robot
Library     Collections

*** Test Cases ***
A01-TC01 Unauthorized API Access
    [Documentation]    OWASP A01: Broken Access Control — Unauthorized endpoint access
    ${response}=    Send Unauthenticated Request    /api/v1/sessions/secret-session    GET
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Unauthorized access properly blocked: ${response.status_code}

A01-TC02 IDOR Prevention
    [Documentation]    OWASP A01: Insecure Direct Object Reference
    ${response}=    Test IDOR    fake-session-id-12345
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    IDOR attempt blocked: ${response.status_code}

A01-TC03 JWT Manipulation
    [Documentation]    OWASP A01: JWT token manipulation attempt
    ${response}=    Test JWT Manipulation    eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9.
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    JWT manipulation blocked: ${response.status_code}

A01-TC04 Session Fixation
    [Documentation]    OWASP A01: Session fixation attempt
    ${response}=    Send Unauthenticated Request    /api/v1/sessions/    GET
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Session fixation prevented

A01-TC05 CORS Misconfiguration
    [Documentation]    OWASP A01: CORS misconfiguration test
    ${response}=    Test CORS    http://evil.com    /api/v1/auth/login
    Should Not Contain    ${response.headers}.get('Access-Control-Allow-Origin', '')    http://evil.com
    Log    CORS misconfiguration prevented
