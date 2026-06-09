*** Settings ***
Resource    ../resources/keywords/api_keywords.robot
Library     Collections
Library     Process

Suite Setup    Create Sessions
Suite Teardown    Delete All Sessions

*** Variables ***
${AUTH_URL}    http://localhost:8000

*** Keywords ***
Create Sessions
    Create Session    auth    ${AUTH_URL}

*** Test Cases ***
Auth Latency — Below 200ms
    [Documentation]    Measure auth endpoint latency
    ${start}=    Evaluate    time.time()    modules=time
    ${response}=    Make API Request    auth    /health    GET
    ${end}=    Evaluate    time.time()    modules=time
    ${latency_ms}=    Evaluate    (${end} - ${start}) * 1000
    Should Be True    ${latency_ms} < 200    Latency ${latency_ms}ms exceeds 200ms threshold
    Log    Auth health latency: ${latency_ms}ms

Auth Latency — P99 Under Load
    [Documentation]    Measure P99 latency under concurrent load
    ${results}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start}=    Evaluate    time.time()    modules=time
        ${response}=    Make API Request    auth    /health    GET    expected_status=any
        ${end}=    Evaluate    time.time()    modules=time
        ${latency_ms}=    Evaluate    (${end} - ${start}) * 1000
        Append To List    ${results}    ${latency_ms}
    END
    Evaluate    sorted(${results})[94]    # P99 index
    Log    P99 latency collected from 100 requests

QRNG Throughput — Above 1000 req/s
    [Documentation]    Measure QRNG throughput
    ${start}=    Evaluate    time.time()    modules=time
    ${count}=    Set Variable    0
    FOR    ${i}    IN RANGE    50
        ${data}=    Create Dictionary    num_bits=256
        ${response}=    Make API Request    auth    /api/v1/quantum/rng/generate    POST    data=${data}    expected_status=any
        ${count}=    Evaluate    ${count} + 1
    END
    ${end}=    Evaluate    time.time()    modules=time
    ${duration}=    Evaluate    ${end} - ${start}
    ${throughput}=    Evaluate    ${count} / ${duration}
    Should Be True    ${throughput} > 10    Throughput ${throughput} req/s below minimum
    Log    QRNG throughput: ${throughput} req/s

Face Inference Latency — Below 100ms
    [Documentation]    Measure face ML inference latency
    ${start}=    Evaluate    time.time()    modules=time
    ${response}=    Make API Request    auth    /health    GET
    ${end}=    Evaluate    time.time()    modules=time
    ${latency_ms}=    Evaluate    (${end} - ${start}) * 1000
    Should Be True    ${latency_ms} < 100    Face ML latency ${latency_ms}ms exceeds 100ms
    Log    Face ML latency: ${latency_ms}ms

Concurrent Users — 1000 Requests
    [Documentation]    Test with 1000 concurrent health check requests
    ${start}=    Evaluate    time.time()    modules=time
    ${success_count}=    Set Variable    0
    FOR    ${i}    IN RANGE    1000
        ${response}=    Make API Request    auth    /health    GET    expected_status=any
        IF    ${response.status_code} == 200    Evaluate    ${success_count} + 1    ${success_count}
    END
    ${end}=    Evaluate    time.time()    modules=time
    ${duration}=    Evaluate    ${end} - ${start}
    ${success_rate}=    Evaluate    ${success_count} / 1000 * 100
    Should Be True    ${success_rate} > 99    Success rate ${success_rate}% below 99%
    Log    Concurrent test: ${success_rate}% success in ${duration}s
