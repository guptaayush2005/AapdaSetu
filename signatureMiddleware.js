// ==============================================================================
// AAPDASETU - SIGNATURE VERIFICATION MIDDLEWARE (EXPRESS)
// Verifies HMAC-SHA256 signature in X-Signature header on incoming POST/PUT
// ==============================================================================
const crypto = require('crypto');

/**
 * Express middleware to verify HMAC-SHA256 signature on POST/PUT requests.
 * @param {string} [secret] - Shared secret key (defaults to API_SECRET env var or fallback)
 * @returns {import('express').RequestHandler}
 */
function verifySignature(secret = process.env.API_SECRET || 'aapda-setu-secure-token') {
  return (req, res, next) => {
    const method = (req.method || '').toUpperCase();

    // Only inspect mutating requests
    if (['POST', 'PUT'].includes(method)) {
      const signature = req.headers['x-signature'];
      if (!signature) {
        return res.status(401).json({
          error: 'Unauthorized: Missing X-Signature header'
        });
      }

      // Extract raw body or stringified payload
      const payload = typeof req.body === 'string'
        ? req.body
        : (req.rawBody ? req.rawBody.toString() : JSON.stringify(req.body || ''));

      // Calculate HMAC-SHA256
      const expectedSignature = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');

      // Secure constant-time comparison against timing attacks
      const sigBuffer = Buffer.from(signature);
      const expBuffer = Buffer.from(expectedSignature);

      if (sigBuffer.length !== expBuffer.length || !crypto.timingSafeEqual(sigBuffer, expBuffer)) {
        return res.status(401).json({
          error: 'Unauthorized: Invalid X-Signature header'
        });
      }
    }

    next();
  };
}

/**
 * Express middleware to attach Content Security Policy (CSP) & hardening headers.
 * @returns {import('express').RequestHandler}
 */
function contentSecurityPolicy() {
  return (req, res, next) => {
    res.setHeader(
      'Content-Security-Policy',
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-inline' https://unpkg.com; " +
      "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; " +
      "font-src 'self' https://fonts.gstatic.com data:; " +
      "img-src 'self' data: blob: https://server.arcgisonline.com https://tile.openstreetmap.de https://*.tile.openstreetmap.org https://*.openstreetmap.org https://api.qrserver.com https://worldview.earthdata.nasa.gov; " +
      "connect-src 'self' http://127.0.0.1:8000 http://localhost:8000 https://api.search.tinyfish.ai https://api.open-meteo.com https://geocoding-api.open-meteo.com https://air-quality-api.open-meteo.com https://api.web3forms.com https://formsubmit.co; " +
      "object-src 'none'; " +
      "base-uri 'self';"
    );
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    next();
  };
}

/**
 * Express middleware for Mini-mTLS Zero-Trust Gateway check for IoT sensors.
 * 1. Strict IP Allowlisting: Verifies request originates from trusted sensor subnet/IP.
 * 2. Custom Sensor Signature: Verifies HMAC-SHA256 signature in X-Sensor-Auth header.
 * 
 * @param {Object} [options]
 * @param {string} [options.sensorSecret] - Pre-shared sensor secret key
 * @param {string[]} [options.allowedIps] - List of allowed IPs or subnets
 * @returns {import('express').RequestHandler}
 */
