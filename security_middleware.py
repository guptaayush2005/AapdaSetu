"""
Root-level alias for AapdaSetu Security Middleware suite.
Re-exports all security components from backend.security_middleware.
"""

from backend.security_middleware import (
    calculate_hmac_signature,
    verify_hmac_signature,
    SignatureVerificationMiddleware,
    CSP_POLICY,
    apply_security_headers,
    ContentSecurityPolicyMiddleware,
    extract_client_ip,
    is_sensor_ip_allowlisted,
    verify_sensor_signature,
    haversine_distance_km,
    check_impossible_travel,
    ImpossibleTravelMiddleware,
    REVOKED_SESSION_TOKENS,
    ACTIVE_SESSION_LOCATIONS,
    IMPOSSIBLE_TRAVEL_INCIDENTS,
    encrypt_field,
    decrypt_field,
    encrypt_record,
    decrypt_record,
    SENSITIVE_FIELD_NAMES
)

__all__ = [
    "calculate_hmac_signature",
    "verify_hmac_signature",
    "SignatureVerificationMiddleware",
    "CSP_POLICY",
    "apply_security_headers",
    "ContentSecurityPolicyMiddleware",
    "extract_client_ip",
    "is_sensor_ip_allowlisted",
    "verify_sensor_signature",
    "haversine_distance_km",
    "check_impossible_travel",
    "ImpossibleTravelMiddleware",
    "REVOKED_SESSION_TOKENS",
    "ACTIVE_SESSION_LOCATIONS",
    "IMPOSSIBLE_TRAVEL_INCIDENTS",
    "encrypt_field",
    "decrypt_field",
    "encrypt_record",
    "decrypt_record",
    "SENSITIVE_FIELD_NAMES"
]
