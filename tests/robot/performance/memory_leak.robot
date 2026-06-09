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
${MEMORY_GROWTH_THRESHOLD}    10

*** Test Cases ***
Memory Leak Test Authentication
    [Documentation]    Memory leak test for authentication
    [Tags]    performance    memory_leak    authentication
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${initial_memory}=    Get System Memory
    
    @{memory_samples}=    Create List
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/auth/login
            ...    body=${{"user_id": "memory_user_${i}", "device_id": "device_${i}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        END
        
        ${current_memory}=    Get System Memory
        Append To List    ${memory_samples}    ${current_memory}
        
        Log    Elapsed: ${elapsed_minutes} minutes, Memory: ${current_memory}MB
    END
    
    ${final_memory}=    Get System Memory
    ${memory_growth}=    Evaluate    ${final_memory} - ${initial_memory}
    ${memory_growth_percent}=    Evaluate    (${memory_growth} / ${initial_memory}) * 100
    
    Log    Initial memory: ${initial_memory}MB
    Log    Final memory: ${final_memory}MB
    Log    Memory growth: ${memory_growth}MB (${memory_growth_percent}%)
    
    Should Be True    ${memory_growth_percent} < ${MEMORY_GROWTH_THRESHOLD}

Memory Leak Test Face Processing
    [Documentation]    Memory leak test for face processing
    [Tags]    performance    memory_leak    face
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${initial_memory}=    Get System Memory
    
    @{memory_samples}=    Create List
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/face/embed
            ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
        END
        
        ${current_memory}=    Get System Memory
        Append To List    ${memory_samples}    ${current_memory}
        
        Log    Elapsed: ${elapsed_minutes} minutes, Memory: ${current_memory}MB
    END
    
    ${final_memory}=    Get System Memory
    ${memory_growth}=    Evaluate    ${final_memory} - ${initial_memory}
    ${memory_growth_percent}=    Evaluate    (${memory_growth} / ${initial_memory}) * 100
    
    Log    Initial memory: ${initial_memory}MB
    Log    Final memory: ${final_memory}MB
    Log    Memory growth: ${memory_growth}MB (${memory_growth_percent}%)
    
    Should Be True    ${memory_growth_percent} < ${MEMORY_GROWTH_THRESHOLD}

Memory Leak Test Crypto Operations
    [Documentation]    Memory leak test for crypto operations
    [Tags]    performance    memory_leak    crypto
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${initial_memory}=    Get System Memory
    
    @{memory_samples}=    Create List
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
            ...    body=${{"algorithm": "kyber-768"}}
        END
        
        ${current_memory}=    Get System Memory
        Append To List    ${memory_samples}    ${current_memory}
        
        Log    Elapsed: ${elapsed_minutes} minutes, Memory: ${current_memory}MB
    END
    
    ${final_memory}=    Get System Memory
    ${memory_growth}=    Evaluate    ${final_memory} - ${initial_memory}
    ${memory_growth_percent}=    Evaluate    (${memory_growth} / ${initial_memory}) * 100
    
    Log    Initial memory: ${initial_memory}MB
    Log    Final memory: ${final_memory}MB
    Log    Memory growth: ${memory_growth}MB (${memory_growth_percent}%)
    
    Should Be True    ${memory_growth_percent} < ${MEMORY_GROWTH_THRESHOLD}

Memory Leak Test ZK Proofs
    [Documentation]    Memory leak test for ZK proofs
    [Tags]    performance    memory_leak    zk
    [Timeout]    ${TIMEOUT}
    
    ${start_time}=    Get Time    epoch
    ${initial_memory}=    Get System Memory
    
    @{memory_samples}=    Create List
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        ${elapsed_minutes}=    Evaluate    (${current_time} - ${start_time}) / 60
        
        IF    ${elapsed_minutes} >= ${DURATION_MINUTES}    BREAK
        
        FOR    ${i}    IN RANGE    ${REQUESTS_PER_MINUTE}
            ${response}=    Send Request    POST    /api/v1/zk/generate
            ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc${i}"}}}
        END
        
        ${current_memory}=    Get System Memory
        Append To List    ${memory_samples}    ${current_memory}
        
        Log    Elapsed: ${elapsed_minutes} minutes, Memory: ${current_memory}MB
    END
    
    ${final_memory}=    Get System Memory
    ${memory_growth}=    Evaluate    ${final_memory} - ${initial_memory}
    ${memory_growth_percent}=    Evaluate    (${memory_growth} / ${initial_memory}) * 100
    
    Log    Initial memory: ${initial_memory}MB
    Log    Final memory: ${final_memory}MB
    Log    Memory growth: ${memory_growth}MB (${memory_growth_percent}%)
    
    Should Be True    ${memory_growth_percent} < 20
