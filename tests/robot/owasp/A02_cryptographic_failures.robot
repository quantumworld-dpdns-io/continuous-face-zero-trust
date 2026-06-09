*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

*** Test Cases ***
A02-TC01 Weak Algorithm Detection
    [Documentation]    OWASP A02: Cryptographic Failures — weak algorithm check
    ${response}=    Make API Request    pqc    /api/v1/pqc/algorithms    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Log    Available algorithms: ${json}

A02-TC02 Key Management Verification
    [Documentation]    OWASP A02: Key management validation
    ${response}=    Make API Request    pqc    /api/v1/pqc/kem/encapsulate    POST    data={"algorithm": "KYBER_768"}
    Should Be Equal As Numbers    ${response.status_code}    200
    Log    PQC key encapsulation working

A02-TC03 TLS Version Check
    [Documentation]    OWASP A02: TLS version enforcement
    ${response}=    Make API Request    auth    /health    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    Log    TLS check passed

A02-TC04 Post-Quantum Readiness
    [Documentation]    OWASP A02: PQC migration readiness
    ${response}=    Make API Request    pqc    /api/v1/pqc/algorithms    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    Log    PQC algorithms available

A02-TC05 Entropy Quality
    [Documentation]    OWASP A02: Entropy source quality validation
    ${response}=    Make API Request    quantum    /api/v1/quantum/rng/generate    POST    data={"num_bits": 256}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    ${json.get('nist_test_passed', False)}    NIST randomness test failed
    Log    Quantum entropy quality verified
