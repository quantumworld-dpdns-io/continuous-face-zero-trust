"""SecurityLibrary — Robot Framework library for OWASP security testing."""
from __future__ import annotations

import re
import json
import urllib.parse


class SecurityLibrary:
    """Robot Framework library for security test operations."""

    SQL_INJECTION_PAYLOADS = [
        "' OR 1=1 --",
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "1' AND 1=CONVERT(int, (SELECT TOP 1 table_name FROM information_schema.tables)) --",
        "admin'--",
        "' OR 1=1#",
        "1; SELECT * FROM users",
    ]

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//",
        "<iframe src='javascript:alert(\"XSS\")'>",
    ]

    COMMAND_INJECTION_PAYLOADS = [
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "; ls -la /",
        "|| ping -c 10 attacker.com",
    ]

    SSRF_PAYLOADS = [
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:6379",
        "http://[::1]:6379",
        "http://0x7f000001:6379",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]

    IDOR_PAYLOADS = [
        "../admin",
        "..%2fadmin",
        "....//admin",
        "%2e%2e%2fadmin",
        "..%252fadmin",
    ]

    def get_sql_injection_payloads(self) -> list[str]:
        return self.SQL_INJECTION_PAYLOADS

    def get_xss_payloads(self) -> list[str]:
        return self.XSS_PAYLOADS

    def get_command_injection_payloads(self) -> list[str]:
        return self.COMMAND_INJECTION_PAYLOADS

    def get_ssrf_payloads(self) -> list[str]:
        return self.SSRF_PAYLOADS

    def get_idor_payloads(self) -> list[str]:
        return self.IDOR_PAYLOADS

    def check_security_headers(self, headers: dict) -> dict:
        required = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        results = {}
        for header, expected in required.items():
            actual = headers.get(header, "")
            results[header] = {
                "present": header in headers,
                "correct": actual == expected,
                "actual": actual,
                "expected": expected,
            }
        return results

    def check_no_stack_trace(self, response_body: str) -> bool:
        stack_patterns = [
            r"Traceback \(most recent call last\)",
            r"at \w+\.\w+\(",
            r"File \".*\", line \d+",
            r"Internal Server Error",
            r"stack trace",
            r"debug mode",
        ]
        for pattern in stack_patterns:
            if re.search(pattern, response_body, re.IGNORECASE):
                return False
        return True

    def check_no_sensitive_data(self, response_body: str) -> dict:
        sensitive_patterns = {
            "password": r"password[:\s]",
            "secret": r"secret[:\s]",
            "token": r"token[:\s]",
            "api_key": r"api[_-]?key[:\s]",
            "private_key": r"private[_-]?key[:\s]",
            "database_url": r"database[_-]?url[:\s]",
        }
        found = {}
        for name, pattern in sensitive_patterns.items():
            if re.search(pattern, response_body, re.IGNORECASE):
                found[name] = True
        return {"clean": len(found) == 0, "found": found}

    def validate_cors(self, headers: dict, origin: str) -> dict:
        acao = headers.get("Access-Control-Allow-Origin", "")
        acac = headers.get("Access-Control-Allow-Credentials", "")
        return {
            "origin_reflected": acao == origin,
            "wildcard": acao == "*",
            "credentials_with_wildcard": acao == "*" and acac == "true",
            "safe": acao != "*" and not (acao == origin and acac == "true"),
        }

    def validate_rate_limit(self, responses: list[dict], max_requests: int) -> dict:
        status_codes = [r.get("status_code", 200) for r in responses]
        rate_limited = any(code == 429 for code in status_codes)
        return {
            "rate_limit_triggered": rate_limited,
            "total_requests": len(responses),
            "rate_limited_at": status_codes.index(429) if rate_limited else None,
        }
