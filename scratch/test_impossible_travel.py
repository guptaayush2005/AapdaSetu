import urllib.request
import urllib.error
import json
import time
import os
import sys

BASE_URL = "http://127.0.0.1:8000"

def send_request(path, data=None, headers=None, method="POST"):
    url = f"{BASE_URL}{path}"
    req_body = json.dumps(data).encode("utf-8") if isinstance(data, dict) else (data or None)
    all_headers = {"Content-Type": "application/json"}
    if headers:
        all_headers.update(headers)
    req = urllib.request.Request(url, data=req_body, headers=all_headers, method=method)
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
    print("TESTING AAPDASETU PHYSICS-BASED IMPOSSIBLE TRAVEL")
    print(f"Targeting active backend server at {BASE_URL}")
    print("==================================================")

    # 1. Test Status Endpoint
    print("\n--- TEST 1: Impossible Travel Engine Status ---")
    status_code, status_data = send_request("/api/security/impossible-travel/status", method="GET")
    print("Status response:", status_code, status_data)
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert status_data["status"] == "ACTIVE"
    assert status_data["max_plausible_speed_kmh"] == 950.0
    print("[OK] Engine is ACTIVE with maximum plausible speed limit = 950.0 km/h.")

    # 2. Test Normal Human Travel (Plausible Speed)
    print("\n--- TEST 2: Normal Plausible Human Travel (Delhi -> Lucknow) ---")
    test_token_normal = f"AS-USR-LEGIT-{int(time.time())}"
    
    # Step A: User active in New Delhi
    code_a, data_a = send_request(
        "/api/security/geo-check",
        data={"token": test_token_normal, "lat": 28.6139, "lon": 77.2090, "city": "New Delhi"}
    )
    print("Location A (Delhi):", code_a, data_a)
    assert code_a == 200
    assert data_a["result"]["status"] == "INITIALIZED"

    # Step B: User makes request from nearby location (same city or low distance)
    code_b, data_b = send_request(
        "/api/security/geo-check",
        data={"token": test_token_normal, "lat": 28.6300, "lon": 77.2200, "city": "Connaught Place, Delhi"}
    )
    print("Location B (Local movement):", code_b, data_b)
    assert code_b == 200
    assert data_b["result"]["status"] == "PASS"
    print("[OK] Normal local movement authenticated successfully without false alarms.")

    # 3. Test Impossible Travel Anomaly (Simulation Endpoint)
    print("\n--- TEST 3: Impossible Travel Attack (Delhi -> London in 5 Mins) ---")
    sim_token = f"AS-STOLEN-TOKEN-{int(time.time())}"
    code_sim, data_sim = send_request(
        "/api/security/simulate-impossible-travel",
        data={
            "token": sim_token,
            "origin_city": "delhi",
            "jump_city": "london",
            "elapsed_minutes": 5.0
        }
    )
    print("Simulation status:", code_sim)
    print("Calculated Distance (km):", data_sim.get("haversine_distance_km"))
    print("Calculated Speed (km/h):", data_sim.get("calculated_velocity_kmh"))
    print("Is Impossible Travel:", data_sim.get("is_impossible_travel"))
    print("Session Killed:", data_sim.get("session_killed"))
    assert code_sim == 200
    assert data_sim["is_impossible_travel"] == True
    assert data_sim["session_killed"] == True
    assert data_sim["calculated_velocity_kmh"] > 50000.0  # ~80,500 km/h
    print("[OK] Impossible Travel detected! Speed exceeded 80,000 km/h; session killed instantly.")

    # 4. Test Immediate Revocation / Block on Stolen Token
    print("\n--- TEST 4: Block Subsequent Request With Stolen/Killed Token ---")
    code_blocked, data_blocked = send_request(
        "/api/security/geo-check",
        data={"token": sim_token, "lat": 51.5074, "lon": -0.1278, "city": "London"}
    )
    print("Subsequent request status:", code_blocked, data_blocked)
    assert code_blocked == 401
    assert "SESSION_REVOKED_IMPOSSIBLE_TRAVEL" in str(data_blocked)
    print("[OK] Subsequent request using killed token was immediately blocked with 401.")

    # 5. Test Live Middleware on Authenticated Route With Jump
    print("\n--- TEST 5: Automatic HTTP Middleware Detection ---")
    mid_token = f"AS-USR-MID-{int(time.time())}"
    
    # First request from Delhi (registered)
    code_m1, data_m1 = send_request(
        "/api/security/geo-check",
        data={"token": mid_token, "lat": 28.6139, "lon": 77.2090, "city": "New Delhi"}
    )
    assert code_m1 == 200

    # Second request 1 second later from New York with header X-Session-Token
    code_m2, data_m2 = send_request(
        "/api/security/geo-check",
        data={"token": mid_token, "lat": 40.7128, "lon": -74.0060, "city": "New York"},
        headers={"X-Session-Token": mid_token}
    )
    print("Jump to New York status:", code_m2, data_m2)
    assert code_m2 == 401
    assert "IMPOSSIBLE_TRAVEL_DETECTED" in str(data_m2) or "revoked" in str(data_m2).lower()
    print("[OK] Sudden jump to New York detected by Engine and session revoked.")

    # 6. Test Incidents Log Endpoint
    print("\n--- TEST 6: Audit Log of Detected Incidents ---")
    code_inc, data_inc = send_request("/api/security/impossible-travel/incidents", method="GET")
    assert code_inc == 200
    print("Total recorded incidents:", data_inc.get("count"))
    assert data_inc.get("count", 0) >= 2
    first_inc = data_inc["incidents"][0]
    print("Latest incident sample:")
    print("  - Incident ID:", first_inc["incident_id"])
    print("  - Distance:", first_inc["distance_km"], "km")
    print("  - Speed:", first_inc["calculated_speed_kmh"], "km/h")
    print("  - Physics verdict:", first_inc["physics_verdict"])
    print("[OK] Audit log contains fully documented forensic incident records.")

    print("\n==================================================")
    print("ALL 6 IMPOSSIBLE TRAVEL SECURITY TESTS PASSED! SUCCESS")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
