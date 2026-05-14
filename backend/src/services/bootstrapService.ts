import argon2 from "argon2";
import { prisma } from "../db/prisma.js";
import { generateSalt, deriveDeterministicSeed } from "./derivationService.js";
import { encryptTransformedVector } from "./encryptionService.js";
import { generateInvertibleMatrix, transformVector } from "./matrixService.js";

const demoUsers = [
  {
    email: "demo@neuromove.app",
    password: "demo12345",
    displayName: "Demo User",
    role: "user",
    vector: [0.72, 0.68, 0.56, 0.62, 0.75, 0.44, 0.5, 0.48]
  },
  {
    email: "research@neuromove.app",
    password: "research123",
    displayName: "Research Demo",
    role: "researcher",
    vector: [0.5, 0.58, 0.44, 0.48, 0.52, 0.5, 0.5, 0.5]
  },
  {
    email: "admin@neuromove.app",
    password: "admin12345",
    displayName: "Admin Demo",
    role: "admin",
    vector: [0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45]
  }
];

async function createSensitiveProfile(userId: string, password: string, vector: number[]) {
  const salt = generateSalt();
  const seed = deriveDeterministicSeed(password, salt);
  const matrixK = generateInvertibleMatrix(seed, vector.length);
  const transformedVector = transformVector(matrixK, vector);
  const encrypted = encryptTransformedVector(transformedVector);

  const profile = await prisma.sensitiveProfile.create({
    data: {
      encryptedVector: new Uint8Array(encrypted.encryptedVector),
      vectorIv: new Uint8Array(encrypted.vectorIv),
      vectorAuthTag: new Uint8Array(encrypted.vectorAuthTag),
      wrappedDek: new Uint8Array(encrypted.wrappedDek),
      wrappedDekIv: new Uint8Array(encrypted.wrappedDekIv),
      wrappedDekAuthTag: new Uint8Array(encrypted.wrappedDekAuthTag),
      salt: new Uint8Array(salt),
      vectorDimension: vector.length
    }
  });

  await prisma.userProfileLink.create({
    data: {
      userId,
      profileId: profile.id
    }
  });
}

export async function seedDemoData(): Promise<void> {
  for (const demo of demoUsers) {
    const existing = await prisma.user.findUnique({ where: { email: demo.email } });
    if (!existing) {
      const user = await prisma.user.create({
        data: {
          email: demo.email,
          passwordHash: await argon2.hash(demo.password, { type: argon2.argon2id }),
          displayName: demo.displayName,
          role: demo.role
        }
      });
      await createSensitiveProfile(user.id, demo.password, demo.vector);
    }
  }

  const nodeSeeds = [
    { name: "MEC Lyon A", region: "lyon", health: 96, modelVersion: "mec-r0" },
    { name: "MEC Grenoble B", region: "grenoble", health: 93, modelVersion: "mec-r0" },
    { name: "MEC Paris C", region: "paris", health: 91, modelVersion: "mec-r0" }
  ];

  for (const node of nodeSeeds) {
    await prisma.mecNode.upsert({
      where: { name: node.name },
      update: node,
      create: node
    });
  }
}
