*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/auth_keywords.robot
Library     Collections

*** Test Cases ***
A07-TC01 Brute Force Protection
    [Documentation]    OWASP A07: Authentication Failures — brute force
    ${responses}=    Test Rate Limiting    /api/v1/auth/login    100
    ${blocked}=    Set Variable    ${False}
    FOR    ${resp}    IN    @{responses}
        IF    ${resp.status_code} == 429    Set Variable    ${True}    ${blocked}
    END
    Should Be True    ${blocked}    Brute force should trigger rate limiting
    Log    Brute force protection verified

A07-TC02 Face Auth Bypass Attempt
    [Documentation]    OWASP A07: Face authentication bypass
    ${data}=    Create Dictionary    device_id=test-bypass    platform=unknown
    ${response}=    Make API Request    auth    /api/v1/auth/login    POST    data=${data}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Face auth bypass prevented

A07-TC03 Session Management
    [Documentation]    OWASP A07: Session management validation
    ${response}=    Make API Request    auth    /api/v1/sessions/nonexistent    GET    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Session management verified
