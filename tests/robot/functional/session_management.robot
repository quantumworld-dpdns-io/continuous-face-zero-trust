*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_session_001
${TIMEOUT}    300

*** Test Cases ***
Create Session
    [Documentation]    Test creating a session
    [Tags]    session    create    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][session_id]
    Should Be Equal As Strings    ${response}[body][status]    active

Get Session Details
    [Documentation]    Test getting session details
    [Tags]    session    get    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    ${session_id}=    Set Variable    ${login_response}[body][session_id]
    
    # Get session
    ${response}=    Send Request    GET    /api/v1/sessions/${session_id}
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Equal As Strings    ${response}[body][session_id]    ${session_id}
    Should Be Equal As Strings    ${response}[body][user_id]    ${TEST_USER}
    Should Be Equal As Strings    ${response}[body][status]    active

Get Session Unauthorized
    [Documentation]    Test getting session without authorization
    [Tags]    session    get    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/sessions/test_session
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Unauthorized

Get Session Not Found
    [Documentation]    Test getting non-existent session
    [Tags]    session    get    negative
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Get non-existent session
    ${response}=    Send Request    GET    /api/v1/sessions/nonexistent_session
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    
    Should Be Equal As Strings    ${response}[status]    404
    Should Contain    ${response}[body][message]    Session not found

Refresh Session
    [Documentation]    Test refreshing a session
    [Tags]    session    refresh    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${refresh_token}=    Set Variable    ${login_response}[body][refresh_token]
    
    # Refresh session
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "${refresh_token}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][token]
    Should Not Be Empty    ${response}[body][refresh_token]

Refresh Invalid Token
    [Documentation]    Test refreshing with invalid token
    [Tags]    session    refresh    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "invalid_token"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Invalid token

Invalidate Session
    [Documentation]    Test invalidating a session
    [Tags]    session    invalidate    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Logout (invalidate session)
    ${response}=    Send Request    POST    /api/v1/auth/logout
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    
    # Try to use invalidated session
    ${verify_response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${verify_response}[status]    401

Session Expiration
    [Documentation]    Test session expiration
    [Tags]    session    expiration
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Wait for session to expire
    Sleep    60s
    
    # Try to use expired session
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Session expired

Multiple Sessions
    [Documentation]    Test multiple sessions for same user
    [Tags]    session    multiple
    [Timeout]    ${TIMEOUT}
    
    # Create multiple sessions
    @{sessions}=    Create List
    FOR    ${i}    IN RANGE    3
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_00${i}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        
        Append To List    ${sessions}    ${response}[body][session_id]
    END
    
    # Verify all sessions are active
    FOR    ${session_id}    IN    @{sessions}
        ${response}=    Send Request    GET    /api/v1/sessions/${session_id}
        ...    headers=${{"Authorization": "Bearer ${sessions}[0]"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Be Equal As Strings    ${response}[body][status]    active
    END
