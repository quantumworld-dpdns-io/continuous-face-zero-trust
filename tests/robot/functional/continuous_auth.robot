*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_continuous_001
${TIMEOUT}    300
${VERIFICATION_INTERVAL}    30

*** Test Cases ***
Continuous Verify Same Face
    [Documentation]    Test continuous verification with same face
    [Tags]    continuous_verify    positive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Continuous verify multiple times
    FOR    ${i}    IN RANGE    5
        ${response}=    Send Request    POST    /api/v1/auth/verify
        ...    headers=${{"Authorization": "Bearer ${token}"}}
        ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Be True    ${response}[body][success]
        Should Be True    ${response}[body][similarity] > 0.85
        
        Sleep    ${VERIFICATION_INTERVAL}s
    END

Continuous Verify Different Face
    [Documentation]    Test continuous verification with different face
    [Tags]    continuous_verify    negative
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

Continuous Verify Expired Session
    [Documentation]    Test continuous verification with expired session
    [Tags]    continuous_verify    negative
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Wait for session to expire
    Sleep    60s
    
    # Try to verify
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    401
    Should Contain    ${response}[body][message]    Session expired

Continuous Verify Risk Score Increase
    [Documentation]    Test risk score increase on low similarity
    [Tags]    continuous_verify    risk
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    ${initial_risk}=    Set Variable    ${login_response}[body][risk_score]
    
    # Verify with lower quality image
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/low_quality.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][risk_score] > ${initial_risk}

Continuous Verify Adaptive Refresh
    [Documentation]    Test adaptive refresh interval
    [Tags]    continuous_verify    adaptive
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Verify with high confidence
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] > 0.95
    Should Be True    ${response}[body][refresh_interval] > 300

Continuous Verify Liveness Challenge
    [Documentation]    Test liveness challenge on low confidence
    [Tags]    continuous_verify    liveness
    [Timeout]    ${TIMEOUT}
    
    # First login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    ${token}=    Set Variable    ${login_response}[body][token]
    
    # Verify with photo
    ${response}=    Send Request    POST    /api/v1/auth/verify
    ...    headers=${{"Authorization": "Bearer ${token}"}}
    ...    body=${{"face_image": "${CURDIR}/../test_data/faces/photo.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Equal As Strings    ${response}[body][action]    allow
    Should Contain    ${response}[body][action]    challenge
