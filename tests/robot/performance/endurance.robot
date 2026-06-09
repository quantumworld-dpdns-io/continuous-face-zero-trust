*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    7200
${DURATION_MINUTES}    60
${REQUESTS_PER_MINUTE}    100
${TARGET_ERROR_RATE}    0.01

*** Test Cases ***
Endurance Test Authentication
    [Documentation]    Endurance test for authentication
    [Tags]    performance    endurance    authentication
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${total_requests}=    Set Variable    0
    ${failed_requests}=    Set Variable    0
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/auth/login
            ...    body=${{"user_id": "endurance_user_${i}", "device_id": "device_${i}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
            
            ${total_requests}=    Evaluate    ${total_requests} + 1
            IF    ${response}[status] != 200
                ${failed_requests}=    Evaluate    ${failed_requests} + 1
            END
        END
        
        Log    Elapsed: ${elapsed_minutes} minutes, Total requests: ${total_requests}, Failed: ${failed_requests}
    END
    
    ${error_rate}=    Evaluate    ${failed_requests} / ${total_requests}
    
    Log    Total requests: ${total_requests}
    Log    Failed requests: ${failed_requests}
    Log    Error rate: ${error_rate}
    
    Should Be True    ${error_rate} < ${TARGET_ERROR_RATE}

Endurance Test Face Processing
    [Documentation]    Endurance test for face processing
    [Tags]    performance    endurance    face
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${total_requests}=    Set Variable    0
    ${failed_requests}=    Set Variable    0
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/face/embed
            ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
            
            ${total_requests}=    Evaluate    ${total_requests} + 1
            IF    ${response}[status] != 200
                ${failed_requests}=    Evaluate    ${failed_requests} + 1
            END
        END
        
        Log    Elapsed: ${elapsed_minutes} minutes, Total requests: ${total_requests}, Failed: ${failed_requests}
    END
    
    ${error_rate}=    Evaluate    ${failed_requests} / ${total_requests}
    
    Log    Total requests: ${total_requests}
    Log    Failed requests: ${failed_requests}
    Log    Error rate: ${error_rate}
    
    Should Be True    ${error_rate} < ${TARGET_ERROR_RATE}

Endurance Test Crypto Operations
    [Documentation]    Endurance test for crypto operations
    [Tags]    performance    endurance    crypto
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${total_requests}=    Set Variable    0
    ${failed_requests}=    Set Variable    0
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
            ...    body=${{"algorithm": "kyber-768"}}
            
            ${total_requests}=    Evaluate    ${total_requests} + 1
            IF    ${response}[status] != 200
                ${failed_requests}=    Evaluate    ${failed_requests} + 1
            END
        END
        
        Log    Elapsed: ${elapsed_minutes} minutes, Total requests: ${total_requests}, Failed: ${failed_requests}
    END
    
    ${error_rate}=    Evaluate    ${failed_requests} / ${total_requests}
    
    Log    Total requests: ${total_requests}
    Log    Failed requests: ${failed_requests}
    Log    Error rate: ${error_rate}
    
    Should Be True    ${error_rate} < ${TARGET_ERROR_RATE}

Endurance Test ZK Proofs
    [Documentation]    Endurance test for ZK proofs
    [Tags]    performance    endurance    zk
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${total_requests}=    Set Variable    0
    ${failed_requests}=    Set Variable    0
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/zk/generate
            ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc${i}"}}}
            
            ${total_requests}=    Evaluate    ${total_requests} + 1
            IF    ${response}[status] != 200
                ${failed_requests}=    Evaluate    ${failed_requests} + 1
            END
        END
        
        Log    Elapsed: ${elapsed_minutes} minutes, Total requests: ${total_requests}, Failed: ${failed_requests}
    END
    
    ${error_rate}=    Evaluate    ${failed_requests} / ${total_requests}
    
    Log    Total requests: ${total_requests}
    Log    Failed requests: ${failed_requests}
    Log    Error rate: ${error_rate}
    
    Should Be True    ${error_rate} < 0.05
