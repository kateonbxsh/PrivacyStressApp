import { Prisma } from "@prisma/client";
import { z } from "zod";
import { prisma } from "../db/prisma.js";

const DEFAULT_SHARED_WEIGHTS = [0.18, 0.22, 0.2, 0.16, 0.12, 0.14, 0.1, 0.12, -0.55];

const updateSchema = z.object({
  clientId: z.string().min(1),
  mecNodeName: z.string().default("MEC Lyon A"),
  region: z.string().default("lyon"),
  round: z.number().int().min(0).default(1),
  sampleCount: z.number().int().min(1).default(1),
  updateNorm: z.number().min(0),
  sharedWeights: z.array(z.number()).optional(),
  epsilon: z.number().min(0).optional(),
  metrics: z.record(z.unknown()).optional()
});

function asWeights(value: unknown): number[] | null {
  if (!Array.isArray(value)) return null;
  if (!value.every((item) => typeof item === "number" && Number.isFinite(item))) return null;
  return value;
}

function weightedAverage(models: Array<{ weights: number[]; sampleCount: number }>): number[] {
  if (models.length === 0) return DEFAULT_SHARED_WEIGHTS;
  const dimension = models[0].weights.length;
  const total = models.reduce((sum, model) => sum + Math.max(1, model.sampleCount), 0);
  const result = Array.from({ length: dimension }, () => 0);

  for (const model of models) {
    const weight = Math.max(1, model.sampleCount) / total;
    for (let i = 0; i < dimension; i += 1) {
      result[i] += model.weights[i] * weight;
    }
  }

  return result.map((value) => Number(value.toFixed(8)));
}

export async function getGlobalSharedModel() {
  const global = await prisma.globalModelState.upsert({
    where: { id: "global" },
    update: {},
    create: {
      id: "global",
      version: "global-v0",
      sharedWeights: DEFAULT_SHARED_WEIGHTS,
      sampleCount: 0
    }
  });

  return {
    scope: "cloud",
    version: global.version,
    sharedWeights: asWeights(global.sharedWeights) ?? DEFAULT_SHARED_WEIGHTS,
    sampleCount: global.sampleCount
  };
}

export async function getRegionalSharedModel(region: string, mecNodeName = `MEC ${region}`) {
  const global = await getGlobalSharedModel();
  const node = await prisma.mecNode.upsert({
    where: { name: mecNodeName },
    update: {
      region,
      status: "online",
      lastHeartbeat: new Date()
    },
    create: {
      name: mecNodeName,
      region,
      status: "online",
      health: 95,
      modelVersion: `${region}-from-${global.version}`,
      sharedWeights: global.sharedWeights,
      sampleCount: 0
    }
  });

  return {
    scope: "mec",
    name: node.name,
    region: node.region,
    version: node.modelVersion,
    sharedWeights: asWeights(node.sharedWeights) ?? global.sharedWeights,
    sampleCount: node.sampleCount,
    initializedFrom: node.sharedWeights ? "regional" : "cloud"
  };
}

async function refreshCloudFromRegions() {
  const nodes = await prisma.mecNode.findMany({
    where: { sharedWeights: { not: Prisma.DbNull } }
  });
  const regionalModels = nodes
    .map((node) => ({
      weights: asWeights(node.sharedWeights),
      sampleCount: node.sampleCount
    }))
    .filter((model): model is { weights: number[]; sampleCount: number } => Boolean(model.weights));

  if (regionalModels.length === 0) return getGlobalSharedModel();

  const sharedWeights = weightedAverage(regionalModels);
  const sampleCount = regionalModels.reduce((sum, model) => sum + model.sampleCount, 0);
  const version = `global-r${Date.now()}`;

  const global = await prisma.globalModelState.upsert({
    where: { id: "global" },
    update: {
      version,
      sharedWeights,
      sampleCount
    },
    create: {
      id: "global",
      version,
      sharedWeights,
      sampleCount
    }
  });

  return {
    scope: "cloud",
    version: global.version,
    sharedWeights: asWeights(global.sharedWeights) ?? DEFAULT_SHARED_WEIGHTS,
    sampleCount: global.sampleCount
  };
}

export async function submitFederatedUpdate(raw: unknown, userId?: string) {
  const payload = updateSchema.parse(raw);
  const incomingWeights = payload.sharedWeights;
  const node = await prisma.mecNode.upsert({
    where: { name: payload.mecNodeName },
    update: {
      region: payload.region,
      status: "online",
      health: Math.max(75, 98 - Math.round(payload.updateNorm * 3)),
      modelVersion: `mec-r${payload.round}`,
      sharedWeights: incomingWeights ?? undefined,
      sampleCount: incomingWeights ? payload.sampleCount : undefined,
      lastHeartbeat: new Date()
    },
    create: {
      name: payload.mecNodeName,
      region: payload.region,
      status: "online",
      health: Math.max(75, 98 - Math.round(payload.updateNorm * 3)),
      modelVersion: `mec-r${payload.round}`,
      sharedWeights: incomingWeights,
      sampleCount: incomingWeights ? payload.sampleCount : 0
    }
  });

  const accepted = payload.updateNorm <= 100 && !payload.metrics?.personalComponentIncluded;
  const row = await prisma.federatedUpdate.create({
    data: {
      userId,
      mecNodeId: node.id,
      clientId: payload.clientId,
      round: payload.round,
      sampleCount: payload.sampleCount,
      updateNorm: payload.updateNorm,
      sharedWeights: incomingWeights,
      epsilon: payload.epsilon,
      metrics: payload.metrics as Prisma.InputJsonValue | undefined,
      accepted
    }
  });

  const global = incomingWeights ? await refreshCloudFromRegions() : await getGlobalSharedModel();
  const updatesInRound = await prisma.federatedUpdate.count({
    where: { round: payload.round, accepted: true }
  });

  return {
    id: row.id,
    accepted,
    mecNode: {
      name: node.name,
      region: node.region,
      modelVersion: `mec-r${payload.round}`,
      sharedWeights: incomingWeights ?? asWeights(node.sharedWeights) ?? global.sharedWeights
    },
    aggregation: {
      hierarchy: "device_shared_to_mec_to_cloud",
      rule: "personal_component_vi_never_leaves_phone",
      updatesInRound,
      globalModelVersion: global.version,
      globalSharedWeights: global.sharedWeights
    }
  };
}
