*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/PQCLibrary.py
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    600
${TARGET_LATENCY_MS}    50
${CONCURRENT_USERS}    100
${REQUESTS_PER_USER}    100

*** Test Cases ***
PQC Encryption Latency Kyber768
    [Documentation]    Test PQC encryption latency for Kyber768
    [Tags]    performance    latency    kyber    encryption
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
        ...    body=${{"algorithm": "kyber-768"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Kyber768 Average latency: ${avg_latency}ms
    Log    Kyber768 P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

PQC Encryption Latency Kyber1024
    [Documentation]    Test PQC encryption latency for Kyber1024
    [Tags]    performance    latency    kyber    encryption
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
        ...    body=${{"algorithm": "kyber-1024"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Kyber1024 Average latency: ${avg_latency}ms
    Log    Kyber1024 P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 100

PQC Encryption Latency Dilithium3
    [Documentation]    Test PQC encryption latency for Dilithium3
    [Tags]    performance    latency    dilithium    signing
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/sign
        ...    body=${{"algorithm": "dilithium-3", "data": "test_data_to_sign"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Dilithium3 Average latency: ${avg_latency}ms
    Log    Dilithium3 P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

PQC Decryption Latency
    [Documentation]    Test PQC decryption latency
    [Tags]    performance    latency    kyber    decryption
    [Timeout]    ${TIMEOUT}
    
    # Generate key pair and encapsulate first
    ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
    ...    body=${{"algorithm": "kyber-768"}}
    
    ${ciphertext}=    Set Variable    ${response}[body][ciphertext]
    ${shared_secret}=    Set Variable    ${response}[body][shared_secret]
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/kem/decapsulate
        ...    body=${{"algorithm": "kyber-768", "ciphertext": "${ciphertext}"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Kyber768 Decryption Average latency: ${avg_latency}ms
    Log    Kyber768 Decryption P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

PQC Signature Verification Latency
    [Documentation]    Test PQC signature verification latency
    [Tags]    performance    latency    dilithium    verification
    [Timeout]    ${TIMEOUT}
    
    # Generate signature first
    ${response}=    Send Request    POST    /api/v1/crypto/sign
    ...    body=${{"algorithm": "dilithium-3", "data": "test_data_to_verify"}}
    
    ${signature}=    Set Variable    ${response}[body][signature]
    ${public_key}=    Set Variable    ${response}[body][public_key]
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/verify
        ...    body=${{"algorithm": "dilithium-3", "data": "test_data_to_verify", "signature": "${signature}", "public_key": "${public_key}"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Dilithium3 Verification Average latency: ${avg_latency}ms
    Log    Dilithium3 Verification P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 10

PQC Batch Operations Latency
    [Documentation]    Test PQC batch operations latency
    [Tags]    performance    latency    batch
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        @{batch_items}=    Create List
        FOR    ${j}    IN RANGE    100
            Append To List    ${batch_items}    ${{"algorithm": "kyber-768"}}
        END
        
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/batch/encapsulate
        ...    body=${{"items": ${batch_items}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Batch Encapsulation Average latency: ${avg_latency}ms
    Log    Batch Encapsulation P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 500
