*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    JSONLibrary

*** Keywords ***
Send Unauthenticated Request
    [Arguments]    ${url}    ${method}=GET
    ${response}=    Run Keyword If    '${method}' == 'GET'    Get Request    auth    ${url}
    ...    ELSE IF    '${method}' == 'POST'    Post Request    auth    ${url}    data= {}
    ...    ELSE    Delete Request    auth    ${url}
    [Return]    ${response}

Attempt Token Manipulation
    [Arguments]    ${token}    ${payload_modification}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${response}=    Get Request    auth    /api/v1/sessions/test    headers=${headers}
    [Return]    ${response}

Test CORS
    [Arguments]    ${origin}    ${url}
    ${headers}=    Create Dictionary    Origin=${origin}
    ${response}=    Options Request    auth    ${url}    headers=${headers}
    [Return]    ${response}

Test Rate Limiting
    [Arguments]    ${url}    ${attempts}=100
    ${responses}=    Create List
    FOR    ${i}    IN RANGE    ${attempts}
        ${response}=    Get Request    auth    ${url}    expected_status=any
        Append To List    ${responses}    ${response}
    END
    [Return]    ${responses}

Test SQL Injection
    [Arguments]    ${input_value}
    ${data}=    Create Dictionary    query=${input_value}
    ${response}=    Post Request    auth    /api/v1/auth/login    json=${data}    expected_status=any
    [Return]    ${response}

Test XSS Attempt
    [Arguments]    ${xss_payload}
    ${data}=    Create Dictionary    name=${xss_payload}
    ${response}=    Post Request    auth    /api/v1/enrollment/enroll    json=${data}    expected_status=any
    [Return]    ${response}

Test IDOR
    [Arguments]    ${other_session_id}
    ${response}=    Get Request    auth    /api/v1/sessions/${other_session_id}    expected_status=any
    [Return]    ${response}

Test JWT Manipulation
    [Arguments]    ${token}    ${algorithm}=none
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${response}=    Get Request    auth    /api/v1/sessions/test    headers=${headers}    expected_status=any
    [Return]    ${response}

Verify Security Headers
    [Arguments]    ${response}
    Dictionary Should Contain Key    ${response.headers}    X-Content-Type-Options
    Dictionary Should Contain Key    ${response.headers}    X-Frame-Options
    Dictionary Should Contain Key    ${response.headers}    Strict-Transport-Security
    Dictionary Should Contain Key    ${response.headers}    X-XSS-Protection
    Should Be Equal    ${response.headers}[X-Content-Type-Options]    nosniff
    Should Be Equal    ${response.headers}[X-Frame-Options]    DENY
