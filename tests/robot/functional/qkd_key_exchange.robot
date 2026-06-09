*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/QuantumLibrary.py
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300
${KEY_SIZE}    256

*** Test Cases ***
QKD Key Exchange
    [Documentation]    Test QKD key exchange
    [Tags]    qkd    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
    ...    body=${{"key_size": ${KEY_SIZE}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][shared_secret]
    Should Be Equal As Numbers    ${response}[body][key_size]    ${KEY_SIZE}

QKD Key Exchange Different Sizes
    [Documentation]    Test QKD key exchange with different sizes
    [Tags]    qkd    positive
    [Timeout]    ${TIMEOUT}
    
    @{sizes}=    Create List    128    256    512
    
    FOR    ${size}    IN    @{sizes}
        ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
        ...    body=${{"key_size": ${size}}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][shared_secret]
        Should Be Equal As Numbers    ${response}[body][key_size]    ${size}
    END

QKD Key Exchange Consistency
    [Documentation]    Test QKD key exchange consistency
    [Tags]    qkd    consistency
    [Timeout]    ${TIMEOUT}
    
    # Exchange multiple keys
    @{keys}=    Create List
    FOR    ${i}    IN RANGE    5
        ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
        ...    body=${{"key_size": ${KEY_SIZE}}}
        
        Append To List    ${keys}    ${response}[body][shared_secret]
    END
    
    # Check all keys are unique
    ${unique_keys}=    Evaluate    len(set(${keys}))
    Should Be Equal As Numbers    ${unique_keys}    5

QKD Key Exchange Integrity
    [Documentation]    Test QKD key exchange integrity
    [Tags]    qkd    integrity
    [Timeout]    ${TIMEOUT}
    
    # Exchange key
    ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
    ...    body=${{"key_size": ${KEY_SIZE}}}
    
    ${shared_secret}=    Set Variable    ${response}[body][shared_secret]
    
    # Verify key integrity
    ${integrity}=    Verify Key Integrity    ${shared_secret}
    Should Be True    ${integrity}

QKD Key Exchange Health
    [Documentation]    Test QKD key exchange health
    [Tags]    qkd    health
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/quantum/qkd/health
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Equal As Strings    ${response}[body][status]    healthy
    Should Be True    ${response}[body][channel_active]

QKD Key Exchange Performance
    [Documentation]    Test QKD key exchange performance
    [Tags]    qkd    performance
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
        ...    body=${{"key_size": ${KEY_SIZE}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    ${end_time} - ${start_time}
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 0.1

QKD Key Exchange Error Handling
    [Documentation]    Test QKD key exchange error handling
    [Tags]    qkd    negative
    [Timeout]    ${TIMEOUT}
    
    # Test invalid key size
    ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
    ...    body=${{"key_size": 0}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Invalid key size

QKD Key Exchange Encryption
    [Documentation]    Test QKD key exchange with encryption
    [Tags]    qkd    encryption
    [Timeout]    ${TIMEOUT}
    
    # Exchange key
    ${response}=    Send Request    POST    /api/v1/quantum/qkd/exchange
    ...    body=${{"key_size": ${KEY_SIZE}}}
    
    ${shared_secret}=    Set Variable    ${response}[body][shared_secret}
    
    # Encrypt data
    ${plaintext}=    Set Variable    "Hello, World!"
    ${ciphertext}=    Encrypt Data    ${plaintext}    ${shared_secret}
    
    # Decrypt data
    ${decrypted}=    Decrypt Data    ${ciphertext}    ${shared_secret}
    
    Should Be Equal As Strings    ${decrypted}    ${plaintext}
