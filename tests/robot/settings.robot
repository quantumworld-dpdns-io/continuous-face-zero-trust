*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    String
Library    OperatingSystem
Library    Process
Library    JSONLibrary
Resource   resources/keywords/auth_keywords.robot
Resource   resources/keywords/security_keywords.robot
Resource   resources/keywords/api_keywords.robot
Variables  resources/variables/common.yaml

Suite Setup    Setup Test Environment
Suite Teardown    Teardown Test Environment

*** Variables ***
${BASE_URL}    http://localhost:8000
${FACE_ML_URL}    http://localhost:8001
${ZK_URL}    http://localhost:8002
${QUANTUM_URL}    http://localhost:8003
${PQC_URL}    http://localhost:8006
${VECTOR_URL}    http://localhost:8008

*** Keywords ***
Setup Test Environment
    Create Session    auth    ${BASE_URL}
    Create Session    face    ${FACE_ML_URL}
    Create Session    zk      ${ZK_URL}
    Create Session    quantum ${QUANTUM_URL}
    Create Session    pqc     ${PQC_URL}
    Create Session    vector  ${VECTOR_URL}

Teardown Test Environment
    Delete All Sessions
