*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/ZKLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    600
${TARGET_LATENCY_MS}    500
${CONCURRENT_USERS}    50
${REQUESTS_PER_USER}    10

*** Test Cases ***
ZK Proving Latency Single Request
    [Documentation]    Test ZK proving latency for single request
    [Tags]    performance    latency    single_request
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/zk/generate
        ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc123"}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Calculate statistics
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${min_latency}=    Evaluate    min(${latencies})
    ${max_latency}=    Evaluate    max(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    Min latency: ${min_latency}ms
    Log    Max latency: ${max_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

ZK Proving Latency Concurrent
    [Documentation]    Test ZK proving latency with concurrent requests
    [Tags]    performance    latency    concurrent
    [Timeout]    ${TIMEOUT}
    
    @{all_latencies}=    Create List
    FOR    ${user}    IN RANGE    ${CONCURRENT_USERS}
        @{user_latencies}=    Create List
        FOR    ${request}    IN RANGE    ${REQUESTS_PER_USER}
            ${start_time}=    Get Time    epoch
            ${response}=    Send Request    POST    /api/v1/zk/generate
            ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc123"}}}
            ${end_time}=    Get Time    epoch
            
            ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
            Append To List    ${user_latencies}    ${latency}
        END
        Append To List    ${all_latencies}    ${user_latencies}
    END
    
    # Calculate statistics
    @{flat_latencies}=    Evaluate    [lat for user_lats in ${all_latencies} for lat in user_lats]
    ${avg_latency}=    Evaluate    sum(${flat_latencies}) / len(${flat_latencies})
    ${p99_latency}=    Evaluate    sorted(${flat_latencies})[int(len(${flat_latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

ZK Verification Latency
    [Documentation]    Test ZK verification latency
    [Tags]    performance    latency    verification
    [Timeout]    ${TIMEOUT}
    
    # Generate proof first
    ${proof_response}=    Send Request    POST    /api/v1/zk/generate
    ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc123"}}}
    
    ${proof}=    Set Variable    ${proof_response}[body][proof]
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/zk/verify
        ...    body=${{"circuit": "face_matching", "proof": "${proof}", "public_inputs": {"stored_hash": "abc123"}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Calculate statistics
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 50

ZK Proof Aggregation Latency
    [Documentation]    Test ZK proof aggregation latency
    [Tags]    performance    latency    aggregation
    [Timeout]    ${TIMEOUT}
    
    # Generate multiple proofs
    @{proofs}=    Create List
    FOR    ${i}    IN RANGE    10
        ${response}=    Send Request    POST    /api/v1/zk/generate
        ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc${i}"}}}
        
        Append To List    ${proofs}    ${{"circuit": "face_matching", "proof": ${response}[body][proof], "public_inputs": {"stored_hash": "abc${i}"}}}
    END
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/zk/aggregate
        ...    body=${{"proofs": ${proofs}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Calculate statistics
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 1000
