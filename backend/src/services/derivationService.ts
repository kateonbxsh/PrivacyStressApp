import { scryptSync, randomBytes } from "node:crypto";

export function generateSalt(): Buffer {
  return randomBytes(16);
}

export function deriveDeterministicSeed(password: string, salt: Buffer): Buffer {
  return scryptSync(password, salt, 32);
}
