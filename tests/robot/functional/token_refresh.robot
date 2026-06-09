*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_token_001
${TIMEOUT}    300

*** Test Cases ***
Refresh Token Success
    [Documentation]    Test refreshing token successfully
    [Tags]    token    refresh    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Refresh token
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "${refresh_token}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][token]
    Should Not Be Empty    ${response}[body][refresh_token]
    Should Be True    ${response}[body][expires_in] > 0

Refresh Token Invalid
    [Documentation]    Test refreshing with invalid token
    [Tags]    token    refresh    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "invalid_token"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Invalid token

Refresh Token Expired
    [Documentation]    Test refreshing with expired token
    [Tags]    token    refresh    negative
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Wait for token to expire
    Sleep    60s
    
    # Try to refresh
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "${refresh_token}"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Token expired

Refresh Token Multiple Times
    [Documentation]    Test refreshing token multiple times
    [Tags]    token    refresh    multiple
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Refresh multiple times
    FOR    ${i}    IN RANGE    5
        ${response}=    Send Request    POST    /api/v1/auth/refresh
        ...    body=${{"refresh_token": "${refresh_token}"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][token]
        Should Not Be Empty    ${response}[body][refresh_token]
        
        ${refresh_token}=    Set Variable    ${response}[body][refresh_token]
    END

Refresh Token Rotation
    [Documentation]    Test token rotation on refresh
    [Tags]    token    refresh    rotation
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token_1}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Refresh token
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "${refresh_token_1}"}}
    
    ${refresh_token_2}=    Set Variable    ${response}[body][refresh_token]
    
    # Verify tokens are different
    Should Not Be Equal As Strings    ${refresh_token_1}    ${refresh_token_2}
    
    # Try to use old refresh token
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "${refresh_token_1}"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Invalid token

Refresh Token Use New Token
    [Documentation]    Test using new token after refresh
    [Tags]    token    refresh    use
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Refresh token
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "${refresh_token}"}}
    
    ${new_token}=    Set Variable    ${response}[body][token]
    
    # Use new token
    ${verify_response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${new_token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${verify_response}[status]    200
    Should Be True    ${verify_response}[body][success]

Refresh Token Performance
    [Documentation]    Test refresh token performance
    [Tags]    token    refresh    performance
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Refresh multiple times and measure latency
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/auth/refresh
        ...    body=${{"refresh_token": "${refresh_token}"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
        
        ${refresh_token}=    Set Variable    ${response}[body][refresh_token]
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 100
