"""
==============================================================================
AAPDASETU - UNIFIED PYTHON SECURITY MIDDLEWARE & DEFENSE SUITE
Direct Python translation & enhancement of signatureMiddleware.js for FastAPI/ASGI.
Zero UI/UX dependencies.
==============================================================================

Security Layers Included:
1. HMAC-SHA256 Request Signature Verification (X-Signature Header)
2. Content Security Policy (CSP) & Hardening Headers (XSS/Clickjacking Prevention)
3. Zero-Trust Mini-mTLS Gateway for IoT Sensors (Strict IP Allowlist + X-Sensor-Auth)
4. Physics-Based Geolocation & Impossible Travel Detection (Haversine + Velocity Check)
5. Field-Level Encryption (AES-256-GCM) with Database Dump Protection
"""

import os
import math
import time
import hmac
import base64
import hashlib
import ipaddress
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set, Tuple, Union, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Cryptography for AES-256-GCM Field-Level Encryption
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ==============================================================================
# 1. HMAC-SHA256 SIGNATURE VERIFICATION (X-Signature)
# Verifies data integrity & authenticity of mutating requests (POST/PUT).
# ==============================================================================

DEFAULT_API_SECRET = os.getenv("API_SECRET", "aapda-setu-secure-token").strip()


def calculate_hmac_signature(payload: Union[str, bytes], secret: Optional[str] = None) -> str:
    """
    Calculates HMAC-SHA256 digest in hex format for a given payload.
    Compatible with client-side Web Crypto API (signature-interceptor.js).
    """
    sec = (secret or DEFAULT_API_SECRET).encode("utf-8")
    data_bytes = payload.encode("utf-8") if isinstance(payload, str) else (payload or b"")
    return hmac.new(sec, data_bytes, hashlib.sha256).hexdigest()


def verify_hmac_signature(payload: Union[str, bytes], signature: Optional[str], secret: Optional[str] = None) -> bool:
    """
    Performs constant-time verification against timing attacks.
    """
    if not signature:
        return False
    expected = calculate_hmac_signature(payload, secret)
    return hmac.compare_digest(signature.strip().lower(), expected.lower())


class SignatureVerificationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette Middleware that inspects incoming POST and PUT requests
    for the 'X-Signature' header. Rejects tampered payloads with 401 Unauthorized.
    """
    def __init__(
        self,
        app,
        secret: Optional[str] = None,
        bypass_paths: Optional[Set[str]] = None,
        enforce_strictly: bool = False
    ):
        super().__init__(app)
        self.secret = secret or DEFAULT_API_SECRET
        self.enforce_strictly = enforce_strictly
        self.bypass_paths = bypass_paths or {
            "/docs", "/redoc", "/openapi.json", "/api/telemetry", "/api/sensor/telemetry",
            "/api/security/simulate-impossible-travel", "/api/security/fle/encrypt",
            "/api/security/fle/decrypt", "/api/security/signature/sign",
            "/api/security/signature/verify", "/api/security/suite/status", "/health"
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method.upper()

        # Check if route is a mutating request and not bypassed
        path = request.url.path
        if method in ("POST", "PUT") and path not in self.bypass_paths and not path.startswith("/frontend"):
            signature = request.headers.get("x-signature") or request.headers.get("X-Signature")

            if not signature:
                if self.enforce_strictly:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": "Unauthorized: Missing X-Signature header",
                            "code": "MISSING_SIGNATURE",
                            "security_layer": "HMAC-SHA256 Signature Verification"
                        }
                    )
            else:
                body_bytes = await request.body()
                if not verify_hmac_signature(body_bytes, signature, self.secret):
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": "Unauthorized: Invalid X-Signature header. Payload hash mismatch.",
                            "code": "INVALID_SIGNATURE",
                            "security_layer": "HMAC-SHA256 Signature Verification"
                        }
                    )

        return await call_next(request)


# ==============================================================================
# 2. CONTENT SECURITY POLICY (CSP) & HTTP SECURITY HEADERS
# Mitigates XSS, Clickjacking, MIME confusion, and rogue asset injection.
# ==============================================================================

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob: https://server.arcgisonline.com https://tile.openstreetmap.de https://*.tile.openstreetmap.org https://*.openstreetmap.org https://api.qrserver.com https://worldview.earthdata.nasa.gov; "
    "connect-src 'self' http://127.0.0.1:8000 http://localhost:8000 https://api.search.tinyfish.ai https://api.open-meteo.com https://geocoding-api.open-meteo.com https://air-quality-api.open-meteo.com https://api.web3forms.com https://formsubmit.co; "
    "object-src 'none'; "
    "base-uri 'self';"
)


def apply_security_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Attaches standard security headers to a dictionary of headers."""
    headers["Content-Security-Policy"] = CSP_POLICY
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    headers["X-XSS-Protection"] = "1; mode=block"
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return headers


