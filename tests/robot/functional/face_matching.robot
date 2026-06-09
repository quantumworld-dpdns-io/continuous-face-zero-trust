*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300
${SIMILARITY_THRESHOLD}    0.85

*** Test Cases ***
Face Matching Same Person
    [Documentation]    Test face matching with same person
    [Tags]    face_matching    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_side.jpg
    
    # Compare
    ${response}=    Send Request    POST    /api/v1/face/compare
    ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] > ${SIMILARITY_THRESHOLD}
    Should Be True    ${response}[body][match]

Face Matching Different Person
    [Documentation]    Test face matching with different person
    [Tags]    face_matching    negative
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person2_front.jpg
    
    # Compare
    ${response}=    Send Request    POST    /api/v1/face/compare
    ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] < ${SIMILARITY_THRESHOLD}
    Should Not Be True    ${response}[body][match]

Face Matching Identical Images
    [Documentation]    Test face matching with identical images
    [Tags]    face_matching    positive
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    
    # Compare
    ${response}=    Send Request    POST    /api/v1/face/compare
    ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] > 0.99
    Should Be True    ${response}[body][match]

Face Matching Different Lighting
    [Documentation]    Test face matching with different lighting
    [Tags]    face_matching    robustness
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_bright.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_dark.jpg
    
    # Compare
    ${response}=    Send Request    POST    /api/v1/face/compare
    ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] > ${SIMILARITY_THRESHOLD}

Face Matching Different Pose
    [Documentation]    Test face matching with different pose
    [Tags]    face_matching    robustness
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_left.jpg
    
    # Compare
    ${response}=    Send Request    POST    /api/v1/face/compare
    ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][similarity] > ${SIMILARITY_THRESHOLD}

Face Matching Search
    [Documentation]    Test face search
    [Tags]    face_matching    search
    [Timeout]    ${TIMEOUT}
    
    # Generate query embedding
    ${query_embedding}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    
    # Search
    ${response}=    Send Request    POST    /api/v1/face/search
    ...    body=${{"vector": ${query_embedding}, "limit": 10, "threshold": 0.8}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][results]
    Should Be True    len(${response}[body][results]) > 0

Face Matching Search No Results
    [Documentation]    Test face search with no results
    [Tags]    face_matching    search    negative
    [Timeout]    ${TIMEOUT}
    
    # Generate random embedding
    @{random_embedding}=    Evaluate    [0.1] * 512
    
    # Search
    ${response}=    Send Request    POST    /api/v1/face/search
    ...    body=${{"vector": ${random_embedding}, "limit": 10, "threshold": 0.9}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be Empty    ${response}[body][results]

Face Matching Threshold
    [Documentation]    Test face matching with different thresholds
    [Tags]    face_matching    threshold
    [Timeout]    ${TIMEOUT}
    
    # Generate embeddings
    ${embedding1}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_front.jpg
    ${embedding2}=    Generate Embedding    ${CURDIR}/../test_data/faces/person1_side.jpg
    
    # Compare with different thresholds
    @{thresholds}=    Create List    0.7    0.8    0.9    0.95
    
    FOR    ${threshold}    IN    @{thresholds}
        ${response}=    Send Request    POST    /api/v1/face/compare
        ...    body=${{"embedding1": ${embedding1}, "embedding2": ${embedding2}, "threshold": ${threshold}}}
        
        Should Be Equal As Strings    ${response}[status]    200
        
        IF    ${response}[body][similarity] >= ${threshold}
            Should Be True    ${response}[body][match]
        ELSE
            Should Not Be True    ${response}[body][match]
        END
    END
