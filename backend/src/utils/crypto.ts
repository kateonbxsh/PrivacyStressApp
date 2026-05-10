import { randomBytes, createCipheriv, createDecipheriv } from "node:crypto";

export interface AesGcmPayload {
  ciphertext: Buffer;
  iv: Buffer;
  authTag: Buffer;
}

export function aesGcmEncrypt(plaintext: Buffer, key: Buffer): AesGcmPayload {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const authTag = cipher.getAuthTag();
  return { ciphertext, iv, authTag };
}

export function aesGcmDecrypt(payload: AesGcmPayload, key: Buffer): Buffer {
  const decipher = createDecipheriv("aes-256-gcm", key, payload.iv);
  decipher.setAuthTag(payload.authTag);
  return Buffer.concat([decipher.update(payload.ciphertext), decipher.final()]);
}

export function parseKek(raw: string): Buffer {
  const isHex = /^[0-9a-fA-F]{64}$/.test(raw);
  const key = isHex ? Buffer.from(raw, "hex") : Buffer.from(raw, "base64");
  if (key.length !== 32) {
    throw new Error("SERVER_KEK must decode to exactly 32 bytes");
  }
  return key;
}