class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware to automatically inject CSP and hardening headers."""
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CSP_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# ==============================================================================
# 3. ZERO-TRUST SENSOR GATEWAY (MINI-mTLS - LAYER 7 CHECKS)
# Enforces Strict IP Allowlisting and Custom HMAC Hardware Signatures.
# ==============================================================================

SENSOR_SECRET_KEY = os.getenv("SENSOR_SECRET_KEY", "aapda-iot-sensor-zero-trust-key-2026").strip()

DEFAULT_ALLOWED_SENSOR_NETWORKS: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def extract_client_ip(request: Request) -> str:
    """Extracts client IP resolving proxies and load balancers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host.strip()
    return "127.0.0.1"


def is_sensor_ip_allowlisted(ip_str: str, custom_allowed: Optional[List[str]] = None) -> bool:
    """Validates if IP is inside allowlisted subnets or specific addresses."""
    if not ip_str or ip_str in ("testclient", "localhost", "127.0.0.1", "::1"):
        return True

    networks = list(DEFAULT_ALLOWED_SENSOR_NETWORKS)
    env_allowed = os.getenv("ALLOWED_SENSOR_IPS", "").strip()
    extra_items = []
    if env_allowed:
        extra_items.extend(env_allowed.split(","))
    if custom_allowed:
        extra_items.extend(custom_allowed)

    for item in extra_items:
        val = item.strip()
        if not val:
            continue
        try:
            if "/" in val:
                networks.append(ipaddress.ip_network(val, strict=False))
            else:
                networks.append(ipaddress.ip_network(f"{val}/32" if ":" not in val else f"{val}/128", strict=False))
        except ValueError:
            pass

    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in networks)
    except ValueError:
        return False


def verify_sensor_signature(raw_body: bytes, provided_sig: Optional[str], secret: Optional[str] = None) -> bool:
    """Verifies X-Sensor-Auth signature using HMAC-SHA256."""
    if not provided_sig:
        return False
    sec_bytes = (secret or SENSOR_SECRET_KEY).encode("utf-8")
    expected = hmac.new(sec_bytes, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided_sig.strip().lower(), expected.lower())


# ==============================================================================
# 4. PHYSICS-BASED IMPOSSIBLE TRAVEL DETECTION
# Uses Haversine Formula + Kinematics to revoke stolen tokens.
# ==============================================================================

EARTH_RADIUS_KM = 6371.0088
MAX_PLAUSIBLE_SPEED_KMH = 950.0  # Commercial airliner cruising velocity
MIN_ANOMALY_DISTANCE_KM = 50.0   # Ignore sub-50km small hops for speed checks

# In-memory stores for tracking & revocation
ACTIVE_SESSION_LOCATIONS: Dict[str, Dict[str, Any]] = {}
REVOKED_SESSION_TOKENS: Set[str] = set()
IMPOSSIBLE_TRAVEL_INCIDENTS: List[Dict[str, Any]] = []


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two GPS coordinates on Earth using Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)


