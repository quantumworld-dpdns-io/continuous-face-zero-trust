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
Verify Face Proof
    [Documentation]    Test verifying face proof
    [Tags]    zk    verify    face    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate embedding
    ${embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    ${stored_hash}=    Hash Embedding    ${embedding}
    
    # Generate proof
    ${proof_response}=    Send Request    POST    /api/v1/zk/face-proof
    ...    body=${{"embedding": ${embedding}, "stored_hash": "${stored_hash}", "threshold": 0.85}}
    
    ${proof}=    Set Variable    ${proof_response}[body][proof]
    
    # Verify proof
    ${response}=    Send Request    POST    /api/v1/zk/verify
    ...    body=${{"circuit": "face_matching", "proof": "${proof}", "public_inputs": {"stored_hash": "${stored_hash}", "threshold": 0.85}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][valid]
    Should Be True    ${response}[body][verification_time_ms] > 0

Verify Liveness Proof
    [Documentation]    Test verifying liveness proof
    [Tags]    zk    verify    liveness    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate image features
    ${features}=    Generate Image Features    ${CURDIR}/../test_data/faces/live.jpg
    ${model_hash}=    Hash Model
    
    # Generate proof
    ${proof_response}=    Send Request    POST    /api/v1/zk/liveness-proof
    ...    body=${{"image_features": ${features}, "liveness_threshold": 0.9, "model_hash": "${model_hash}"}}
    
    ${proof}=    Set Variable    ${proof_response}[body][proof]
    
    # Verify proof
    ${response}=    Send Request    POST    /api/v1/zk/verify
    ...    body=${{"circuit": "liveness_check", "proof": "${proof}", "public_inputs": {"liveness_threshold": 0.9, "model_hash": "${model_hash}"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][valid]
    Should Be True    ${response}[body][verification_time_ms] > 0

Verify Invalid Proof
    [Documentation]    Test verifying invalid proof
    [Tags]    zk    verify    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/zk/verify
    ...    body=${{"circuit": "face_matching", "proof": "invalid_proof", "public_inputs": {"stored_hash": "abc123", "threshold": 0.85}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][valid]

Verify Proof Wrong Circuit
    [Documentation]    Test verifying proof with wrong circuit
    [Tags]    zk    verify    negative
    [Timeout]    ${TIMEOUT}
    
    # Generate embedding
    ${embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    ${stored_hash}=    Hash Embedding    ${embedding}
    
    # Generate proof
    ${proof_response}=    Send Request    POST    /api/v1/zk/face-proof
    ...    body=${{"embedding": ${embedding}, "stored_hash": "${stored_hash}", "threshold": 0.85}}
    
    ${proof}=    Set Variable    ${proof_response}[body][proof]
    
    # Verify with wrong circuit
    ${response}=    Send Request    POST    /api/v1/zk/verify
    ...    body=${{"circuit": "liveness_check", "proof": "${proof}", "public_inputs": {"liveness_threshold": 0.9, "model_hash": "abc123"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][valid]

Verify Proof Performance
    [Documentation]    Test proof verification performance
    [Tags]    zk    verify    performance
    [Timeout]    ${TIMEOUT}
    
    # Generate embedding
    ${embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/front.jpg
    ${stored_hash}=    Hash Embedding    ${embedding}
    
    # Generate proof
    ${proof_response}=    Send Request    POST    /api/v1/zk/face-proof
    ...    body=${{"embedding": ${embedding}, "stored_hash": "${stored_hash}", "threshold": 0.85}}
    
    ${proof}=    Set Variable    ${proof_response}[body][proof]
    
    # Verify multiple times
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/zk/verify
        ...    body=${{"circuit": "face_matching", "proof": "${proof}", "public_inputs": {"stored_hash": "${stored_hash}", "threshold": 0.85}}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 10
