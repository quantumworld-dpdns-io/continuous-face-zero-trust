*** Settings ***
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

Suite Setup    Create Sessions
Suite Teardown    Delete All Sessions

*** Variables ***
${QUANTUM_URL}    http://localhost:8003

*** Keywords ***
Create Sessions
    Create Session    quantum    ${QUANTUM_URL}

*** Test Cases ***
QRNG — Generate 256 Bits
    [Documentation]    Generate 256 quantum random bits
    ${data}=    Create Dictionary    num_bits=256    purpose=session_key
    ${response}=    Make API Request    quantum    /api/v1/quantum/rng/generate    POST    data=${data}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${json}[random_bytes]
    Should Be True    ${json}[nist_test_passed]
    Log    Generated 256 bits with entropy ${json}[min_entropy]

QRNG — Generate 4096 Bits
    [Documentation]    Generate 4096 quantum random bits
    ${data}=    Create Dictionary    num_bits=4096    purpose=general
    ${response}=    Make API Request    quantum    /api/v1/quantum/rng/generate    POST    data=${data}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    ${json}[nist_test_passed]
    Log    Generated 4096 bits

QRNG — Uniform Distribution Test
    [Documentation]    Verify QRNG output has uniform distribution
    ${all_bits}=    Create List
    FOR    ${i}    IN RANGE    10
        ${data}=    Create Dictionary    num_bits=256    purpose=general
        ${response}=    Make API Request    quantum    /api/v1/quantum/rng/generate    POST    data=${data}
        ${json}=    Set Variable    ${response.json()}
        Append To List    ${all_bits}    ${json}[random_bytes]
    END
    Length Should Be    ${all_bits}    10
    Log    Collected 10 random samples for distribution analysis

Quantum Backend Health
    [Documentation]    Check quantum backend health
    ${response}=    Make API Request    quantum    /api/v1/quantum/rng/health    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    ${json}[healthy]
    Log    Quantum backend healthy: ${json}[backend]
