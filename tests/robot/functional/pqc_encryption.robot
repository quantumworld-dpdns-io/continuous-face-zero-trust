*** Settings ***
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

Suite Setup    Create Sessions
Suite Teardown    Delete All Sessions

*** Variables ***
${PQC_URL}    http://localhost:8006

*** Keywords ***
Create Sessions
    Create Session    pqc    ${PQC_URL}

*** Test Cases ***
List PQC Algorithms
    [Documentation]    List all supported PQC algorithms
    ${response}=    Make API Request    pqc    /api/v1/pqc/algorithms    GET
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${json}[algorithms]
    Log    Available algorithms: ${json}

Kyber-768 KEM Encapsulation
    [Documentation]    Test Kyber-768 key encapsulation
    ${data}=    Create Dictionary    algorithm=KYBER_768
    ${response}=    Make API Request    pqc    /api/v1/pqc/kem/encapsulate    POST    data=${data}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${json}[ciphertext]
    Should Not Be Empty    ${json}[shared_secret]
    Should Be Equal As Numbers    ${json}[algorithm]    3
    Log    Kyber-768 encapsulation successful

Dilithium-3 Signing
    [Documentation]    Test Dilithium-3 digital signature
    ${data}=    Create Dictionary    message=dGVzdCBtZXNzYWdl    algorithm=DILITHIUM_3
    ${response}=    Make API Request    pqc    /api/v1/pqc/sign    POST    data=${data}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${json}[signature]
    Should Be Equal As Numbers    ${json}[algorithm]    5
    Log    Dilithium-3 signing successful

FALCON-512 Signing
    [Documentation]    Test FALCON-512 digital signature
    ${data}=    Create Dictionary    message=dGVzdCBtZXNzYWdl    algorithm=FALCON_512
    ${response}=    Make API Request    pqc    /api/v1/pqc/sign    POST    data=${data}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${json}[signature]
    Log    FALCON-512 signing successful

Hybrid Encryption
    [Documentation]    Test hybrid classical+PQC encryption
    ${data}=    Create Dictionary    plaintext=dGVzdCBwbGFpbnRleHQ    algorithm=KYBER_768
    ${response}=    Make API Request    pqc    /api/v1/pqc/encrypt    POST    data=${data}
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Not Be Empty    ${json}[ciphertext]
    Log    Hybrid encryption successful
