*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
Cache Set And Get
    [Documentation]    Test cache set and get operations
    [Tags]    cache    set    get    positive
    [Timeout]    ${TIMEOUT}
    
    # Set value
    ${set_response}=    Send Request    POST    /api/v1/cache/set
    ...    body=${{"key": "test_key_001", "value": "test_value", "ttl": 300}}
    
    Should Be Equal As Strings    ${set_response}[status]    200
    Should Be True    ${set_response}[body][success]
    
    # Get value
    ${get_response}=    Send Request    POST    /api/v1/cache/get
    ...    body=${{"key": "test_key_001"}}
    
    Should Be Equal As Strings    ${get_response}[status]    200
    Should Be True    ${get_response}[body][found]
    Should Be Equal As Strings    ${get_response}[body][value]    test_value

Cache Delete
    [Documentation]    Test cache delete operation
    [Tags]    cache    delete    positive
    [Timeout]    ${TIMEOUT}
    
    # Set value
    ${set_response}=    Send Request    POST    /api/v1/cache/set
    ...    body=${{"key": "test_key_delete", "value": "test_value", "ttl": 300}}
    
    Should Be Equal As Strings    ${set_response}[status]    200
    
    # Delete value
    ${delete_response}=    Send Request    POST    /api/v1/cache/delete
    ...    body=${{"key": "test_key_delete"}}
    
    Should Be Equal As Strings    ${delete_response}[status]    200
    Should Be True    ${delete_response}[body][success]
    
    # Verify deleted
    ${get_response}=    Send Request    POST    /api/v1/cache/get
    ...    body=${{"key": "test_key_delete"}}
    
    Should Be Equal As Strings    ${get_response}[status]    200
    Should Not Be True    ${get_response}[body][found]

Cache Get Not Found
    [Documentation]    Test cache get with non-existent key
    [Tags]    cache    get    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/cache/get
    ...    body=${{"key": "nonexistent_key"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be True    ${response}[body][found]

Cache TTL
    [Documentation]    Test cache TTL expiration
    [Tags]    cache    ttl
    [Timeout]    ${TIMEOUT}
    
    # Set value with short TTL
    ${set_response}=    Send Request    POST    /api/v1/cache/set
    ...    body=${{"key": "test_key_ttl", "value": "test_value", "ttl": 5}}
    
    Should Be Equal As Strings    ${set_response}[status]    200
    
    # Get value immediately
    ${get_response}=    Send Request    POST    /api/v1/cache/get
    ...    body=${{"key": "test_key_ttl"}}
    
    Should Be Equal As Strings    ${get_response}[status]    200
    Should Be True    ${get_response}[body][found]
    
    # Wait for expiration
    Sleep    6s
    
    # Get value after expiration
    ${get_response}=    Send Request    POST    /api/v1/cache/get
    ...    body=${{"key": "test_key_ttl"}}
    
    Should Be Equal As Strings    ${get_response}[status]    200
    Should Not Be True    ${get_response}[body][found]

Cache PubSub Publish
    [Documentation]    Test cache pub/sub publish
    [Tags]    cache    pubsub    publish    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/cache/pubsub/publish
    ...    body=${{"channel": "test_channel", "message": "test_message"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Be True    ${response}[body][success]
    Should Be True    ${response}[body][subscribers] >= 0

Cache PubSub Subscribe
    [Documentation]    Test cache pub/sub subscribe
    [Tags]    cache    pubsub    subscribe    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/cache/pubsub/subscribe
    ...    body=${{"channel": "test_channel", "timeout": 5}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][messages]

Cache Multiple Operations
    [Documentation]    Test multiple cache operations
    [Tags]    cache    multiple
    [Timeout]    ${TIMEOUT}
    
    # Set multiple values
    FOR    ${i}    IN RANGE    10
        ${set_response}=    Send Request    POST    /api/v1/cache/set
        ...    body=${{"key": "test_key_${i}", "value": "test_value_${i}", "ttl": 300}}
        
        Should Be Equal As Strings    ${set_response}[status]    200
    END
    
    # Get multiple values
    FOR    ${i}    IN RANGE    10
        ${get_response}=    Send Request    POST    /api/v1/cache/get
        ...    body=${{"key": "test_key_${i}"}}
        
        Should Be Equal As Strings    ${get_response}[status]    200
        Should Be True    ${get_response}[body][found]
        Should Be Equal As Strings    ${get_response}[body][value]    test_value_${i}
    END

Cache Performance
    [Documentation]    Test cache performance
    [Tags]    cache    performance
    [Timeout]    ${TIMEOUT}
    
    # Set values and measure latency
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    100
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/cache/set
        ...    body=${{"key": "perf_key_${i}", "value": "perf_value_${i}", "ttl": 300}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 10
