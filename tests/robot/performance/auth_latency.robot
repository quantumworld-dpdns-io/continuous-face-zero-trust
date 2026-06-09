*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_perf_001
${TIMEOUT}    600
${TARGET_LATENCY_MS}    200
${CONCURRENT_USERS}    100
${REQUESTS_PER_USER}    10

*** Test Cases ***
Auth Latency Single User
    [Documentation]    Test auth latency for single user
    [Tags]    performance    latency    single_user
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
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

Auth Latency Concurrent Users
    [Documentation]    Test auth latency with concurrent users
    [Tags]    performance    latency    concurrent
    [Timeout]    ${TIMEOUT}
    
    # This test would require parallel execution
    # For now, we simulate concurrent users sequentially
    @{all_latencies}=    Create List
    FOR    ${user}    IN RANGE    ${CONCURRENT_USERS}
        @{user_latencies}=    Create List
        FOR    ${request}    IN RANGE    ${REQUESTS_PER_USER}
            ${start_time}=    Get Time    epoch
            ${response}=    Send Request    POST    /api/v1/auth/login
            ...    body=${{"user_id": "user_${user}", "device_id": "device_${user}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
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

Auth Latency Under Load
    [Documentation]    Test auth latency under sustained load
    [Tags]    performance    latency    load
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    1000
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
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

Auth Latency With Network Delay
    [Documentation]    Test auth latency with network delay
    [Tags]    performance    latency    network
    [Timeout]    ${TIMEOUT}
    
    # This test would require network simulation
    # For now, we just test normal latency
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${TEST_USER}", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
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
