*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/QuantumLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300
${MIN_ENTROPY}    0.95

*** Test Cases ***
QRNG Generate Random Bits
    [Documentation]    Test QRNG random bit generation
    [Tags]    qrng    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
    ...    body=${{"num_bits": 256, "purpose": "token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][random_data]
    Should Be True    ${response}[body][health_passed]
    Should Be True    ${response}[body][min_entropy] > ${MIN_ENTROPY}

QRNG Generate Different Sizes
    [Documentation]    Test QRNG with different bit sizes
    [Tags]    qrng    positive
    [Timeout]    ${TIMEOUT}
    
    @{sizes}=    Create List    128    256    512    1024
    
    FOR    ${size}    IN    @{sizes}
        ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
        ...    body=${{"num_bits": ${size}, "purpose": "token"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][random_data]
        Should Be True    ${response}[body][health_passed]
    END

QRNG Health Check
    [Documentation]    Test QRNG health check
    [Tags]    qrng    health
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/quantum/rng/health
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Equal As Strings    ${response}[body][status]    healthy
    Should Be True    ${response}[body][hardware_available]
    Should Be True    ${response}[body][simulator_available]

QRNG Entropy Pool
    [Documentation]    Test QRNG entropy pool
    [Tags]    qrng    entropy
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/quantum/rng/pool
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][pool_size_bits] > 0
    Should Be True    ${response}[body][available_bits] > 0
    Should Be True    ${response}[body][fill_rate] > 0

QRNG Hardware Mode
    [Documentation]    Test QRNG hardware mode
    [Tags]    qrng    hardware
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
    ...    body=${{"num_bits": 256, "purpose": "token", "require_hardware": true}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Equal As Strings    ${response}[body][source]    hardware
    Should Be True    ${response}[body][health_passed]

QRNG Simulator Mode
    [Documentation]    Test QRNG simulator mode
    [Tags]    qrng    simulator
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
    ...    body=${{"num_bits": 256, "purpose": "token", "require_hardware": false}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][source] == "hardware" or ${response}[body][source] == "simulator"
    Should Be True    ${response}[body][health_passed]

QRNG Multiple Requests
    [Documentation]    Test QRNG with multiple requests
    [Tags]    qrng    performance
    [Timeout]    ${TIMEOUT}
    
    @{results}=    Create List
    FOR    ${i}    IN RANGE    10
        ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
        ...    body=${{"num_bits": 256, "purpose": "token"}}
        
        Append To List    ${results}    ${response}[body][random_data]
    END
    
    # Check all responses are unique
    ${unique_results}=    Evaluate    len(set(${results}))
    Should Be Equal As Numbers    ${unique_results}    10

QRNG Different Purposes
    [Documentation]    Test QRNG for different purposes
    [Tags]    qrng    purpose
    [Timeout]    ${TIMEOUT}
    
    @{purposes}=    Create List    token    nonce    zk_proof    key_derivation
    
    FOR    ${purpose}    IN    @{purposes}
        ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
        ...    body=${{"num_bits": 256, "purpose": "${purpose}"}}
        
        Should Be Equal As Strings    ${response}[status]    200
        Should Not Be Empty    ${response}[body][random_data]
        Should Be True    ${response}[body][health_passed]
    END

QRNG Statistical Tests
    [Documentation]    Test QRNG statistical properties
    [Tags]    qrng    statistical
    [Timeout]    ${TIMEOUT}
    
    # Generate large sample
    ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
    ...    body=${{"num_bits": 10000, "purpose": "statistical"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][health_passed]
    Should Be True    ${response}[body][min_entropy] > ${MIN_ENTROPY}
