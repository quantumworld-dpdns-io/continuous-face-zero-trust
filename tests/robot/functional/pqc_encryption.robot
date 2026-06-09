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
PQC Key Exchange Kyber
    [Documentation]    Test PQC key exchange with Kyber
    [Tags]    pqc    kem    kyber    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
    ...    body=${{"algorithm": "kyber-1024"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][ciphertext]
    Should Not Be Empty    ${response}[body][shared_secret]
    Should Be Equal As Strings    ${response}[body][algorithm]    kyber-1024

PQC Key Exchange Different Algorithms
    [Documentation]    Test PQC key exchange with different algorithms
    [Tags]    pqc    kem    positive
    [Timeout]    ${TIMEOUT}
    
    @{algorithms}=    Create List    kyber-512    kyber-768    kyber-1024
    
    FOR    ${algorithm}    IN    @{algorithms}
        ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
        ...    body=${{"algorithm": "${algorithm}"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][ciphertext]
        Should Not Be Empty    ${response}[body][shared_secret]
        Should Be Equal As Strings    ${response}[body][algorithm]    ${algorithm}
    END

PQC Key Exchange Consistency
    [Documentation]    Test PQC key exchange consistency
    [Tags]    pqc    kem    consistency
    [Timeout]    ${TIMEOUT}
    
    # Exchange multiple keys
    @{keys}=    Create List
    FOR    ${i}    IN RANGE    5
        ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
        ...    body=${{"algorithm": "kyber-1024"}}
        
        Append To List    ${keys}    ${response}[body][shared_secret]
    END
    
    # Check all keys are unique
    ${unique_keys}=    Evaluate    len(set(${keys}))
    Should Be Equal As Numbers    ${unique_keys}    5

PQC Encryption Hybrid
    [Documentation]    Test PQC hybrid encryption
    [Tags]    pqc    encryption    hybrid    positive
    [Timeout]    ${TIMEOUT}
    
    ${plaintext}=    Set Variable    "Hello, World! This is a secret message."
    
    # Encrypt
    ${encrypt_response}=    Send Request    POST    /api/v1/crypto/encrypt
    ...    body=${{"algorithm": "hybrid-kyber-aes", "plaintext": "${plaintext}"}}
    
    Should Be Equal As Strings    ${encrypt_response}[status]    200
    Should Not Be Empty    ${encrypt_response}[body][ciphertext]
    Should Not Be Empty    ${encrypt_response}[body][nonce]
    
    # Decrypt
    ${decrypt_response}=    Send Request    POST    /api/v1/crypto/decrypt
    ...    body=${{"algorithm": "hybrid-kyber-aes", "ciphertext": "${encrypt_response}[body][ciphertext]", "nonce": "${encrypt_response}[body][nonce]"}}
    
    Should Be Equal As Strings    ${decrypt_response}[status]    200
    Should Be Equal As Strings    ${decrypt_response}[body][plaintext]    ${plaintext}

PQC Encryption Different Algorithms
    [Documentation]    Test PQC hybrid encryption with different algorithms
    [Tags]    pqc    encryption    positive
    [Timeout]    ${TIMEOUT}
    
    @{algorithms}=    Create List    hybrid-kyber-aes    hybrid-kyber-chacha
    
    FOR    ${algorithm}    IN    @{algorithms}
        ${plaintext}=    Set Variable    "Test message for ${algorithm}"
        
        # Encrypt
        ${encrypt_response}=    Send Request    POST    /api/v1/crypto/encrypt
        ...    body=${{"algorithm": "${algorithm}", "plaintext": "${plaintext}"}}
        
        Should Be Equal As Strings    ${encrypt_response}[status]    200
        
        # Decrypt
        ${decrypt_response}=    Send Request    POST    /api/v1/crypto/decrypt
        ...    body=${{"algorithm": "${algorithm}", "ciphertext": "${encrypt_response}[body][ciphertext]", "nonce": "${encrypt_response}[body][nonce]"}}
        
        Should Be Equal As Strings    ${decrypt_response}[status]    200
        Should Be Equal As Strings    ${decrypt_response}[body][plaintext]    ${plaintext}
    END

PQC Encryption Performance
    [Documentation]    Test PQC encryption performance
    [Tags]    pqc    encryption    performance
    [Timeout]    ${TIMEOUT}
    
    ${plaintext}=    Set Variable    "Performance test message"
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/encrypt
        ...    body=${{"algorithm": "hybrid-kyber-aes", "plaintext": "${plaintext}"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 50

PQC Get Algorithms
    [Documentation]    Test getting supported algorithms
    [Tags]    pqc    algorithms
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/crypto/algorithms
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][kem]
    Should Not Be Empty    ${response}[body][signatures]
    Should Not Be Empty    ${response}[body][encryption]
