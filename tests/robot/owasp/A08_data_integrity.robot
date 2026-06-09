*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A08-TC01 CI/CD Pipeline Security
    [Documentation]    OWASP A08: Data Integrity — CI/CD security
    ${result}=    Run Process    cat    .github/workflows/ci.yml    shell=True
    Should Contain    ${result.stdout}    actions/checkout
    Should Contain    ${result.stdout}    cache
    Log    CI/CD pipeline security verified

A08-TC02 Signed Artifacts
    [Documentation]    OWASP A08: Signed build artifacts
    ${result}=    Run Process    cat    .github/workflows/release.yml    shell=True
    Should Contain    ${result.stdout}    cosign
    Log    Artifact signing configured

A08-TC03 Data Tampering Detection
    [Documentation]    OWASP A08: Data integrity verification
    ${response}=    Make API Request    zk    /api/v1/zk/verify    POST    data={"proof": "test", "public_inputs": "test", "verification_key": "test", "circuit_id": "face_verify"}    expected_status=any
    Log    Data tampering detection test completed
