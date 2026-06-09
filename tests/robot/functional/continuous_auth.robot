*** Settings ***
Resource    ../resources/keywords/auth_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections

Suite Setup    Create Sessions
Suite Teardown    Delete All Sessions

*** Variables ***
${BASE_URL}    http://localhost:8000

*** Keywords ***
Create Sessions
    Create Session    auth    ${BASE_URL}

*** Test Cases ***
Face Enrollment — Multiple Images
    [Documentation]    Enroll face with multiple images
    ${images}=    Create List    test_data/face_01.jpg    test_data/face_02.jpg    test_data/face_03.jpg
    ${response}=    Enroll Face    ${images}    user-001    tenant-1
    Should Be Equal As Numbers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    ${json}[success]
    Should Be Equal As Numbers    ${json}[face_count]    3
    Log    Enrollment successful: ${json}[enrollment_id]

Face Enrollment — Insufficient Images
    [Documentation]    Enroll with only 1 image (should fail)
    ${images}=    Create List    test_data/face_01.jpg
    ${response}=    Enroll Face    ${images}    user-002
    Should Not Be Equal As Numbers    ${response.status_code}    200
    Log    Insufficient images rejected

Continuous Verification — Same Person
    [Documentation]    Continuous verification with same person
    ${auth_response}=    Authenticate User    test_data/face_real.jpg    device-id-cv-01    web
    ${json}=    Set Variable    ${auth_response.json()}
    Should Be True    ${json}[authenticated]

    Sleep    5s
    ${verify_response}=    Authenticate User    test_data/face_real.jpg    device-id-cv-01    continuous
    ${verify_json}=    Set Variable    ${verify_response.json()}
    Should Be True    ${verify_json}[authenticated]
    Log    Continuous verification passed for same person

Continuous Verification — Different Person
    [Documentation]    Continuous verification with different person
    ${auth_response}=    Authenticate User    test_data/face_real.jpg    device-id-cv-02    web
    ${json}=    Set Variable    ${auth_response.json()}
    Should Be True    ${json}[authenticated]

    Sleep    5s
    ${verify_response}=    Authenticate User    test_data/face_other.jpg    device-id-cv-02    continuous
    ${verify_json}=    Set Variable    ${verify_response.json()}
    Should Not Be True    ${verify_json}[authenticated]
    Log    Continuous verification correctly rejected different person
