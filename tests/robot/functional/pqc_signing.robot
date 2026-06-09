*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/PQCLibrary.py
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
PQC Signing Dilithium
    [Documentation]    Test PQC signing with Dilithium
    [Tags]    pqc    sign    dilithium    positive
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Test message to sign"
    
    ${response}=    Send Request    POST    /api/v1/crypto/sign
    ...    body=${{"algorithm": "dilithium-5", "message": "${message}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][signature]
    Should Be Equal As Strings    ${response}[body][algorithm]    dilithium-5

PQC Signing Different Algorithms
    [Documentation]    Test PQC signing with different algorithms
    [Tags]    pqc    sign    positive
    [Timeout]    ${TIMEOUT}
    
    @{algorithms}=    Create List    dilithium-2    dilithium-3    dilithium-5    falcon-512    falcon-1024
    
    FOR    ${algorithm}    IN    @{algorithms}
        ${message}=    Set Variable    "Test message for ${algorithm}"
        
        ${response}=    Send Request    POST    /api/v1/crypto/sign
        ...    body=${{"algorithm": "${algorithm}", "message": "${message}"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][signature]
        Should Be Equal As Strings    ${response}[body][algorithm]    ${algorithm}
    END

PQC Signing Consistency
    [Documentation]    Test PQC signing consistency
    [Tags]    pqc    sign    consistency
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Consistency test message"
    
    # Sign multiple times
    @{signatures}=    Create List
    FOR    ${i}    IN RANGE    5
        ${response}=    Send Request    POST    /api/v1/crypto/sign
        ...    body=${{"algorithm": "dilithium-5", "message": "${message}"}}
        
        Append To List    ${signatures}    ${response}[body][signature]
    END
    
    # Check all signatures are unique (different randomness)
    ${unique_signatures}=    Evaluate    len(set(${signatures}))
    Should Be Equal As Numbers    ${unique_signatures}    5

PQC Signing Performance
    [Documentation]    Test PQC signing performance
    [Tags]    pqc    sign    performance
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Performance test message"
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/sign
        ...    body=${{"algorithm": "dilithium-5", "message": "${message}"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 10

PQC Verification Valid Signature
    [Documentation]    Test PQC verification with valid signature
    [Tags]    pqc    verify    positive
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Test message to verify"
    
    # Sign message
    ${sign_response}=    Send Request    POST    /api/v1/crypto/sign
    ...    body=${{"algorithm": "dilithium-5", "message": "${message}"}}
    
    ${signature}=    Set Variable    ${sign_response}[body][signature]
    
    # Verify signature
    ${response}=    Send Request    POST    /api/v1/crypto/verify
    ...    body=${{"algorithm": "dilithium-5", "message": "${message}", "signature": "${signature}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][valid]

PQC Verification Invalid Signature
    [Documentation]    Test PQC verification with invalid signature
    [Tags]    pqc    verify    negative
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Test message to verify"
    ${invalid_signature}=    Set Variable    "invalid_signature"
    
    # Verify invalid signature
    ${response}=    Send Request    POST    /api/v1/crypto/verify
    ...    body=${{"algorithm": "dilithium-5", "message": "${message}", "signature": "${invalid_signature}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][valid]

PQC Verification Wrong Message
    [Documentation]    Test PQC verification with wrong message
    [Tags]    pqc    verify    negative
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Original message"
    ${wrong_message}=    Set Variable    "Wrong message"
    
    # Sign message
    ${sign_response}=    Send Request    POST    /api/v1/crypto/sign
    ...    body=${{"algorithm": "dilithium-5", "message": "${message}"}}
    
    ${signature}=    Set Variable    ${sign_response}[body][signature]
    
    # Verify with wrong message
    ${response}=    Send Request    POST    /api/v1/crypto/verify
    ...    body=${{"algorithm": "dilithium-5", "message": "${wrong_message}", "signature": "${signature}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][valid]

PQC Verification Performance
    [Documentation]    Test PQC verification performance
    [Tags]    pqc    verify    performance
    [Timeout]    ${TIMEOUT}
    
    ${message}=    Set Variable    "Performance test message"
    
    # Sign message
    ${sign_response}=    Send Request    POST    /api/v1/crypto/sign
    ...    body=${{"algorithm": "dilithium-5", "message": "${message}"}}
    
    ${signature}=    Set Variable    ${sign_response}[body][signature]
    
    # Verify multiple times
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/verify
        ...    body=${{"algorithm": "dilithium-5", "message": "${message}", "signature": "${signature}"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 5
