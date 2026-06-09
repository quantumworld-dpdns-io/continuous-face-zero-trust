*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    600
${TARGET_LATENCY_MS}    100
${CONCURRENT_USERS}    100
${REQUESTS_PER_USER}    10

*** Test Cases ***
Face Inference Latency Single Request
    [Documentation]    Test face inference latency for single request
    [Tags]    performance    latency    single_request
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/face/embed
        ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
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

Face Inference Latency Concurrent
    [Documentation]    Test face inference latency with concurrent requests
    [Tags]    performance    latency    concurrent
    [Timeout]    ${TIMEOUT}
    
    @{all_latencies}=    Create List
    FOR    ${user}    IN RANGE    ${CONCURRENT_USERS}
        @{user_latencies}=    Create List
        FOR    ${request}    IN RANGE    ${REQUESTS_PER_USER}
            ${start_time}=    Get Time    epoch
            ${response}=    Send Request    POST    /api/v1/face/embed
            ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
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

Face Detection Latency
    [Documentation]    Test face detection latency
    [Tags]    performance    latency    detection
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/face/detect
        ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Calculate statistics
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

Face Comparison Latency
    [Documentation]    Test face comparison latency
    [Tags]    performance    latency    comparison
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings first
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_side.jpg
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/face/compare
        ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Calculate statistics
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

Liveness Detection Latency
    [Documentation]    Test liveness detection latency
    [Tags]    performance    latency    liveness
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/face/liveness
        ...    body=${{"image": "${CURDIR}/../test_data/faces/live.jpg"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Calculate statistics
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}
