*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/CryptoLibrary.py
Library    ../resources/libraries/FaceMLLibrary.py
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TEST_USER}    test_user_enroll_001
${TIMEOUT}    300

*** Test Cases ***
Enroll With Single Image
    [Documentation]    Test enrollment with single face image
    [Tags]    enrollment    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_single", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    Should Not Be Empty    ${response}[body][embedding_id]

Enroll With Multiple Images
    [Documentation]    Test enrollment with multiple face images
    [Tags]    enrollment    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_multiple", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg", "${CURDIR}/../test_data/faces/left.jpg", "${CURDIR}/../test_data/faces/right.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    Should Not Be Empty    ${response}[body][embedding_id]

Enroll With Low Quality Image
    [Documentation]    Test enrollment with low quality image
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_low_quality", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/low_quality.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Image quality too low

Enroll Without Face
    [Documentation]    Test enrollment without face in image
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_no_face", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/no_face.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    No face detected

Enroll With Multiple Faces
    [Documentation]    Test enrollment with multiple faces in image
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_multi_face", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/multiple_faces.jpg"]}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Multiple faces detected

Enroll Existing User
    [Documentation]    Test enrolling an existing user
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    # First enroll
    ${response1}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_existing", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg"]}}
    
    # Try to enroll again
    ${response2}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_existing", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg"]}}
    
    Should Be Equal As Strings    ${response2}[status]    409
    Should Contain    ${response2}[body][message]    User already enrolled

Enroll With Invalid Image Format
    [Documentation]    Test enrollment with invalid image format
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_invalid_format", "device_id": "test_device_001", "face_images": ["invalid_base64_data"]}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Invalid image format

Enroll With Empty Images
    [Documentation]    Test enrollment with empty images list
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_empty", "device_id": "test_device_001", "face_images": []}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    At least one image required

Enroll With Too Many Images
    [Documentation]    Test enrollment with too many images
    [Tags]    enrollment    negative
    [Timeout]    ${TIMEOUT}
    
    @{images}=    Create List
    FOR    ${i}    IN RANGE    20
        Append To List    ${images}    ${CURDIR}/../test_data/faces/front.jpg
    END
    
    ${response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_too_many", "device_id": "test_device_001", "face_images": ${images}}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Too many images

Enroll And Login
    [Documentation]    Test enrollment followed by login
    [Tags]    enrollment    integration
    [Timeout]    ${TIMEOUT}
    
    # Enroll
    ${enroll_response}=    Send Request    POST    /api/v1/auth/enroll
    ...    body=${{"user_id": "${TEST_USER}_enroll_login", "device_id": "test_device_001", "face_images": ["${CURDIR}/../test_data/faces/front.jpg"]}}
    
    Should Be Equal As Strings    ${enroll_response}[status]    200
    
    # Login
    ${login_response}=    Send Request    POST    /api/v1/auth/login
    ...    body=${{"user_id": "${TEST_USER}_enroll_login", "device_id": "test_device_001", "face_image": "${CURDIR}/../test_data/faces/front.jpg"}}
    
    Should Be Equal As Strings    ${login_response}[status]    200
    Should Not Be Empty    ${login_response}[body][token]