function sensorMtlsMiddleware(options = {}) {
  const sensorSecret = options.sensorSecret || process.env.SENSOR_SECRET_KEY || 'aapda-iot-sensor-zero-trust-key-2026';
  const customIps = (process.env.ALLOWED_SENSOR_IPS || '').split(',').map(s => s.trim()).filter(Boolean);
  const defaultIps = ['127.0.0.1', '::1', '::ffff:127.0.0.1', 'localhost'];
  const allowedSet = new Set([...defaultIps, ...customIps, ...(options.allowedIps || [])]);

  return (req, res, next) => {
    // Determine Client IP
    const forwarded = req.headers['x-forwarded-for'];
    const clientIp = forwarded ? forwarded.split(',')[0].trim() : (req.socket.remoteAddress || req.ip || '127.0.0.1');

    // 1. Strict IP Allowlisting
    const isLocalOrPrivate = 
      allowedSet.has(clientIp) ||
      clientIp.startsWith('10.') ||
      clientIp.startsWith('192.168.') ||
      (/^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(clientIp));

    if (!isLocalOrPrivate) {
      return res.status(403).json({
        error: `Forbidden: IP address '${clientIp}' is not authorized to transmit IoT sensor telemetry.`,
        client_ip: clientIp,
        zero_trust_status: 'DROPPED_BY_GATEWAY'
      });
    }

    // 2. Custom Sensor Signature (X-Sensor-Auth)
    const sensorAuth = req.headers['x-sensor-auth'];
    if (!sensorAuth) {
      return res.status(401).json({
        error: "Unauthorized: Missing 'X-Sensor-Auth' signature header.",
        zero_trust_status: 'DROPPED_BY_GATEWAY'
      });
    }

    const payload = typeof req.body === 'string'
      ? req.body
      : (req.rawBody ? req.rawBody.toString() : JSON.stringify(req.body || ''));

    const expectedSignature = crypto
      .createHmac('sha256', sensorSecret)
      .update(payload)
      .digest('hex');

    const authBuffer = Buffer.from(sensorAuth.trim());
    const expectedBuffer = Buffer.from(expectedSignature);

    if (authBuffer.length !== expectedBuffer.length || !crypto.timingSafeEqual(authBuffer, expectedBuffer)) {
      return res.status(401).json({
        error: "Unauthorized: Invalid 'X-Sensor-Auth' signature. Telemetry data dropped.",
        zero_trust_status: 'DROPPED_BY_GATEWAY'
      });
    }

    // Attach verified sensor metadata to request
    req.sensorVerified = true;
    req.sensorClientIp = clientIp;
    next();
  };
}

/**
 * Calculates Great-Circle distance between coordinates using Haversine formula (km).
 */
function haversineDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371.0088;
  const toRad = (x) => (x * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 100) / 100;
}

/**
 * Express middleware for Impossible Travel Detection.
 * Tracks session tokens by (lat, lon, timestamp) and kills sessions
 * if physical velocity exceeds MAX_SPEED (default 950 km/h).
 */
function impossibleTravelMiddleware(options = {}) {
  const maxSpeedKmh = options.maxSpeedKmh || 950.0;
  const minDistanceKm = options.minDistanceKm || 50.0;
  const sessionStore = new Map();
  const revokedTokens = new Set();

  return (req, res, next) => {
    const authHeader = req.headers['authorization'] || '';
    let token = req.headers['x-session-token'] || req.headers['x-auth-token'];
    if (!token && authHeader.toLowerCase().startsWith('bearer ')) {
      token = authHeader.slice(7).trim();
    }

    if (!token) return next();

    if (revokedTokens.has(token)) {
      return res.status(401).json({
        error: 'Unauthorized: Session token permanently revoked due to Impossible Travel anomaly.',
        code: 'SESSION_REVOKED_IMPOSSIBLE_TRAVEL'
      });
    }

    const lat = parseFloat(req.headers['x-client-lat']) || 28.6139;
    const lon = parseFloat(req.headers['x-client-lon']) || 77.2090;
    const now = Date.now();

    if (sessionStore.has(token)) {
      const prev = sessionStore.get(token);
      const distanceKm = haversineDistanceKm(prev.lat, prev.lon, lat, lon);
      const deltaHours = Math.max(1, (now - prev.time) / 1000) / 3600;
      const speedKmh = distanceKm / deltaHours;

      if (distanceKm >= minDistanceKm && speedKmh > maxSpeedKmh) {
        revokedTokens.add(token);
        sessionStore.delete(token);
        return res.status(401).json({
          error: `Impossible Travel Detected: Speed ${speedKmh.toFixed(1)} km/h exceeds maximum plausible human travel limit (${maxSpeedKmh} km/h).`,
          code: 'IMPOSSIBLE_TRAVEL_DETECTED',
          distance_km: distanceKm,
          speed_kmh: speedKmh
        });
      }
    }

    sessionStore.set(token, { lat, lon, time: now });
    next();
  };
}

// ==============================================================================
// FIELD-LEVEL ENCRYPTION (FLE) ENGINE: AES-256-GCM (Node.js)
// 100% cross-compatible with Python cryptography AESGCM implementation.
// Encrypts sensitive fields (phone, address) using AES-256-GCM before DB write.
// Format: 'enc:v1:<base64(12B_iv + ciphertext + 16B_tag)>'
// ==============================================================================

