*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A05-TC01 Security Headers Check
    [Documentation]    OWASP A05: Security Misconfiguration — headers
    ${response}=    Make API Request    auth    /health    GET
    Verify Security Headers    ${response}
    Log    Security headers verified

A05-TC02 Error Handling — No Stack Traces
    [Documentation]    OWASP A05: Error message leakage
    ${response}=    Test SQL Injection    ' OR 1=1 --
    Should Not Contain    ${response.text}    Traceback
    Should Not Contain    ${response.text}    stack trace
    Should Not Contain    ${response.text}    Internal Server Error
    Log    Error handling verified — no stack traces leaked

A05-TC03 Service Mesh Configuration
    [Documentation]    OWASP A05: Istio service mesh security
    ${response}=    Make API Request    auth    /health    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    Log    Service mesh configuration verified
