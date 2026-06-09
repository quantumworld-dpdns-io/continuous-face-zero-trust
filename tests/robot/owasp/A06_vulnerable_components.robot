*** Settings ***
Resource    ../resources/keywords/security_keywords.robot
Resource    ../resources/keywords/api_keywords.robot
Library     Collections
Library     Process

*** Test Cases ***
A06-TC01 Dependency Scanning
    [Documentation]    OWASP A06: Vulnerable Components — dependency scan
    ${result}=    Run Process    pip    audit    -r    services/auth-api/requirements.txt    shell=True    timeout=60s
    Log    Dependency scan completed: ${result.returncode}

A06-TC02 Container Image Scanning
    [Documentation]    OWASP A06: Container vulnerability scanning
    ${result}=    Run Process    trivy    image    --severity    HIGH,CRITICAL    python:3.12-slim    shell=True    timeout=120s
    Log    Container scan completed

A06-TC03 SBOM Validation
    [Documentation]    OWASP A06: Software Bill of Materials
    ${result}=    Run Process    syft    packages    ./services    -o    spdx-json    shell=True    timeout=60s
    Log    SBOM generation completed: ${result.returncode}
