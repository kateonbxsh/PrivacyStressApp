import { randomBytes } from "node:crypto";
import { aesGcmDecrypt, aesGcmEncrypt, parseKek } from "../utils/crypto.js";
import { config } from "../config.js";

const kek = parseKek(config.serverKek);

export interface EncryptedVectorRecord {
  encryptedVector: Uint8Array;
  vectorIv: Uint8Array;
  vectorAuthTag: Uint8Array;
  wrappedDek: Uint8Array;
  wrappedDekIv: Uint8Array;
  wrappedDekAuthTag: Uint8Array;
}

export function encryptTransformedVector(vectorY: number[]): EncryptedVectorRecord {
  const dek = randomBytes(32);
  const vectorPayload = Buffer.from(JSON.stringify(vectorY), "utf8");
  const encryptedVector = aesGcmEncrypt(vectorPayload, dek);
  const wrappedDek = aesGcmEncrypt(dek, kek);

  return {
    encryptedVector: encryptedVector.ciphertext,
    vectorIv: encryptedVector.iv,
    vectorAuthTag: encryptedVector.authTag,
    wrappedDek: wrappedDek.ciphertext,
    wrappedDekIv: wrappedDek.iv,
    wrappedDekAuthTag: wrappedDek.authTag
  };
}

export function decryptTransformedVector(record: EncryptedVectorRecord): number[] {
  const dek = aesGcmDecrypt(
    {
      ciphertext: Buffer.from(record.wrappedDek),
      iv: Buffer.from(record.wrappedDekIv),
      authTag: Buffer.from(record.wrappedDekAuthTag)
    },
    kek
  );

  const plaintext = aesGcmDecrypt(
    {
      ciphertext: Buffer.from(record.encryptedVector),
      iv: Buffer.from(record.vectorIv),
      authTag: Buffer.from(record.vectorAuthTag)
    },
    dek
  );

  return JSON.parse(plaintext.toString("utf8")) as number[];
}
