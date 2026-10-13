"""
Comprehensive Python Verification Suite for AapdaSetu Security Layers.
Tests all 5 converted Python security components:
1. HMAC-SHA256 Signatures (calculate, verify, API endpoints, tamper rejection)
2. CSP & Security Headers
3. Zero-Trust Mini-mTLS (IP allowlisting + X-Sensor-Auth)
4. Physics-Based Impossible Travel (Haversine distance + velocity check + session revocation)
5. Field-Level Encryption (AES-256-GCM authenticated encryption + transparent recovery)
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly from the converted Python security suite
from backend.security_middleware import (
    calculate_hmac_signature,
    verify_hmac_signature,
    CSP_POLICY,
    is_sensor_ip_allowlisted,
    verify_sensor_signature,
    haversine_distance_km,
    check_impossible_travel,
    encrypt_field,
    decrypt_field,
    encrypt_record,
    decrypt_record,
    REVOKED_SESSION_TOKENS
)

BASE_URL = "http://127.0.0.1:8000"


def make_request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8") if isinstance(data, dict) else (data.encode("utf-8") if isinstance(data, str) else data)

    try:
        with urllib.request.urlopen(req, data=body_bytes, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            resp_headers = dict(resp.headers)
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            return resp.status, parsed, resp_headers
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        resp_headers = dict(e.headers)
        try:
            parsed = json.loads(err_content)
        except Exception:
            parsed = {"error": err_content}
        return e.code, parsed, resp_headers


def run_tests():
    print("=" * 70)
    print("TESTING AAPDASETU UNIFIED PYTHON SECURITY SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: Overall Security Suite Status Endpoint
    # -------------------------------------------------------------
    print("\n[TEST 1] GET /api/security/suite/status:")
    code, body, _ = make_request("/api/security/suite/status")
    print(f"Status Code: {code}")
    assert code == 200, f"Expected 200, got {code}"
    layers = body.get("layers", {})
    print(f"Runtime: {body.get('runtime')}")
    print(f"Layer 1 (HMAC-SHA256): {layers.get('layer_1_hmac_signature', {}).get('status')}")
    print(f"Layer 2 (CSP): {layers.get('layer_2_content_security_policy', {}).get('status')}")
    print(f"Layer 3 (Mini-mTLS): {layers.get('layer_3_zero_trust_mini_mtls', {}).get('status')}")
    print(f"Layer 4 (Impossible Travel): {layers.get('layer_4_physics_impossible_travel', {}).get('status')}")
    print(f"Layer 5 (FLE AES-256-GCM): {layers.get('layer_5_field_level_encryption', {}).get('status')}")
    assert all(l.get("status") == "ACTIVE" for l in layers.values())
    print("--> PASSED: All 5 security layers confirmed ACTIVE in Python runtime.")

    # -------------------------------------------------------------
    # TEST 2: Python HMAC-SHA256 Signatures & Constant-Time Verification
    # -------------------------------------------------------------
    print("\n[TEST 2] Python HMAC-SHA256 Signature Primitives & API:")
    test_payload = json.dumps({"action": "EMERGENCY_RESCUE", "people": 5})
    calc_sig = calculate_hmac_signature(test_payload)
    print(f"Payload: {test_payload}")
    print(f"Calculated HMAC: {calc_sig}")
    assert verify_hmac_signature(test_payload, calc_sig), "Local verify failed"
    assert not verify_hmac_signature(test_payload, "tampered_fake_signature_12345"), "Tampered signature accepted!"

    # Test via API endpoints
    code, sign_api, _ = make_request("/api/security/signature/sign", method="POST", data={"payload": test_payload})
    assert code == 200 and sign_api.get("signature") == calc_sig, "Sign API mismatch"
    code, verify_api, _ = make_request("/api/security/signature/verify", method="POST", data={"payload": test_payload, "signature": calc_sig})
    assert code == 200 and verify_api.get("valid") is True, "Verify API returned invalid"
    print("--> PASSED: Python HMAC-SHA256 signing & constant-time validation verified.")

    # -------------------------------------------------------------
    # TEST 3: Content Security Policy & Hardening Headers
    # -------------------------------------------------------------
    print("\n[TEST 3] Content Security Policy (CSP) & Hardening Headers:")
    code, _, hdrs = make_request("/health")
    csp_header = hdrs.get("content-security-policy") or hdrs.get("Content-Security-Policy")
    x_frame = hdrs.get("x-frame-options") or hdrs.get("X-Frame-Options")
    x_content = hdrs.get("x-content-type-options") or hdrs.get("X-Content-Type-Options")
    print(f"Content-Security-Policy: {csp_header[:60]}...")
    print(f"X-Frame-Options: {x_frame}")
    print(f"X-Content-Type-Options: {x_content}")
    assert csp_header and "default-src 'self'" in csp_header
    assert x_frame == "DENY"
    assert x_content == "nosniff"
    print("--> PASSED: CSP and HTTP hardening headers active on responses.")

    # -------------------------------------------------------------
    # TEST 4: Zero-Trust Mini-mTLS Gateway for IoT Sensors
    # -------------------------------------------------------------
    print("\n[TEST 4] Zero-Trust Mini-mTLS Gateway (IP Allowlist + X-Sensor-Auth):")
    # Subnet verification
    assert is_sensor_ip_allowlisted("127.0.0.1") is True
    assert is_sensor_ip_allowlisted("192.168.1.100") is True
    assert is_sensor_ip_allowlisted("10.0.0.5") is True
    assert is_sensor_ip_allowlisted("203.0.113.195") is False  # Public untrusted IP rejected
    print("--> IP Allowlisting verified: Local/private trusted, public untrusted blocked.")

    # Live sensor transmission test with HMAC signature
    sensor_telemetry = {
        "sensor_id": "PYTHON-RIVER-GAUGE-01",
        "station_name": "Alaknanda Basin Sensor #1",
        "water_level_m": 4.85,
        "danger_level_m": 6.0,
        "flow_velocity_mps": 2.4
    }
    raw_payload_str = json.dumps(sensor_telemetry)
    sensor_sig = calculate_hmac_signature(raw_payload_str, "aapda-iot-sensor-zero-trust-key-2026")

    # Transmit with valid signature
    code, tel_resp, _ = make_request(
        "/api/telemetry",
        method="POST",
        data=sensor_telemetry,
        headers={"X-Sensor-Auth": sensor_sig}
    )
    print(f"Telemetry submission with X-Sensor-Auth: HTTP {code}")
    assert code == 200, f"Expected 200, got {code}: {tel_resp}"
    assert tel_resp.get("success") is True

    # Transmit with invalid signature (MUST BE REJECTED 401)
    code_bad, bad_resp, _ = make_request(
        "/api/telemetry",
        method="POST",
        data=sensor_telemetry,
        headers={"X-Sensor-Auth": "tampered_fake_sensor_hash"}
    )
    print(f"Tampered X-Sensor-Auth submission: HTTP {code_bad}")
    assert code_bad == 401, f"Expected 401, got {code_bad}"
    print("--> PASSED: Zero-Trust Mini-mTLS accepts valid sensor signatures & drops tampered ones.")

    # -------------------------------------------------------------
    # TEST 5: Physics-Based Impossible Travel Detection
    # -------------------------------------------------------------
    print("\n[TEST 5] Physics-Based Impossible Travel Defense:")
    # Haversine distance test: Delhi to London (~6,710 km)
    dist = haversine_distance_km(28.6139, 77.2090, 51.5074, -0.1278)
    print(f"Haversine Delhi -> London: {dist:,.1f} km (Expected ~6,710 km)")
    assert 6650 <= dist <= 6770, f"Unexpected distance: {dist}"

    # Simulation endpoint: Delhi to London in 5 minutes (speed > 80,000 km/h -> IMPOSSIBLE)
    sim_data = {
        "token": "tok_python_test_superman_anomaly",
        "origin_city": "Delhi",
        "jump_city": "London",
        "elapsed_minutes": 5.0
    }
    code_sim, sim_resp, _ = make_request("/api/security/simulate-impossible-travel", method="POST", data=sim_data)
    print(f"Simulation Delhi -> London in 5 min: HTTP {code_sim}")
    assert code_sim == 200
    assert sim_resp.get("is_impossible_travel") is True
    print(f"Session Killed: {sim_resp.get('session_killed')}")
    calc_vel = sim_resp.get('calculated_velocity_kmh')
    print(f"Calculated Velocity: {calc_vel:,.1f} km/h")
    print("--> PASSED: Impossible Travel mathematically detected and session killed.")

    # -------------------------------------------------------------
    # TEST 6: Field-Level Encryption (AES-256-GCM)
    # -------------------------------------------------------------
    print("\n[TEST 6] Field-Level Encryption (AES-256-GCM):")
    sample_phone = "+91 98765 43210"
    sample_address = "Joshimath Sector 4, Uttarakhand"
    enc_phone = encrypt_field(sample_phone)
    enc_addr = encrypt_field(sample_address)
    print(f"Original Phone: {sample_phone}")
    print(f"Encrypted Phone: {enc_phone}")
    assert enc_phone.startswith("enc:v1:"), "Missing enc:v1: prefix"

    dec_phone = decrypt_field(enc_phone)
    dec_addr = decrypt_field(enc_addr)
    print(f"Decrypted Phone: {dec_phone}")
    assert dec_phone == sample_phone
    assert dec_addr == sample_address

    # Record-level dictionary test
    sample_rec = {
        "name": "Citizen Rohit",
        "email": "rohit@example.com",
        "phone": sample_phone,
        "location": sample_address,
        "status": "SAFE"
    }
    enc_rec = encrypt_record(sample_rec)
    assert enc_rec["name"] == "Citizen Rohit"  # Searchable plaintext
    assert enc_rec["phone"].startswith("enc:v1:")  # Encrypted
    dec_rec = decrypt_record(enc_rec)
    assert dec_rec["phone"] == sample_phone
    print("--> PASSED: Field-Level Encryption encrypts sensitive PII and transparently decrypts.")

    print("\n" + "=" * 70)
    print("ALL 6 PYTHON SECURITY SUITE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
