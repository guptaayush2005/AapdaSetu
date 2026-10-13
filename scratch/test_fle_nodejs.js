/**
 * Test script for Node.js Field-Level Encryption in signatureMiddleware.js
 * Verifies:
 * 1. Node.js encryptField and decryptField roundtrip.
 * 2. Unencrypted fallback.
 * 3. encryptRecord and decryptRecord.
 */

const { encryptField, decryptField, encryptRecord, decryptRecord } = require('../signatureMiddleware.js');

console.log("============================================================");
console.log("RUNNING NODE.JS FIELD-LEVEL ENCRYPTION (AES-256-GCM) TESTS");
console.log("============================================================");

// Test 1: Single Field Round-trip
const phone = "+91 98765 43210";
const encryptedPhone = encryptField(phone);
console.log("\n[TEST 1] Single Field Encryption:");
console.log("Original Phone:", phone);
console.log("Encrypted:", encryptedPhone);
if (!encryptedPhone.startsWith("enc:v1:")) {
  console.error("FAIL: Encrypted phone does not start with 'enc:v1:'");
  process.exit(1);
}

const decryptedPhone = decryptField(encryptedPhone);
console.log("Decrypted Phone:", decryptedPhone);
if (decryptedPhone !== phone) {
  console.error("FAIL: Decrypted phone does not match original!");
  process.exit(1);
}
console.log("--> PASSED: Node.js AES-256-GCM round-trip successful.");

// Test 2: Unencrypted fallback
const plaintext = "legacy_unencrypted_phone";
const fallbackRes = decryptField(plaintext);
if (fallbackRes !== plaintext) {
  console.error("FAIL: Fallback did not return plaintext as-is!");
  process.exit(1);
}
console.log("\n[TEST 2] Legacy Unencrypted Fallback: PASSED (returned unchanged).");

// Test 3: Record Dictionary
const record = {
  name: "Sunita Sharma",
  email: "sunita@example.com",
  phone: "+91 98765 43211",
  location: "Rudraprayag, Uttarakhand",
  relation: "Mother"
};

const encRec = encryptRecord(record);
console.log("\n[TEST 3] Record Encryption:");
console.log("Encrypted Record:", encRec);
if (!encRec.phone.startsWith("enc:v1:") || !encRec.location.startsWith("enc:v1:")) {
  console.error("FAIL: Sensitive fields were not encrypted!");
  process.exit(1);
}
if (encRec.name !== record.name || encRec.email !== record.email) {
  console.error("FAIL: Non-sensitive fields were modified!");
  process.exit(1);
}

const decRec = decryptRecord(encRec);
console.log("Decrypted Record:", decRec);
if (decRec.phone !== record.phone || decRec.location !== record.location) {
  console.error("FAIL: Decrypted record does not match original!");
  process.exit(1);
}
console.log("--> PASSED: Record encryption & decryption works seamlessly!");

console.log("\n============================================================");
console.log("ALL NODE.JS FIELD-LEVEL ENCRYPTION TESTS PASSED!");
console.log("============================================================");
process.exit(0);
