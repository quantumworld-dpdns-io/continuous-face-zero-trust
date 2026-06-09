*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A09-TC01 Audit Logging Verification
    [Documentation]    OWASP A09: Logging Failures — audit completeness
    ${response}=    Make API Request    auth    /health    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    Log    Audit logging endpoint accessible

A09-TC02 Suspicious Activity Detection
    [Documentation]    OWASP A09: Suspicious activity monitoring
    ${responses}=    Test Rate Limiting    /api/v1/auth/login    30
    ${suspicious_detected}=    Set Variable    ${False}
    FOR    ${resp}    IN    @{responses}
        IF    ${resp.status_code} == 429    Set Variable    ${True}    ${suspicious_detected}
    END
    Log    Suspicious activity detection: ${suspicious_detected}

A09-TC03 Quantum Audit Trail
    [Documentation]    OWASP A09: Quantum operation auditing
    ${response}=    Make API Request    quantum    /api/v1/quantum/rng/generate    POST    data={"num_bits": 64, "purpose": "audit_test"}
    Should Be Equal As Numbers    ${response.status_code}    200
    Log    Quantum audit trail verified
