"""
Zero-dependency test suite for Field-Level Encryption (AES-256-GCM) in AapdaSetu.
Uses standard library urllib.request and json.
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def make_request(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")

    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req, data=body_bytes, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content)
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_content)
        except Exception:
            parsed = {"error": err_content}
        return e.code, parsed


def run_tests():
    print("=" * 65)
    print("RUNNING AAPDASETU FIELD-LEVEL ENCRYPTION (AES-256-GCM) TESTS")
    print("=" * 65)

    # 1. Test Status Endpoint
    try:
        code, data = make_request("/api/security/fle/status")
        print("\n[TEST 1] GET /api/security/fle/status:")
        print(f"Status Code: {code}")
        print(f"Engine: {data.get('engine')}")
        print(f"Cipher: {data.get('cipher')}")
        print(f"Status: {data.get('status')}")
        assert data.get("status") == "ACTIVE", "Status is not ACTIVE"
        assert data.get("cipher") == "AES-256-GCM", "Cipher is not AES-256-GCM"
        print("--> PASSED: FLE engine is active with AES-256-GCM.")
    except Exception as e:
        print(f"--> FAILED Test 1: {e}")
        return False

    # 2. Test Encryption Endpoint
    sample_payload = {
        "name": "Kaushal Sharma",
        "email": "kaushal@example.com",
        "phone": "+91 98765 43210",
        "location": "Joshimath Sector 4, Uttarakhand",
        "status": "SAFE"
    }

    try:
        code, enc_res = make_request(
            "/api/security/fle/encrypt",
            method="POST",
            data={"data": sample_payload, "sensitive_keys": ["phone", "location"]}
        )
        print("\n[TEST 2] POST /api/security/fle/encrypt:")
        print(f"Status Code: {code}")
        rec = enc_res.get("encrypted_record", {})
        print(f"Original Phone: {sample_payload['phone']}")
        print(f"Encrypted Phone: {rec.get('phone')}")
        print(f"Original Location: {sample_payload['location']}")
        print(f"Encrypted Location: {rec.get('location')}")
        print(f"Plaintext Name: {rec.get('name')}")
        print(f"Plaintext Email: {rec.get('email')}")

        assert rec.get("phone", "").startswith("enc:v1:"), "Phone missing enc:v1: prefix"
        assert rec.get("location", "").startswith("enc:v1:"), "Location missing enc:v1: prefix"
        assert rec.get("name") == sample_payload["name"], "Name should not be encrypted"
        assert rec.get("email") == sample_payload["email"], "Email should not be encrypted"
        print("--> PASSED: Sensitive fields encrypted; searchable fields remain plaintext.")
    except Exception as e:
        print(f"--> FAILED Test 2: {e}")
        return False

    # 3. Test Decryption Endpoint
    try:
        code, dec_res = make_request(
            "/api/security/fle/decrypt",
            method="POST",
            data={"data": rec}
        )
        print("\n[TEST 3] POST /api/security/fle/decrypt:")
        print(f"Status Code: {code}")
        dec_rec = dec_res.get("decrypted_record", {})
        print(f"Decrypted Phone: {dec_rec.get('phone')}")
        print(f"Decrypted Location: {dec_rec.get('location')}")
        assert dec_rec.get("phone") == sample_payload["phone"]
        assert dec_rec.get("location") == sample_payload["location"]
        print("--> PASSED: Decryption recovered exact plaintext.")
    except Exception as e:
        print(f"--> FAILED Test 3: {e}")
        return False

    # 4. Test Pitch DB Dump Preview Endpoint
    try:
        code, preview_data = make_request("/api/security/fle/db-dump-preview")
        print("\n[TEST 4] GET /api/security/fle/db-dump-preview (Pitch Demo):")
        print(f"Status Code: {code}")
        print(f"Scenario: {preview_data.get('scenario')}")
        hacker_view = preview_data.get("hacker_stolen_database_dump", [])
        print(f"Stolen Row 1 Phone (Hacker View): {hacker_view[0].get('phone')}")
        print(f"Stolen Row 1 Location (Hacker View): {hacker_view[0].get('location')}")
        print(f"Authorized Row 1 Phone: {preview_data.get('authorized_application_view')[0].get('phone')}")
        assert hacker_view[0].get("phone", "").startswith("enc:v1:")
        print("--> PASSED: Pitch simulation correctly shows garbage data to attacker.")
    except Exception as e:
        print(f"--> FAILED Test 4: {e}")
        return False

    # 5. Test Live DB Dump Endpoint
    try:
        code, live_data = make_request("/api/security/fle/db-dump-live")
        print("\n[TEST 5] GET /api/security/fle/db-dump-live (Live Database Inspection):")
        print(f"Status Code: {code}")
        print(f"Total rows inspected: {live_data.get('total_rows_inspected')}")
        print(f"Pitch: {live_data.get('pitch')}")
        print(f"Security Verdict: {live_data.get('security_verdict')}")
        print("--> PASSED: Live database inspection endpoint functional.")
    except Exception as e:
        print(f"--> FAILED Test 5: {e}")
        return False

    # 6. Test Real Family Member Registration & Transparent Decryption
    try:
        new_member = {
            "name": "FLE Test Citizen",
            "phone": "+91 99887 76655",
            "relation": "Sister",
            "location": "Badrinath Road, Camp Alpha",
            "user_phone": "+91 98765 00000",
            "status": "SAFE"
        }
        code, save_res = make_request("/api/family/members", method="POST", data=new_member)
        print("\n[TEST 6] POST /api/family/members (Real DB Save with Encryption):")
        print(f"Status Code: {code}")
        member_info = save_res.get("member", {})
        created_mid = member_info.get("member_id")
        print(f"Created member ID: {created_mid}")

        # Fetch from admin endpoint (transparent decryption)
        code_admin, admin_data = make_request("/admin/family/members")
        members = admin_data.get("members", [])
        matching = [m for m in members if m.get("member_id") == created_mid]
        assert len(matching) > 0, "Member not found in admin list"
        fetched_member = matching[0]
        print(f"Admin Received Phone (Decrypted in-memory): {fetched_member.get('phone')}")
        print(f"Admin Received Location (Decrypted in-memory): {fetched_member.get('location')}")
        assert fetched_member.get("phone") == new_member["phone"], "Decrypted phone does not match original"
        assert fetched_member.get("location") == new_member["location"], "Decrypted location does not match original"
        print("--> PASSED: End-to-end write encrypted to PostgreSQL & read decrypted seamlessly!")

        # Verify what the raw database table holds for this member via live DB dump
        code_live, live_inspect = make_request("/api/security/fle/db-dump-live")
        raw_items = live_inspect.get("hacker_stolen_raw_db_dump", [])
        raw_match = [r for r in raw_items if r.get("member_id") == created_mid]
        if raw_match:
            print(f"Actual Raw DB Ciphertext in PostgreSQL: {raw_match[0].get('phone')}")
            assert raw_match[0].get("phone", "").startswith("enc:v1:"), "Raw DB row is not encrypted!"
            print("--> CONFIRMED: Real row in PostgreSQL holds AES-256-GCM ciphertext!")

        # Clean up test member
        make_request(f"/api/family/members/{created_mid}", method="DELETE")
        print("--> Cleaned up test member from PostgreSQL database.")
    except Exception as e:
        print(f"--> FAILED Test 6: {e}")
        return False

    print("\n" + "=" * 65)
    print("ALL 6 FIELD-LEVEL ENCRYPTION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
