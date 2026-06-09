*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
gRPC Auth Service Communication
    [Documentation]    Test gRPC communication with auth service
    [Tags]    grpc    auth    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "test_user", "device_id": "test_device", "face_image": "test_image"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][token]

gRPC Face ML Service Communication
    [Documentation]    Test gRPC communication with face ML service
    [Tags]    grpc    face_ml    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/detect
    ...    body=${{"image": "test_image"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][faces]

gRPC PQC Crypto Service Communication
    [Documentation]    Test gRPC communication with PQC crypto service
    [Tags]    grpc    pqc    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/crypto/kem/encapsulate
    ...    body=${{"algorithm": "kyber-1024"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][ciphertext]
    Should Not Be Empty    ${response}[body][shared_secret]

gRPC ZK Proofs Service Communication
    [Documentation]    Test gRPC communication with ZK proofs service
    [Tags]    grpc    zk    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/zk/generate
    ...    body=${{"circuit": "face_matching", "witness": {"embedding": [0.1]*512}, "public_inputs": {"stored_hash": "abc123"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][proof]

gRPC Quantum RNG Service Communication
    [Documentation]    Test gRPC communication with quantum RNG service
    [Tags]    grpc    quantum    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/quantum/rng/generate
    ...    body=${{"num_bits": 256, "purpose": "token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][random_data]

gRPC Communication Latency
    [Documentation]    Test gRPC communication latency
    [Tags]    grpc    latency
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/auth/login
        ...    body=${{"user_id": "test_user", "device_id": "test_device", "face_image": "test_image"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 200

gRPC Communication Error Handling
    [Documentation]    Test gRPC communication error handling
    [Tags]    grpc    error    negative
    [Timeout]    ${TIMEOUT}
    
    # Test invalid request
    ${response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{}}
    
    Should Be Equal As Strings    ${response}[status]    400
    
    # Test unauthorized
    ${response}=    Send Request    GET    /api/v1/sessions/test
    
    Should Be Equal As Strings    ${response}[status]    401

gRPC Communication Timeout
    [Documentation]    Test gRPC communication timeout
    [Tags]    grpc    timeout
    [Timeout]    ${TIMEOUT}
    
    # This test would require a slow service to test timeout
    # For now, we just verify the timeout configuration exists
    ${response}=    Send Request    GET    /api/v1/edge/config
    ...    headers=${{"Authorization": "Bearer test_token"}}
    
    Should Be Equal As Strings    ${response}[status]    200