const FLE_MASTER_KEY_RAW = process.env.DATABASE_ENCRYPTION_KEY || 'aapda-setu-fle-aes-256-gcm-master-key-2026';
const FLE_KEY_256 = crypto.createHash('sha256').update(FLE_MASTER_KEY_RAW).digest();
const FLE_PREFIX = 'enc:v1:';

const SENSITIVE_FIELD_NAMES = new Set([
  'phone', 'user_phone', 'location', 'address', 'pickup_location',
  'contact_phone', 'driver_phone', 'emergency_phone', 'citizen_phone'
]);

/**
 * Encrypts a plaintext string using AES-256-GCM.
 * @param {string} plaintext
 * @returns {string} Encrypted field string with 'enc:v1:' prefix
 */
function encryptField(plaintext) {
  if (plaintext === null || plaintext === undefined) return plaintext;
  const str = String(plaintext).trim();
  if (!str || str.startsWith(FLE_PREFIX)) return str;

  const iv = crypto.randomBytes(12); // 96-bit unique IV
  const cipher = crypto.createCipheriv('aes-256-gcm', FLE_KEY_256, iv);
  const encrypted = Buffer.concat([cipher.update(str, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag(); // 128-bit authentication tag

  const combined = Buffer.concat([iv, encrypted, tag]);
  return `${FLE_PREFIX}${combined.toString('base64')}`;
}

/**
 * Decrypts an AES-256-GCM encrypted field string.
 * Returns plaintext as-is if the field was not encrypted.
 * @param {string} ciphertextField
 * @returns {string} Decrypted plaintext string
 */
function decryptField(ciphertextField) {
  if (ciphertextField === null || ciphertextField === undefined) return ciphertextField;
  const str = String(ciphertextField).trim();
  if (!str.startsWith(FLE_PREFIX)) return str;

  try {
    const rawB64 = str.slice(FLE_PREFIX.length);
    const combined = Buffer.from(rawB64, 'base64');
    if (combined.length < 28) return str;

    const iv = combined.subarray(0, 12);
    const tag = combined.subarray(combined.length - 16);
    const ciphertext = combined.subarray(12, combined.length - 16);

    const decipher = crypto.createDecipheriv('aes-256-gcm', FLE_KEY_256, iv);
    decipher.setAuthTag(tag);
    const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
    return decrypted.toString('utf8');
  } catch (err) {
    return '[ENCRYPTED_PII_PROTECTED]';
  }
}

/**
 * Encrypts sensitive fields in a record dictionary before writing to DB.
 * @param {Object} record
 * @param {string[]} [customSensitiveKeys]
 * @returns {Object}
 */
function encryptRecord(record, customSensitiveKeys) {
  if (!record || typeof record !== 'object') return record;
  const keys = customSensitiveKeys ? new Set(customSensitiveKeys) : SENSITIVE_FIELD_NAMES;
  const output = { ...record };
  for (const [key, value] of Object.entries(output)) {
    if (keys.has(key) && typeof value === 'string') {
      output[key] = encryptField(value);
    }
  }
  return output;
}

/**
 * Decrypts sensitive fields in a record dictionary retrieved from DB.
 * @param {Object} record
 * @param {string[]} [customSensitiveKeys]
 * @returns {Object}
 */
function decryptRecord(record, customSensitiveKeys) {
  if (!record || typeof record !== 'object') return record;
  const keys = customSensitiveKeys ? new Set(customSensitiveKeys) : SENSITIVE_FIELD_NAMES;
  const output = { ...record };
  for (const [key, value] of Object.entries(output)) {
    if (keys.has(key) && typeof value === 'string') {
      output[key] = decryptField(value);
    }
  }
  return output;
}

module.exports = verifySignature;
module.exports.verifySignature = verifySignature;
module.exports.contentSecurityPolicy = contentSecurityPolicy;
module.exports.sensorMtlsMiddleware = sensorMtlsMiddleware;
module.exports.haversineDistanceKm = haversineDistanceKm;
module.exports.impossibleTravelMiddleware = impossibleTravelMiddleware;
module.exports.encryptField = encryptField;
module.exports.decryptField = decryptField;
module.exports.encryptRecord = encryptRecord;
module.exports.decryptRecord = decryptRecord;