def check_impossible_travel(
    token: str,
    current_lat: float,
    current_lon: float,
    timestamp: Optional[float] = None,
    city_hint: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Core Impossible Travel Analysis Function.
    Returns: (is_impossible, details_dict)
    """
    now = timestamp or time.time()

    # 1. Check if token was previously revoked
    if token in REVOKED_SESSION_TOKENS:
        return True, {
            "status": "REVOKED",
            "code": "SESSION_REVOKED_IMPOSSIBLE_TRAVEL",
            "error": "Access Denied: Session token permanently revoked due to Impossible Travel anomaly.",
            "token": token
        }

    # 2. Check previous location
    if token in ACTIVE_SESSION_LOCATIONS:
        prev = ACTIVE_SESSION_LOCATIONS[token]
        prev_lat = prev["lat"]
        prev_lon = prev["lon"]
        prev_time = prev["timestamp"]
        prev_city = prev.get("city", "Unknown")

        distance_km = haversine_distance_km(prev_lat, prev_lon, current_lat, current_lon)
        delta_seconds = max(1.0, now - prev_time)
        delta_hours = delta_seconds / 3600.0
        speed_kmh = round(distance_km / delta_hours, 1)

        # 3. Superman Check
        if distance_km >= MIN_ANOMALY_DISTANCE_KM and speed_kmh > MAX_PLAUSIBLE_SPEED_KMH:
            REVOKED_SESSION_TOKENS.add(token)
            ACTIVE_SESSION_LOCATIONS.pop(token, None)

            incident = {
                "id": f"INC-{int(now)}-{token[:8]}",
                "token_prefix": token[:12] + "...",
                "previous_location": {"lat": prev_lat, "lon": prev_lon, "city": prev_city},
                "current_location": {"lat": current_lat, "lon": current_lon, "city": city_hint or "Unknown"},
                "distance_km": distance_km,
                "elapsed_minutes": round(delta_seconds / 60.0, 2),
                "speed_kmh": speed_kmh,
                "max_limit_kmh": MAX_PLAUSIBLE_SPEED_KMH,
                "physics_verdict": f"Impossible Travel: {distance_km:.1f} km traversed in {delta_seconds/60.0:.1f} mins ({speed_kmh:,.1f} km/h > {MAX_PLAUSIBLE_SPEED_KMH} km/h limit)",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "action": "SESSION_TERMINATED_AND_TOKEN_REVOKED"
            }
            IMPOSSIBLE_TRAVEL_INCIDENTS.insert(0, incident)
            if len(IMPOSSIBLE_TRAVEL_INCIDENTS) > 100:
                IMPOSSIBLE_TRAVEL_INCIDENTS.pop()

            return True, {
                "status": "IMPOSSIBLE_TRAVEL_DETECTED",
                "code": "IMPOSSIBLE_TRAVEL_DETECTED",
                "error": f"Security Alarm: Impossible Travel detected! Speed: {speed_kmh:,.1f} km/h over {distance_km:,.1f} km. Session token revoked.",
                "distance_km": distance_km,
                "speed_kmh": speed_kmh,
                "incident": incident
            }

    # Store updated location
    ACTIVE_SESSION_LOCATIONS[token] = {
        "lat": current_lat,
        "lon": current_lon,
        "timestamp": now,
        "city": city_hint or "Unknown"
    }
    return False, {"status": "PLAUSIBLE_TRAVEL", "token": token}


class ImpossibleTravelMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette Middleware that detects token theft via Physics.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        token = request.headers.get("x-session-token") or request.headers.get("x-auth-token")
        auth_hdr = request.headers.get("authorization", "")
        if not token and auth_hdr.lower().startswith("bearer "):
            token = auth_hdr[7:].strip()

        if token:
            if token in REVOKED_SESSION_TOKENS:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Unauthorized: Session token permanently revoked due to Impossible Travel anomaly.",
                        "code": "SESSION_REVOKED_IMPOSSIBLE_TRAVEL",
                        "security_layer": "Physics-Based Impossible Travel Defense"
                    }
                )

            lat_hdr = request.headers.get("x-client-lat")
            lon_hdr = request.headers.get("x-client-lon")
            if lat_hdr and lon_hdr:
                try:
                    lat = float(lat_hdr)
                    lon = float(lon_hdr)
                    is_impossible, details = check_impossible_travel(token, lat, lon)
                    if is_impossible:
                        return JSONResponse(
                            status_code=401,
                            content={
                                "error": details.get("error", "Impossible Travel Detected"),
                                "code": details.get("code", "IMPOSSIBLE_TRAVEL_DETECTED"),
                                "distance_km": details.get("distance_km"),
                                "speed_kmh": details.get("speed_kmh"),
                                "security_layer": "Physics-Based Impossible Travel Defense"
                            }
                        )
                except ValueError:
                    pass

        return await call_next(request)


# ==============================================================================
# 5. FIELD-LEVEL ENCRYPTION (FLE) ENGINE: AES-256-GCM
# Protects sensitive PII (Phone numbers, exact GPS/home addresses, family contacts)
# against Database Dump compromises and Data-at-Rest leaks.
# ==============================================================================

FLE_MASTER_KEY_RAW = os.getenv("DATABASE_ENCRYPTION_KEY", "aapda-setu-fle-aes-256-gcm-master-key-2026").strip()
FLE_KEY_256 = hashlib.sha256(FLE_MASTER_KEY_RAW.encode("utf-8")).digest()
_aesgcm = AESGCM(FLE_KEY_256)

FLE_PREFIX = "enc:v1:"
SENSITIVE_FIELD_NAMES: Set[str] = {
    "phone", "user_phone", "location", "address", "pickup_location",
    "contact_phone", "driver_phone", "emergency_phone", "citizen_phone"
}


def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypts a sensitive string using AES-256-GCM.
    Returns: 'enc:v1:<base64(12-byte-nonce + ciphertext + 16-byte-tag)>'
    """
    if plaintext is None:
        return None
    s = str(plaintext).strip()
    if not s or s.startswith(FLE_PREFIX):
        return s

    nonce = os.urandom(12)  # Unique 96-bit cryptographic IV
    ciphertext = _aesgcm.encrypt(nonce, s.encode("utf-8"), None)
    encoded = base64.b64encode(nonce + ciphertext).decode("ascii")
    return f"{FLE_PREFIX}{encoded}"


def decrypt_field(ciphertext_field: Optional[str]) -> Optional[str]:
    """
    Decrypts an AES-256-GCM encrypted string.
    Gracefully returns plaintext as-is if field was not encrypted.
    """
    if ciphertext_field is None:
        return None
    s = str(ciphertext_field).strip()
    if not s.startswith(FLE_PREFIX):
        return s

    try:
        raw_b64 = s[len(FLE_PREFIX):]
        combined = base64.b64decode(raw_b64.encode("ascii"))
        if len(combined) < 28:
            return s
        nonce = combined[:12]
        ct = combined[12:]
        decrypted_bytes = _aesgcm.decrypt(nonce, ct, None)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        return "[ENCRYPTED_PII_PROTECTED]"


def encrypt_record(record: Dict[str, Any], sensitive_keys: Optional[Union[List[str], Set[str]]] = None) -> Dict[str, Any]:
    """Encrypts sensitive keys in a dictionary before storing into database."""
    target_keys = set(sensitive_keys) if sensitive_keys else SENSITIVE_FIELD_NAMES
    res = {}
    for k, v in record.items():
        if k in target_keys and isinstance(v, str):
            res[k] = encrypt_field(v)
        else:
            res[k] = v
    return res


def decrypt_record(record: Dict[str, Any], sensitive_keys: Optional[Union[List[str], Set[str]]] = None) -> Dict[str, Any]:
    """Decrypts sensitive keys in a dictionary when retrieving from database."""
    target_keys = set(sensitive_keys) if sensitive_keys else SENSITIVE_FIELD_NAMES
    res = {}
    for k, v in record.items():
        if k in target_keys and isinstance(v, str):
            res[k] = decrypt_field(v)
        else:
            res[k] = v
    return res


# Export all security primitives
__all__ = [
    # 1. HMAC Signatures
    "calculate_hmac_signature",
    "verify_hmac_signature",
    "SignatureVerificationMiddleware",
    # 2. CSP & Headers
    "CSP_POLICY",
    "apply_security_headers",
    "ContentSecurityPolicyMiddleware",
    # 3. Mini-mTLS
    "extract_client_ip",
    "is_sensor_ip_allowlisted",
    "verify_sensor_signature",
    # 4. Impossible Travel
    "haversine_distance_km",
    "check_impossible_travel",
    "ImpossibleTravelMiddleware",
    "REVOKED_SESSION_TOKENS",
    "ACTIVE_SESSION_LOCATIONS",
    "IMPOSSIBLE_TRAVEL_INCIDENTS",
    # 5. Field-Level Encryption
    "encrypt_field",
    "decrypt_field",
    "encrypt_record",
    "decrypt_record",
    "SENSITIVE_FIELD_NAMES"
]
