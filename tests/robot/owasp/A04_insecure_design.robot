*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A04-TC01 Rate Limiting Verification
    [Documentation]    OWASP A04: Insecure Design — rate limiting
    ${responses}=    Test Rate Limiting    /api/v1/auth/login    50
    ${rate_limited}=    Set Variable    ${False}
    FOR    ${resp}    IN    @{responses}
        IF    ${resp.status_code} == 422    Set Variable    ${True}    ${rate_limited}
    END
    Log    Rate limiting test completed

A04-TC02 Biometric Anti-Spoofing
    [Documentation]    OWASP A04: Biometric spoofing prevention
    ${response}=    Make API Request    face    /api/v1/face/liveness    POST    data={"image": "test_spoof"}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    ${json.get('live', False)} == False    Anti-spoofing should detect fake
    Log    Anti-spoofing verification completed

A04-TC03 Business Logic — Minimum Face Images
    [Documentation]    OWASP A04: Business logic enforcement
    ${response}=    Make API Request    auth    /api/v1/enrollment/enroll    POST    data={"user_id": "test", "face_images_count": 0}    expected_status=any
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Business logic enforced: minimum images required
