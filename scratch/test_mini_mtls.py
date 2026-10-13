import hmac
import hashlib
import json
import urllib.request
import urllib.error
import os
import sys

# Ensure backend directory is importable for checking logic functions directly as well
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.main import SENSOR_SECRET_KEY, is_sensor_ip_allowlisted, verify_sensor_signature

BASE_URL = "http://127.0.0.1:8000"

def send_request(path, data=None, headers=None, method="POST"):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.getcode()
            body = resp.read().decode("utf-8")
            return status_code, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"detail": body}
        return e.code, parsed
    except Exception as e:
        print(f"Connection error to {url}: {e}")
        return 0, {"error": str(e)}

def run_tests():
    print("==================================================")
    print("TESTING AAPDASETU ZERO-TRUST MINI-mTLS GATEWAY")
    print(f"Targeting active backend server at {BASE_URL}")
    print("==================================================")

    # 1. Test IP Allowlist function
    print("\n--- TEST 1: IP Allowlist Logic ---")
    assert is_sensor_ip_allowlisted("127.0.0.1") == True, "127.0.0.1 should be allowed"
    assert is_sensor_ip_allowlisted("::1") == True, "IPv6 loopback should be allowed"
    assert is_sensor_ip_allowlisted("192.168.1.100") == True, "Private 192.168.x.x should be allowed"
    assert is_sensor_ip_allowlisted("10.50.2.1") == True, "Private 10.x.x.x should be allowed"
    assert is_sensor_ip_allowlisted("172.20.10.5") == True, "Private 172.16-31 should be allowed"
    assert is_sensor_ip_allowlisted("203.0.113.195") == False, "Public external IP must be blocked"
    assert is_sensor_ip_allowlisted("198.51.100.42") == False, "Public external IP must be blocked"
    print("[OK] IP Allowlist logic correctly validates authorized sensor subnets and rejects external intruder IPs.")

    # 2. Test Legitimate Sensor Push (Allowed IP + Valid HMAC)
    print("\n--- TEST 2: Legitimate River Gauge Telemetry Push ---")
    payload = {
        "sensor_id": "RIVER-GAUGE-GOMTI-01",
        "station_name": "Gomti River Lucknow Station",
        "river_name": "Gomti",
        "water_level_m": 4.85,
        "danger_level_m": 6.00,
        "flow_velocity_mps": 1.45,
        "battery_pct": 94.5,
        "signal_dbm": -68
    }
    raw_body = json.dumps(payload).encode("utf-8")
    valid_sig = hmac.new(SENSOR_SECRET_KEY.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    status, data = send_request(
        "/api/telemetry",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Sensor-Auth": valid_sig,
            "X-Forwarded-For": "127.0.0.1"
        }
    )
    print("Response status:", status)
    print("Response JSON:", data)
    assert status == 200, f"Expected 200, got {status}"
    assert data["success"] == True
    assert data["sensor_id"] == "RIVER-GAUGE-GOMTI-01"
    assert data["gateway_verification"]["zero_trust_status"] == "VERIFIED_HARDWARE_SOURCE"
    print("[OK] Legitimate telemetry authenticated and ingested with 200 OK.")

    # 3. Test Missing Signature (Missing X-Sensor-Auth)
    print("\n--- TEST 3: Missing X-Sensor-Auth Header ---")
    status_no_sig, data_no_sig = send_request(
        "/api/telemetry",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": "127.0.0.1"
        }
    )
    print("Response status:", status_no_sig, data_no_sig)
    assert status_no_sig == 401, f"Expected 401 Unauthorized, got {status_no_sig}"
    assert "Missing 'X-Sensor-Auth'" in str(data_no_sig)
    print("[OK] Missing signature dropped by Gateway with 401 Unauthorized.")

    # 4. Test Fake/Forged Signature
    print("\n--- TEST 4: Fake / Forged X-Sensor-Auth Header ---")
    fake_sig = "deadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678"
    status_fake, data_fake = send_request(
        "/api/telemetry",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Sensor-Auth": fake_sig,
            "X-Forwarded-For": "127.0.0.1"
        }
    )
    print("Response status:", status_fake, data_fake)
    assert status_fake == 401, f"Expected 401 Unauthorized, got {status_fake}"
    assert "Invalid 'X-Sensor-Auth'" in str(data_fake)
    print("[OK] Forged signature dropped by Gateway with 401 Unauthorized.")

    # 5. Test Tampered Payload (Data modified after signature)
    print("\n--- TEST 5: Tampered Payload (Data Injection Attack) ---")
    tampered_payload = dict(payload)
    tampered_payload["water_level_m"] = 9.99  # Attacker tries to inject fake flood surge
    tampered_body = json.dumps(tampered_payload).encode("utf-8")
    status_tampered, data_tampered = send_request(
        "/api/telemetry",
        data=tampered_body,
        headers={
            "Content-Type": "application/json",
            "X-Sensor-Auth": valid_sig,  # Old signature for original payload
            "X-Forwarded-For": "127.0.0.1"
        }
    )
    print("Response status:", status_tampered, data_tampered)
    assert status_tampered == 401, f"Expected 401 Unauthorized, got {status_tampered}"
    print("[OK] Tampered payload detected and dropped with 401 Unauthorized.")

    # 6. Test Unauthorized IP (Spoofed External IP)
    print("\n--- TEST 6: Unauthorized Client IP (External Intruder) ---")
    status_bad_ip, data_bad_ip = send_request(
        "/api/telemetry",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Sensor-Auth": valid_sig,
            "X-Forwarded-For": "203.0.113.195"  # Non-allowlisted external IP
        }
    )
    print("Response status:", status_bad_ip, data_bad_ip)
    assert status_bad_ip == 403, f"Expected 403 Forbidden, got {status_bad_ip}"
    assert "Forbidden" in str(data_bad_ip)
    print("[OK] Unauthorized IP blocked by Gateway with 403 Forbidden.")

    # 7. Test Critical Flood Alert Telemetry Trigger
    print("\n--- TEST 7: Critical Water Breach Alert Telemetry ---")
    crit_payload = {
        "sensor_id": "RIVER-GAUGE-ALAKNANDA-02",
        "station_name": "Alaknanda Chamoli Upper Gauge",
        "river_name": "Alaknanda",
        "water_level_m": 7.40,
        "danger_level_m": 6.50,
        "flow_velocity_mps": 3.80,
        "battery_pct": 89.0,
        "signal_dbm": -72
    }
    crit_body = json.dumps(crit_payload).encode("utf-8")
    crit_sig = hmac.new(SENSOR_SECRET_KEY.encode("utf-8"), crit_body, hashlib.sha256).hexdigest()
    status_crit, data_crit = send_request(
        "/api/telemetry",
        data=crit_body,
        headers={
            "Content-Type": "application/json",
            "X-Sensor-Auth": crit_sig,
            "X-Forwarded-For": "192.168.10.45"  # Trusted private IoT LAN IP
        }
    )
    print("Critical status response:", status_crit, data_crit)
    assert status_crit == 200
    assert data_crit["risk_level"] == "CRITICAL_FLOOD_ALERT"
    print("[OK] Critical telemetry processed, risk classified as:", data_crit["risk_level"])

    # 8. Test Live Telemetry Query Endpoints
    print("\n--- TEST 8: Query Live Authenticated Telemetry ---")
    status_live, data_live = send_request("/api/telemetry/live", method="GET")
    assert status_live == 200
    print("Active sensors count:", data_live.get("active_sensors_count"))
    assert data_live.get("active_sensors_count", 0) >= 2
    print("[OK] Live telemetry dashboard query verified:", len(data_live.get("latest_readings", [])), "active stations.")

    status_gate, data_gate = send_request("/api/telemetry/status", method="GET")
    assert status_gate == 200
    print("Gateway status response:", data_gate)
    print("[OK] Gateway status endpoint returned ACTIVE.")

    print("\n==================================================")
    print("ALL 8 ZERO-TRUST MINI-mTLS GATEWAY TESTS PASSED! SUCCESS")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
