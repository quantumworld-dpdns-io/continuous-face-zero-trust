*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    600
${TARGET_CONCURRENT_USERS}    1000
${REQUESTS_PER_USER}    10
${RAMP_UP_TIME}    60

*** Test Cases ***
Concurrent Authentication
    [Documentation]    Test concurrent authentication
    [Tags]    performance    concurrent    authentication
    [Timeout]    ${TIMEOUT}
    
    @{users}=    Create List
    FOR    ${i}    IN RANGE    ${TARGET_CONCURRENT_USERS}
        ${user_id}=    Set Variable    concurrent_user_${i}
        ${device_id}=    Set Variable    device_${i}
        
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${user_id}", "device_id": "${device_id}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        
        IF    ${response}[status] != 200
            Log    User ${user_id} failed to authenticate: ${response}[status]
            Continue For Loop
        END
        
        ${token}=    Set Variable    ${response}[body][token]
        Append To List    ${users}    ${{"user_id": "${user_id}", "token": "${token}"}}
    END
    
    Should Be True    len(${users}) >= ${TARGET_CONCURRENT_USERS} * 0.95
    
    Log    Successfully authenticated ${len(${users})} users

Concurrent Session Management
    [Documentation]    Test concurrent session management
    [Tags]    performance    concurrent    sessions
    [Timeout]    ${TIMEOUT}
    
    # Create sessions first
    @{sessions}=    Create List
    FOR    ${i}    IN RANGE    ${TARGET_CONCURRENT_USERS}
        ${user_id}=    Set Variable    session_user_${i}
        ${device_id}=    Set Variable    device_${i}
        
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "${user_id}", "device_id": "${device_id}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        
        IF    ${response}[status] != 200
            Continue For Loop
        END
        
        ${token}=    Set Variable    ${response}[body][token]
        Append To List    ${sessions}    ${{"user_id": "${user_id}", "token": "${token}"}}
    END
    
    # Manage sessions concurrently
    @{latencies}=    Create List
    FOR    ${session}    IN    @{sessions}
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    GET    /api/v1/sessions/${session}[user_id]
        ...    headers=${{"Authorization": "Bearer ${session}[token]"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    
    Log    Average session management latency: ${avg_latency}ms

Concurrent Face Processing
    [Documentation]    Test concurrent face processing
    [Tags]    performance    concurrent    face
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    ${TARGET_CONCURRENT_USERS}
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/face/embed
        ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    ${p99_latency}=    Evaluate    sorted(${latencies})[int(len(${latencies}) * 0.99)]
    
    Log    Average face processing latency: ${avg_latency}ms
    Log    P99 face processing latency: ${p99_latency}ms
    
    Should Be True    ${p99_latency} < 200

Concurrent Mixed Workload
    [Documentation]    Test concurrent mixed workload
    [Tags]    performance    concurrent    mixed
    [Timeout]    ${TIMEOUT}
    
    @{auth_latencies}=    Create List
    @{face_latencies}=    Create List
    @{crypto_latencies}=    Create List
    
    FOR    ${i}    IN RANGE    ${TARGET_CONCURRENT_USERS}
        # Authentication
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "user_${i}", "device_id": "device_${i}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
        ${end_time}=    Get Time    epoch
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${auth_latencies}    ${latency}
        
        # Face processing
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/face/embed
        ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
        ${end_time}=    Get Time    epoch
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${face_latencies}    ${latency}
        
        # Crypto operations
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
        ...    body=${{"algorithm": "kyber-768"}}
        ${end_time}=    Get Time    epoch
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${crypto_latencies}    ${latency}
    END
    
    ${auth_avg}=    Evaluate    sum(${auth_latencies}) / len(${auth_latencies})
    ${face_avg}=    Evaluate    sum(${face_latencies}) / len(${face_latencies})
    ${crypto_avg}=    Evaluate    sum(${crypto_latencies}) / len(${crypto_latencies})
    
    Log    Auth average latency: ${auth_avg}ms
    Log    Face average latency: ${face_avg}ms
    Log    Crypto average latency: ${crypto_avg}ms
    
    Should Be True    ${auth_avg} < 200
    Should Be True    ${face_avg} < 200
    Should Be True    ${crypto_avg} < 100
