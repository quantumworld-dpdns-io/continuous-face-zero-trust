*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    3600
${INITIAL_LOAD}    100
${MAX_LOAD}    10000
${STEP_SIZE}    100
${STEP_DURATION}    60
${TARGET_ERROR_RATE}    0.05

*** Test Cases ***
Stress Test Authentication
    [Documentation]    Stress test for authentication
    [Tags]    performance    stress    authentication
    [Timeout]    ${TIMEOUT}
    
    ${current_load}=    Set Variable    ${INITIAL_LOAD}
    ${breakpoint_found}=    Set Variable    False
    ${breakpoint_load}=    Set Variable    0
    
    WHILE    ${current_load} <= ${MAX_LOAD}    AND    ${breakpoint_found} == False
        Log    Testing with load: ${current_load}
        
        @{error_counts}=    Create List
        @{latencies}=    Create List
        
        FOR    ${i}    IN RANGE    ${STEP_DURATION}
            FOR    ${j}    IN RANGE    ${current_load}
                ${start_time}=    Get Time    epoch
                ${response}=    Send Request    POST    /api/v1/auth/login
                ...    body=${{"user_id": "stress_user_${i}_${j}", "device_id": "device_${j}", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
                ${end_time}=    Get Time    epoch
                
                ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
                Append To List    ${latencies}    ${latency}
                
                IF    ${response}[status] != 200
                    Append To List    ${error_counts}    1
                END
            END
        END
        
        ${total_errors}=    Evaluate    len(${error_counts})
        ${total_requests}=    Evaluate    ${current_load} * ${STEP_DURATION}
        ${error_rate}=    Evaluate    ${total_errors} / ${total_requests}
        ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
        
        Log    Load: ${current_load}, Error rate: ${error_rate}, Avg latency: ${avg_latency}ms
        
        IF    ${error_rate} > ${TARGET_ERROR_RATE}
            ${breakpoint_found}=    Set Variable    True
            ${breakpoint_load}=    Set Variable    ${current_load}
        END
        
        ${current_load}=    Evaluate    ${current_load} + ${STEP_SIZE}
    END
    
    IF    ${breakpoint_found}
        Log    Breakpoint found at load: ${breakpoint_load}
    ELSE
        Log    No breakpoint found within max load
    END

Stress Test Face Processing
    [Documentation]    Stress test for face processing
    [Tags]    performance    stress    face
    [Timeout]    ${TIMEOUT}
    
    ${current_load}=    Set Variable    ${INITIAL_LOAD}
    ${breakpoint_found}=    Set Variable    False
    ${breakpoint_load}=    Set Variable    0
    
    WHILE    ${current_load} <= ${MAX_LOAD}    AND    ${breakpoint_found} == False
        Log    Testing with load: ${current_load}
        
        @{error_counts}=    Create List
        @{latencies}=    Create List
        
        FOR    ${i}    IN RANGE    ${STEP_DURATION}
            FOR    ${j}    IN RANGE    ${current_load}
                ${start_time}=    Get Time    epoch
                ${response}=    Send Request    POST    /api/v1/face/embed
                ...    body=${{"image": "${CURDIR}/../test_data/faces/front.jpg"}}
                ${end_time}=    Get Time    epoch
                
                ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
                Append To List    ${latencies}    ${latency}
                
                IF    ${response}[status] != 200
                    Append To List    ${error_counts}    1
                END
            END
        END
        
        ${total_errors}=    Evaluate    len(${error_counts})
        ${total_requests}=    Evaluate    ${current_load} * ${STEP_DURATION}
        ${error_rate}=    Evaluate    ${total_errors} / ${total_requests}
        ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
        
        Log    Load: ${current_load}, Error rate: ${error_rate}, Avg latency: ${avg_latency}ms
        
        IF    ${error_rate} > ${TARGET_ERROR_RATE}
            ${breakpoint_found}=    Set Variable    True
            ${breakpoint_load}=    Set Variable    ${current_load}
        END
        
        ${current_load}=    Evaluate    ${current_load} + ${STEP_SIZE}
    END
    
    IF    ${breakpoint_found}
        Log    Breakpoint found at load: ${breakpoint_load}
    ELSE
        Log    No breakpoint found within max load
    END

Stress Test Crypto Operations
    [Documentation]    Stress test for crypto operations
    [Tags]    performance    stress    crypto
    [Timeout]    ${TIMEOUT}
    
    ${current_load}=    Set Variable    ${INITIAL_LOAD}
    ${breakpoint_found}=    Set Variable    False
    ${breakpoint_load}=    Set Variable    0
    
    WHILE    ${current_load} <= ${MAX_LOAD}    AND    ${breakpoint_found} == False
        Log    Testing with load: ${current_load}
        
        @{error_counts}=    Create List
        @{latencies}=    Create List
        
        FOR    ${i}    IN RANGE    ${STEP_DURATION}
            FOR    ${j}    IN RANGE    ${current_load}
                ${start_time}=    Get Time    epoch
                ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
                ...    body=${{"algorithm": "kyber-768"}}
                ${end_time}=    Get Time    epoch
                
                ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
                Append To List    ${latencies}    ${latency}
                
                IF    ${response}[status] != 200
                    Append To List    ${error_counts}    1
                END
            END
        END
        
        ${total_errors}=    Evaluate    len(${error_counts})
        ${total_requests}=    Evaluate    ${current_load} * ${STEP_DURATION}
        ${error_rate}=    Evaluate    ${total_errors} / ${total_requests}
        ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
        
        Log    Load: ${current_load}, Error rate: ${error_rate}, Avg latency: ${avg_latency}ms
        
        IF    ${error_rate} > ${TARGET_ERROR_RATE}
            ${breakpoint_found}=    Set Variable    True
            ${breakpoint_load}=    Set Variable    ${current_load}
        END
        
        ${current_load}=    Evaluate    ${current_load} + ${STEP_SIZE}
    END
    
    IF    ${breakpoint_found}
        Log    Breakpoint found at load: ${breakpoint_load}
    ELSE
        Log    No breakpoint found within max load
    END
