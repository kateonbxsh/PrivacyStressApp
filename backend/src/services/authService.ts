import argon2 from "argon2";
import { QUESTION_KEYS, type QuestionnaireAnswers } from "../domain/questionnaire.js";
import { prisma } from "../db/prisma.js";
import { deriveDeterministicSeed, generateSalt } from "./derivationService.js";
import { encryptTransformedVector, decryptTransformedVector } from "./encryptionService.js";
import { generateInvertibleMatrix, recoverVector, transformVector } from "./matrixService.js";
import { normalizeAnswers, validateQuestionnaire } from "./vectorService.js";

export interface SignupInput {
  email: string;
  password: string;
  questionnaire: unknown;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface AuthResult {
  userId: string;
  email: string;
  recoveredVector: number[];
  matrixProof: {
    dimension: number;
    matrixKu: number[][];
    transformedVector: number[];
  };
}

function cleanEmail(email: string): string {
  return email.trim().toLowerCase();
}

function ensurePassword(password: string): void {
  if (password.length < 8) {
    throw new Error("Password must be at least 8 characters.");
  }
}

export async function signup(input: SignupInput): Promise<{ userId: string; normalizedVector: number[] }> {
  const email = cleanEmail(input.email);
  ensurePassword(input.password);

  const answers = validateQuestionnaire(input.questionnaire);
  const normalized = normalizeAnswers(answers);

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    throw new Error("Email already registered.");
  }

  const passwordHash = await argon2.hash(input.password, { type: argon2.argon2id });
  const salt = generateSalt();
  const seed = deriveDeterministicSeed(input.password, salt);
  const matrixK = generateInvertibleMatrix(seed, normalized.values.length);
  const transformedVector = transformVector(matrixK, normalized.values);
  const encrypted = encryptTransformedVector(transformedVector);

  const created = await prisma.$transaction(async (tx) => {
    const user = await tx.user.create({
      data: {
        email,
        passwordHash
      }
    });

    const profile = await tx.sensitiveProfile.create({
      data: {
        encryptedVector: new Uint8Array(encrypted.encryptedVector),
        vectorIv: new Uint8Array(encrypted.vectorIv),
        vectorAuthTag: new Uint8Array(encrypted.vectorAuthTag),
        wrappedDek: new Uint8Array(encrypted.wrappedDek),
        wrappedDekIv: new Uint8Array(encrypted.wrappedDekIv),
        wrappedDekAuthTag: new Uint8Array(encrypted.wrappedDekAuthTag),
        salt: new Uint8Array(salt),
        vectorDimension: normalized.values.length
      }
    });

    await tx.userProfileLink.create({
      data: {
        userId: user.id,
        profileId: profile.id
      }
    });

    return user;
  });

  return {
    userId: created.id,
    normalizedVector: normalized.values
  };
}

async function findUserWithProfile(email: string) {
  return prisma.user.findUnique({
    where: { email },
    include: {
      links: {
        include: {
          profile: true
        }
      }
    }
  });
}

export async function login(input: LoginInput): Promise<AuthResult> {
  const email = cleanEmail(input.email);
  const user = await findUserWithProfile(email);

  if (!user) {
    throw new Error("Invalid credentials.");
  }

  const ok = await argon2.verify(user.passwordHash, input.password);
  if (!ok) {
    throw new Error("Invalid credentials.");
  }

  const profile = user.links[0]?.profile;
  if (!profile) {
    throw new Error("Sensitive profile not found.");
  }

  const seed = deriveDeterministicSeed(input.password, Buffer.from(profile.salt));
  const matrixK = generateInvertibleMatrix(seed, profile.vectorDimension);
  const transformed = decryptTransformedVector({
    encryptedVector: profile.encryptedVector,
    vectorIv: profile.vectorIv,
    vectorAuthTag: profile.vectorAuthTag,
    wrappedDek: profile.wrappedDek,
    wrappedDekIv: profile.wrappedDekIv,
    wrappedDekAuthTag: profile.wrappedDekAuthTag
  });

  const recoveredVector = recoverVector(matrixK, transformed);

  return {
    userId: user.id,
    email: user.email,
    recoveredVector,
    matrixProof: {
      dimension: profile.vectorDimension,
      matrixKu: matrixK,
      transformedVector: transformed
    }
  };
}

export async function getStorageProof(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      links: {
        include: {
          profile: true
        }
      }
    }
  });

  if (!user) {
    throw new Error("User not found.");
  }

  const profile = user.links[0]?.profile;
  if (!profile) {
    throw new Error("Sensitive profile not found.");
  }

  return {
    user: {
      id: user.id,
      email: user.email,
      createdAt: user.createdAt.toISOString(),
    },
    sensitiveProfile: {
      id: profile.id,
      vectorDimension: profile.vectorDimension,
      createdAt: profile.createdAt.toISOString(),
      encryptedVectorB64: Buffer.from(profile.encryptedVector).toString("base64"),
      vectorIvB64: Buffer.from(profile.vectorIv).toString("base64"),
      vectorAuthTagB64: Buffer.from(profile.vectorAuthTag).toString("base64"),
      wrappedDekB64: Buffer.from(profile.wrappedDek).toString("base64"),
      wrappedDekIvB64: Buffer.from(profile.wrappedDekIv).toString("base64"),
      wrappedDekAuthTagB64: Buffer.from(profile.wrappedDekAuthTag).toString("base64"),
      saltB64: Buffer.from(profile.salt).toString("base64")
    }
  };
}

export function parseQuestionnaire(raw: unknown): QuestionnaireAnswers {
  return validateQuestionnaire(raw);
}
