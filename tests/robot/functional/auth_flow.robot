*** Settings ***
Resource    ../resources/keywords/auth_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections
Library     OperatingSystem

Suite Setup    Create Sessions
Suite Teardown    Delete All Sessions

*** Variables ***
${BASE_URL}    http://localhost:8000

*** Keywords ***
Create Sessions
    Create Session    auth    ${BASE_URL}

*** Test Cases ***
Full Authentication Flow — Happy Path
    [Documentation]    Test complete authentication flow with valid face image
    ${response}=    Authenticate User    test_data/face_real.jpg    device-id-001    web
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    ${json}[authenticated]
    Should Not Be Empty    ${json}[session_token]
    Should Not Be Empty    ${json}[refresh_token]
    Log    Authentication successful: ${json}[session_id]

Full Authentication Flow — No Face
    [Documentation]    Test authentication with image containing no face
    ${response}=    Authenticate User    test_data/no_face.jpg    device-id-002    web
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    No face detected: ${response.status_code}

Full Authentication Flow — Spoofed Face
    [Documentation]    Test authentication with printed photo (anti-spoof)
    ${response}=    Authenticate User    test_data/face_photo.jpg    device-id-003    web
    ${json}=    Set Variable    ${response.json()}
    Should Not Be True    ${json}[authenticated]
    Log    Spoofed face rejected: ${json}[reason]

Token Refresh Flow
    [Documentation]    Test token refresh after authentication
    ${auth_response}=    Authenticate User    test_data/face_real.jpg    device-id-004    web
    ${json}=    Set Variable    ${auth_response.json()}
    ${refresh_response}=    Refresh Token    ${json}[refresh_token]
    Should Be Equal As Numbers    ${refresh_response.status_code}    200
    ${refresh_json}=    Set Variable    ${refresh_response.json()}
    Should Not Be Empty    ${refresh_json}[session_token]
    Log    Token refreshed successfully

Session Revocation
    [Documentation]    Test session revocation
    ${auth_response}=    Authenticate User    test_data/face_real.jpg    device-id-005    web
    ${json}=    Set Variable    ${auth_response.json()}
    ${revoke_response}=    Revoke Session    ${json}[session_id]    user_requested
    Should Be Equal As Numbers    ${revoke_response.status_code}    200
    ${verify_response}=    Verify Session    ${json}[session_id]
    Should Not Be Equal As Numbers    ${verify_response.status_code}    200
    Log    Session revoked and verified
