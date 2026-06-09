*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    JSONLibrary

*** Keywords ***
Make API Request
    [Arguments]    ${service}    ${endpoint}    ${method}=GET    ${data}=${None}    ${headers}=${None}    ${expected_status}=200
    ${response}=    Run Keyword If    '${method}' == 'GET'    Get Request    ${service}    ${endpoint}    headers=${headers}    expected_status=${expected_status}
    ...    ELSE IF    '${method}' == 'POST'    Post Request    ${service}    ${endpoint}    json=${data}    headers=${headers}    expected_status=${expected_status}
    ...    ELSE IF    '${method}' == 'PUT'    Put Request    ${service}    ${endpoint}    json=${data}    headers=${headers}    expected_status=${expected_status}
    ...    ELSE    Delete Request    ${service}    ${endpoint}    headers=${headers}    expected_status=${expected_status}
    [Return]    ${response}

Validate JSON Response
    [Arguments]    ${response}    ${expected_keys}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    FOR    ${key}    IN    @{expected_keys}
        Dictionary Should Contain Key    ${json}    ${key}
    END
    [Return]    ${json}

Check Response Time
    [Arguments]    ${response}    ${max_ms}=1000
    ${elapsed_ms}=    Evaluate    ${response.elapsed.total_seconds()} * 1000
    Should Be True    ${elapsed_ms} < ${max_ms}    Response took ${elapsed_ms}ms, max allowed is ${max_ms}ms
