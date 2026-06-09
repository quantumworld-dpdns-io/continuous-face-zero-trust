*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py
Library    ../resources/libraries/AuditLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_001
${TEST_PASSWORD}    test_password_123
${TIMEOUT}    300

*** Test Cases ***
Login With Valid Credentials
    [Documentation]    Test login with valid credentials
    [Tags]    auth    login    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][token]
    Should Not Be Empty    ${response}[body][refresh_token]
    Should Be True    ${response}[body][risk_score] >= 0
    Should Be True    ${response}[body][risk_score] <= 1

Login With Invalid User
    [Documentation]    Test login with invalid user
    [Tags]    auth    login    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "invalid_user", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Invalid credentials

Login With Missing Fields
    [Documentation]    Test login with missing fields
    [Tags]    auth    login    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Missing required fields

Enroll New User
    [Documentation]    Test enrolling a new user
    [Tags]    auth    enrollment    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_enroll", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg", "${CURDIR}/../test_data/faces/left.jpg", "${CURDIR}/../test_data/faces/right.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    Should Not Be Empty    ${response}[body][embedding_id]

Enroll Existing User
    [Documentation]    Test enrolling an existing user
    [Tags]    auth    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    409
    Should Contain    ${response}[body][message]    User already enrolled

Refresh Token
    [Documentation]    Test refreshing a token
    [Tags]    auth    refresh    positive
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

Refresh Invalid Token
    [Documentation]    Test refreshing with invalid token
    [Tags]    auth    refresh    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/refresh
    ...    body=${{"refresh_token": "invalid_token"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Invalid token

Logout
    [Documentation]    Test logout
    [Tags]    auth    logout    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Logout
    ${response}=    Send Request    POST    /api/v1/auth/logout
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]

Get Session
    [Documentation]    Test getting session details
    [Tags]    auth    session    positive
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
    [Tags]    auth    session    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/sessions/test_session
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Unauthorized

Continuous Verify Success
    [Documentation]    Test continuous verification success
    [Tags]    auth    continuous_verify    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Continuous verify
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    Should Be True    ${response}[body][similarity] > 0.85
    Should Be Equal As Strings    ${response}[body][action]    allow

Continuous Verify Failure
    [Documentation]    Test continuous verification failure
    [Tags]    auth    continuous_verify    negative
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Continuous verify with different face
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/different.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] < 0.85
    Should Not Be Equal As Strings    ${response}[body][action]    allow
