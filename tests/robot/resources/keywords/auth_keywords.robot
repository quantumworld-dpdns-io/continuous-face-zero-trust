*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    JSONLibrary
Library    String

*** Keywords ***
Authenticate User
    [Arguments]    ${face_image_path}    ${device_id}=test-device    ${platform}=web
    ${image}=    Get Binary File    ${face_image_path}
    ${files}=    Create Dictionary    face_image=${image}
    ${data}=    Create Dictionary    device_id=${device_id}    platform=${platform}
    ${response}=    Post Request    auth    /api/v1/auth/login    files=${files}    data=${data}
    [Return]    ${response}

Enroll Face
    [Arguments]    ${image_paths}    ${user_id}    ${tenant_id}=default
    ${files}=    Create Dictionary
    FOR    ${path}    IN    @{image_paths}
        ${image}=    Get Binary File    ${path}
        Set To Dictionary    ${files}    face_images=${image}
    END
    ${data}=    Create Dictionary    user_id=${user_id}    tenant_id=${tenant_id}
    ${response}=    Post Request    auth    /api/v1/enrollment/enroll    files=${files}    data=${data}
    [Return]    ${response}

Refresh Token
    [Arguments]    ${refresh_token}
    ${data}=    Create Dictionary    refresh_token=${refresh_token}
    ${response}=    Post Request    auth    /api/v1/tokens/refresh    json=${data}
    [Return]    ${response}

Verify Session
    [Arguments]    ${session_id}    ${device_id}=test-device
    ${response}=    Get Request    auth    /api/v1/sessions/${session_id}
    [Return]    ${response}

Revoke Session
    [Arguments]    ${session_id}    ${reason}=user_requested
    ${response}=    Delete Request    auth    /api/v1/sessions/${session_id}    params=reason=${reason}
    [Return]    ${response}

Health Check
    [Arguments]    ${service_url}
    Create Session    health_check    ${service_url}
    ${response}=    Get Request    health_check    /health
    [Return]    ${response}
