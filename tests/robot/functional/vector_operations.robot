*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
Vector Upsert
    [Documentation]    Test vector upsert operation
    [Tags]    vector    upsert    positive
    [Timeout]    ${TIMEOUT}
    
    @{vector}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    
    ${response}=    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "test_vector_001", "vector": ${vector}, "payload": {"user_id": "test_user"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    Should Be Equal As Strings    ${response}[body][id]    test_vector_001

Vector Search
    [Documentation]    Test vector search operation
    [Tags]    vector    search    positive
    [Timeout]    ${TIMEOUT}
    
    # Insert vectors
    @{vector1}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    @{vector2}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.6]
    @{vector3}=    Evaluate    [0.9, 0.8, 0.7, 0.6, 0.5]
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_1", "vector": ${vector1}}}
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_2", "vector": ${vector2}}}
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_3", "vector": ${vector3}}}
    
    # Search
    @{query_vector}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    
    ${response}=    Send Request    POST    /api/v1/vector/search
    ...    body=${{"vector": ${query_vector}, "limit": 10, "threshold": 0.8}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][results]
    Should Be True    len(${response}[body][results]) > 0

Vector Search No Results
    [Documentation]    Test vector search with no results
    [Tags]    vector    search    negative
    [Timeout]    ${TIMEOUT}
    
    @{query_vector}=    Evaluate    [0.9, 0.9, 0.9, 0.9, 0.9]
    
    ${response}=    Send Request    POST    /api/v1/vector/search
    ...    body=${{"vector": ${query_vector}, "limit": 10, "threshold": 0.99}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Empty    ${response}[body][results]

Vector Delete
    [Documentation]    Test vector delete operation
    [Tags]    vector    delete    positive
    [Timeout]    ${TIMEOUT}
    
    # Insert vector
    @{vector}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_delete", "vector": ${vector}}}
    
    # Delete vector
    ${delete_response}=    Send Request    POST    /api/v1/vector/delete
    ...    body=${{"id": "vector_delete"}}
    
    Should Be Equal As Strings    ${delete_response}[status]    200
    Should Be True    ${delete_response}[body][success]
    
    # Verify deleted
    @{query_vector}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    
    ${search_response}=    Send Request    POST    /api/v1/vector/search
    ...    body=${{"vector": ${query_vector}, "limit": 10, "threshold": 0.99}}
    
    Should Be Equal As Strings    ${search_response}[status]    200
    ${found}=    Evaluate    any(r["id"] == "vector_delete" for r in ${search_response}[body][results])
    Should Not Be True    ${found}

Vector Upsert Update
    [Documentation]    Test vector upsert update
    [Tags]    vector    upsert    update
    [Timeout]    ${TIMEOUT}
    
    # Insert vector
    @{vector1}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_update", "vector": ${vector1}}}
    
    # Update vector
    @{vector2}=    Evaluate    [0.9, 0.8, 0.7, 0.6, 0.5]
    
    ${response}=    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_update", "vector": ${vector2}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]

Vector Search Threshold
    [Documentation]    Test vector search with different thresholds
    [Tags]    vector    search    threshold
    [Timeout]    ${TIMEOUT}
    
    # Insert vectors
    @{vector1}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    @{vector2}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.6]
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_threshold_1", "vector": ${vector1}}}
    
    Send Request    POST    /api/v1/vector/upsert
    ...    body=${{"id": "vector_threshold_2", "vector": ${vector2}}}
    
    # Search with different thresholds
    @{query_vector}=    Evaluate    [0.1, 0.2, 0.3, 0.4, 0.5]
    
    @{thresholds}=    Create List    0.7    0.8    0.9    0.95
    
    FOR    ${threshold}    IN    @{thresholds}
        ${response}=    Send Request    POST    /api/v1/vector/search
        ...    body=${{"vector": ${query_vector}, "limit": 10, "threshold": ${threshold}}}
        
        Should Be Equal As Strings    ${response}[status]    200
    END

Vector Search Performance
    [Documentation]    Test vector search performance
    [Tags]    vector    search    performance
    [Timeout]    ${TIMEOUT}
    
    # Insert vectors
    FOR    ${i}    IN RANGE    100
        @{vector}=    Evaluate    [${i}/100, ${i}/100, ${i}/100, ${i}/100, ${i}/100]
        
        Send Request    POST    /api/v1/vector/upsert
        ...    body=${{"id": "perf_vector_${i}", "vector": ${vector}}}
    END
    
    # Search and measure latency
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        @{query_vector}=    Evaluate    [0.5, 0.5, 0.5, 0.5, 0.5]
        
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/vector/search
        ...    body=${{"vector": ${query_vector}, "limit": 10, "threshold": 0.8}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 50
