*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/QuantumLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    600
${TARGET_THROUGHPUT}    1000
${CONCURRENT_USERS}    50
${REQUESTS_PER_USER}    100

*** Test Cases ***
Quantum RNG Throughput Single User
    [Documentation]    Test quantum RNG throughput for single user
    [Tags]    performance    throughput    single_user
    [Timeout]    ${TIMEOUT}
    
    @{throughputs}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${count}=    Set Variable    0
        WHILE    True
            ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
            ...    body=${{"num_bits": 256, "purpose": "token"}}
            ${count}=    Evaluate    ${count} + 1
            ${end_time}=    Get Time    epoch
            ${elapsed}=    Evaluate    ${end_time} - ${start_time}
            IF    ${elapsed} >= 1    BREAK
        END
        
        ${throughput}=    Evaluate    ${count} / ${elapsed}
        Append To List    ${throughputs}    ${throughput}
    END
    
    ${avg_throughput}=    Evaluate    sum(${throughputs}) / len(${throughputs})
    
    Log    Average throughput: ${avg_throughput} requests/second
    
    Should Be True    ${avg_throughput} >= ${TARGET_THROUGHPUT}

Quantum RNG Throughput Concurrent
    [Documentation]    Test quantum RNG throughput with concurrent users
    [Tags]    performance    throughput    concurrent
    [Timeout]    ${TIMEOUT}
    
    @{all_throughputs}=    Create List
    FOR    ${user}    IN RANGE    ${CONCURRENT_USERS}
        ${start_time}=    Get Time    epoch
        ${count}=    Set Variable    0
        WHILE    True
            ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
            ...    body=${{"num_bits": 256, "purpose": "token"}}
            ${count}=    Evaluate    ${count} + 1
            ${end_time}=    Get Time    epoch
            ${elapsed}=    Evaluate    ${end_time} - ${start_time}
            IF    ${elapsed} >= 1    BREAK
        END
        
        ${throughput}=    Evaluate    ${count} / ${elapsed}
        Append To List    ${all_throughputs}    ${throughput}
    END
    
    ${total_throughput}=    Evaluate    sum(${all_throughputs})
    
    Log    Total throughput: ${total_throughput} requests/second
    
    Should Be True    ${total_throughput} >= ${TARGET_THROUGHPUT} * ${CONCURRENT_USERS} * 0.5

Quantum RNG Throughput Different Sizes
    [Documentation]    Test quantum RNG throughput for different sizes
    [Tags]    performance    throughput    sizes
    [Timeout]    ${TIMEOUT}
    
    @{sizes}=    Create List    64    128    256    512    1024
    
    FOR    ${size}    IN    @{sizes}
        ${throughputs}=    Create List
        FOR    ${i}    IN RANGE    10
            ${start_time}=    Get Time    epoch
            ${count}=    Set Variable    0
            WHILE    True
                ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
                ...    body=${{"num_bits": ${size}, "purpose": "token"}}
                ${count}=    Evaluate    ${count} + 1
                ${end_time}=    Get Time    epoch
                ${elapsed}=    Evaluate    ${end_time} - ${start_time}
                IF    ${elapsed} >= 1    BREAK
            END
            
            ${throughput}=    Evaluate    ${count} / ${elapsed}
            Append To List    ${throughputs}    ${throughput}
        END
        
        ${avg_throughput}=    Evaluate    sum(${throughputs}) / len(${throughputs})
        Log    Throughput for ${size} bits: ${avg_throughput} requests/second
    END

Quantum RNG Throughput Sustained Load
    [Documentation]    Test quantum RNG throughput under sustained load
    [Tags]    performance    throughput    sustained
    [Timeout]    ${TIMEOUT}
    
    @{throughputs}=    Create List
    FOR    ${i}    IN RANGE    60
        ${start_time}=    Get Time    epoch
        ${count}=    Set Variable    0
        WHILE    True
            ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
            ...    body=${{"num_bits": 256, "purpose": "token"}}
            ${count}=    Evaluate    ${count} + 1
            ${end_time}=    Get Time    epoch
            ${elapsed}=    Evaluate    ${end_time} - ${start_time}
            IF    ${elapsed} >= 1    BREAK
        END
        
        ${throughput}=    Evaluate    ${count} / ${elapsed}
        Append To List    ${throughputs}    ${throughput}
    END
    
    ${avg_throughput}=    Evaluate    sum(${throughputs}) / len(${throughputs})
    ${min_throughput}=    Evaluate    min(${throughputs})
    
    Log    Average throughput: ${avg_throughput} requests/second
    Log    Minimum throughput: ${min_throughput} requests/second
    
    Should Be True    ${min_throughput} >= ${TARGET_THROUGHPUT} * 0.8
