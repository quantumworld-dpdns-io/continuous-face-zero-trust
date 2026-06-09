*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    600
${TARGET_LATENCY_MS}    50
${VECTOR_DIMENSION}    512
${CONCURRENT_USERS}    100
${REQUESTS_PER_USER}    10

*** Test Cases ***
Vector Search Latency Single Request
    [Documentation]    Test vector search latency for single request
    [Tags]    performance    latency    single_request
    [Timeout]    ${TIMEOUT}
    
    # Generate embedding for search
    ${embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/vector/search
        ...    body=${{"query_embedding": ${embedding}, "top_k": 10, "threshold": 0.7}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

Vector Search Latency Concurrent
    [Documentation]    Test vector search latency with concurrent requests
    [Tags]    performance    latency    concurrent
    [Timeout]    ${TIMEOUT}
    
    # Generate embedding for search
    ${embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    
    @{all_latencies}=    Create List
    FOR    ${user}    IN RANGE    ${CONCURRENT_USERS}
        @{user_latencies}=    Create List
        FOR    ${request}    IN RANGE    ${REQUESTS_PER_USER}
            ${start_time}=    Get Time    epoch
            ${response}=    Send Request    POST    /api/v1/vector/search
            ...    body=${{"query_embedding": ${embedding}, "top_k": 10, "threshold": 0.7}}
            ${end_time}=    Get Time    epoch
            
            ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
            Append To List    ${user_latencies}    ${latency}
        END
        Append To List    ${all_latencies}    ${user_latencies}
    END
    
    @{flat_latencies}=    Evaluate    [lat for user_lats in ${all_latencies} for lat in user_lats]
    ${avg_latency}=    Evaluate    sum(${flat_latencies}) / len(${flat_latencies})
    ${p99_latency}=    Evaluate    sorted(${flat_latencies})[int(len(${flat_latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS} * 2

Vector Insert Latency
    [Documentation]    Test vector insert latency
    [Tags]    performance    latency    insert
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${embedding}=    Generate Random Embedding    ${VECTOR_DIMENSION}
        
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/vector/insert
        ...    body=${{"embedding": ${embedding}, "metadata": {"id": "vec_${i}", "user_id": "test_user"}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < ${TARGET_LATENCY_MS}

Vector Batch Insert Latency
    [Documentation]    Test vector batch insert latency
    [Tags]    performance    latency    batch_insert
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        @{batch_embeddings}=    Create List
        FOR    ${j}    IN RANGE    100
            ${embedding}=    Generate Random Embedding    ${VECTOR_DIMENSION}
            Append To List    ${batch_embeddings}    ${{"embedding": ${embedding}, "metadata": {"id": "batch_vec_${i}_${j}", "user_id": "test_user"}}}
        END
        
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/vector/batch_insert
        ...    body=${{"vectors": ${batch_embeddings}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average latency: ${avg_latency}ms
    Log    P99 latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 100

Vector Search Accuracy
    [Documentation]    Test vector search accuracy
    [Tags]    performance    accuracy
    [Timeout]    ${TIMEOUT}
    
    # Generate test vectors
    ${query_embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    
    # Search and verify results
    ${response}=    Send Request    POST    /api/v1/vector/search
    ...    body=${{"query_embedding": ${query_embedding}, "top_k": 10, "threshold": 0.7}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][results]
    
    # Verify similarity scores are in valid range
    FOR    ${result}    IN    ${response}[body][results]
        Should Be True    ${result}[similarity] >= 0
        Should Be True    ${result}[similarity] <= 1
    END
