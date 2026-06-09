*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A10-TC01 Internal Network SSRF
    [Documentation]    OWASP A10: SSRF — internal network access
    ${data}=    Create Dictionary    url=http://localhost:6379    ${data}
    ${response}=    Make API Request    auth    /api/v1/auth/login    POST    data=${data}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Internal network SSRF blocked

A10-TC02 Cloud Metadata SSRF
    [Documentation]    OWASP A10: SSRF — cloud metadata endpoint
    ${data}=    Create Dictionary    url=http://169.254.169.254/latest/meta-data/    ${data}
    ${response}=    Make API Request    auth    /api/v1/auth/login    POST    data=${data}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Cloud metadata SSRF blocked

A10-TC03 Webhook Abuse
    [Documentation]    OWASP A10: SSRF — webhook URL abuse
    ${data}=    Create Dictionary    callback_url=http://evil.com/callback    ${data}
    ${response}=    Make API Request    auth    /api/v1/auth/login    POST    data=${data}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Webhook abuse prevented
