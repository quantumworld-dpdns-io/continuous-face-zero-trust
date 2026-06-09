*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
Liveness Detection Live Face
    [Documentation]    Test liveness detection with live face
    [Tags]    liveness    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/live.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][is_live]
    Should Be True    ${response}[body][confidence] > 0.9
    Should Be Equal As Strings    ${response}[body][attack_type]    none

Liveness Detection Photo Attack
    [Documentation]    Test liveness detection with photo attack
    [Tags]    liveness    negative    attack
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/photo.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][is_live]
    Should Be Equal As Strings    ${response}[body][attack_type]    photo

Liveness Detection Video Attack
    [Documentation]    Test liveness detection with video attack
    [Tags]    liveness    negative    attack
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/video_frame.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][is_live]
    Should Be Equal As Strings    ${response}[body][attack_type]    video

Liveness Detection Mask Attack
    [Documentation]    Test liveness detection with mask attack
    [Tags]    liveness    negative    attack
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/mask.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][is_live]
    Should Be Equal As Strings    ${response}[body][attack_type]    mask

Liveness Detection No Face
    [Documentation]    Test liveness detection without face
    [Tags]    liveness    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/no_face.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    No face detected

Liveness Detection Multiple Faces
    [Documentation]    Test liveness detection with multiple faces
    [Tags]    liveness    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/multiple_faces.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Multiple faces detected

Liveness Detection Low Quality
    [Documentation]    Test liveness detection with low quality image
    [Tags]    liveness    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/low_quality.jpg"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Image quality too low

Liveness Detection With Video
    [Documentation]    Test liveness detection with video
    [Tags]    liveness    positive    video
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/face/liveness
    ...    body=${{"image": "${CURDIR}/../test_data/faces/live.jpg", "video": "${CURDIR}/../test_data/videos/live.mp4"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][is_live]
    Should Be True    ${response}[body][confidence] > 0.95

Liveness Detection Consistency
    [Documentation]    Test liveness detection consistency
    [Tags]    liveness    consistency
    [Timeout]    ${TIMEOUT}
    
    @{results}=    Create List
    FOR    ${i}    IN RANGE    10
        ${response}=    Send Request    POST    /api/v1/face/liveness
        ...    body=${{"image": "${CURDIR}/../test_data/faces/live.jpg"}}
        
        Append To List    ${results}    ${response}[body][is_live]
    END
    
    # Check consistency
    ${true_count}=    Evaluate    sum(1 for x in ${results} if x == True)
    Should Be True    ${true_count} >= 9
