*** Settings ***
Library    Collections
Library    OperatingSystem
Library    ../resources/libraries/SecurityLibrary.py

*** Variables ***
${BASE_URL}    https://api.cfzt.io
${TIMEOUT}    300

*** Test Cases ***
Execute Simple Query
    [Documentation]    Test executing a simple analytics query
    [Tags]    analytics    query    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/query
    ...    body=${{"query": "SELECT COUNT(*) as count FROM auth_events WHERE created_at > NOW() - INTERVAL '1 day'"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][columns]
    Should Not Be Empty    ${response}[body][rows]
    Should Be True    ${response}[body][row_count] >= 0
    Should Be True    ${response}[body][execution_time_ms] > 0

Execute Query With Parameters
    [Documentation]    Test executing a query with parameters
    [Tags]    analytics    query    parameters    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/query
    ...    body=${{"query": "SELECT COUNT(*) as count FROM auth_events WHERE user_id = $1 AND created_at > $2", "parameters": [{"value": "test_user"}, {"value": "2024-01-01"}]}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][columns]
    Should Not Be Empty    ${response}[body][rows]

Execute Query Invalid SQL
    [Documentation]    Test executing invalid SQL
    [Tags]    analytics    query    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/query
    ...    body=${{"query": "SELECT * FROM nonexistent_table"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Query failed

Execute Query Missing Query
    [Documentation]    Test executing query without query field
    [Tags]    analytics    query    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/query
    ...    body=${{}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Missing query

Generate Auth Summary Report
    [Documentation]    Test generating auth summary report
    [Tags]    analytics    report    auth    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/reports
    ...    body=${{"report_type": "auth_summary", "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-31T23:59:59Z"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][report_id]
    Should Be Equal As Strings    ${response}[body][report_type]    auth_summary
    Should Not Be Empty    ${response}[body][data]

Generate User Activity Report
    [Documentation]    Test generating user activity report
    [Tags]    analytics    report    user    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/reports
    ...    body=${{"report_type": "user_activity", "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-31T23:59:59Z", "filters": {"user_id": "test_user"}}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][report_id]
    Should Be Equal As Strings    ${response}[body][report_type]    user_activity

Generate Security Events Report
    [Documentation]    Test generating security events report
    [Tags]    analytics    report    security    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/reports
    ...    body=${{"report_type": "security_events", "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-31T23:59:59Z"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][report_id]
    Should Be Equal As Strings    ${response}[body][report_type]    security_events

Generate Performance Report
    [Documentation]    Test generating performance report
    [Tags]    analytics    report    performance    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/reports
    ...    body=${{"report_type": "performance", "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-31T23:59:59Z"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][report_id]
    Should Be Equal As Strings    ${response}[body][report_type]    performance

Generate Compliance Report
    [Documentation]    Test generating compliance report
    [Tags]    analytics    report    compliance    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/reports
    ...    body=${{"report_type": "compliance", "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-31T23:59:59Z"}}
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][report_id]
    Should Be Equal As Strings    ${response}[body][report_type]    compliance

Generate Report Invalid Type
    [Documentation]    Test generating report with invalid type
    [Tags]    analytics    report    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    POST    /api/v1/analytics/reports
    ...    body=${{"report_type": "invalid_type", "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-31T23:59:59Z"}}
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Invalid report type

Get Metrics
    [Documentation]    Test getting system metrics
    [Tags]    analytics    metrics    positive
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/analytics/metrics?start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z&metrics=request_count,error_rate
    
    Should Be Equal As Strings    ${response}[status]    200
    Should Not Be Empty    ${response}[body][metrics]

Get Metrics Invalid Time
    [Documentation]    Test getting metrics with invalid time
    [Tags]    analytics    metrics    negative
    [Timeout]    ${TIMEOUT}
    
    ${response}=    Send Request    GET    /api/v1/analytics/metrics?start_time=invalid&end_time=invalid&metrics=request_count
    
    Should Be Equal As Strings    ${response}[status]    400
    Should Contain    ${response}[body][message]    Invalid time format

Analytics Query Performance
    [Documentation]    Test analytics query performance
    [Tags]    analytics    query    performance
    [Timeout]    ${TIMEOUT}
    
    @{latencies}=    Create List
    FOR    ${i}    IN RANGE    10
        ${start_time}=    Get Time    epoch
        ${response}=    Send Request    POST    /api/v1/analytics/query
        ...    body=${{"query": "SELECT COUNT(*) as count FROM auth_events"}}
        ${end_time}=    Get Time    epoch
        
        ${latency}=    Evaluate    (${end_time} - ${start_time}) * 1000
        Append To List    ${latencies}    ${latency}
    END
    
    # Check average latency
    ${avg_latency}=    Evaluate    sum(${latencies}) / len(${latencies})
    Should Be True    ${avg_latency} < 1000
