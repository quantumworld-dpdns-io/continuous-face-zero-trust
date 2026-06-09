*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/ZKLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
Generate Face Proof
    [Documentation]    Test generating face proof
    [Tags]    zk    proof    face    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate embedding
    ${embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    ${stored_hash}=    Hash Embedding    ${embedding}
    
    # Generate proof
    ${response}=    Send Request    POST    /api/v1/zk/face-proof
    ...    body=${{"embedding": ${embedding}, "stored_hash": "${stored_hash}", "threshold": 0.85}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][proof]
    Should Not Be Empty    ${response}[body][commitment]
    Should Be True    ${response}[body][proving_time_ms] > 0

Generate Liveness Proof
    [Documentation]    Test generating liveness proof
    [Tags]    zk    proof    liveness    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate image features
    ${features}=    Generate Image Features    ${CURDIR}/../test_data/faces/live.jpg
    ${model_hash}=    Hash Model
    
    # Generate proof
    ${response}=    Send Request    POST    /api/v1/zk/liveness-proof
    ...    body=${{"image_features": ${features}, "liveness_threshold": 0.9, "model_hash": "${model_hash}"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][proof]
    Should Not Be Empty    ${response}[body][commitment]
    Should Be True    ${response}[body][proving_time_ms] > 0

Generate Age Proof
    [Documentation]    Test generating age proof
    [Tags]    zk    proof    age    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate age estimate
    ${age_estimate}=    Set Variable    25
    ${model_hash}=    Hash Model
    
    # Generate proof
    ${response}=    Send Request    POST    /api/v1/zk/generate
    ...    body=${{"circuit": "age_verification", "witness": {"age_estimate": ${age_estimate}}, "public_inputs": {"age_threshold": 18, "model_hash": "${model_hash}"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][proof]
    Should Be True    ${response}[body][proving_time_ms] > 0

Generate Membership Proof
    [Documentation]    Test generating membership proof
    [Tags]    zk    proof    membership    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate member hash
    ${member_hash}=    Hash Data    "member_123"
    ${merkle_root}=    Hash Data    "merkle_root"
    
    # Generate proof
    ${response}=    Send Request    POST    /api/v1/zk/generate
    ...    body=${{"circuit": "membership_proof", "witness": {"member_hash": "${member_hash}"}, "public_inputs": {"merkle_root": "${merkle_root}"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][proof]
    Should Be True    ${response}[body][proving_time_ms] > 0

Generate Proof Invalid Circuit
    [Documentation]    Test generating proof with invalid circuit
    [Tags]    zk    proof    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/zk/generate
    ...    body=${{"circuit": "invalid_circuit", "witness": {}, "public_inputs": {}}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Invalid circuit

Generate Proof Missing Witness
    [Documentation]    Test generating proof with missing witness
    [Tags]    zk    proof    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/zk/generate
    ...    body=${{"circuit": "face_matching", "witness": {}, "public_inputs": {}}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Missing witness

Generate Proof Performance
    [Documentation]    Test proof generation performance
    [Tags]    zk    proof    performance
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/zk/generate
        ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc123"}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 500
