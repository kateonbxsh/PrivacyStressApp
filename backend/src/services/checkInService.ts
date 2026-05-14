import { prisma } from "../db/prisma.js";
import {
  checkInSchema,
  derivePrivacyPreservingMetrics,
  hasSupportFlag,
  predictStress
} from "./predictionService.js";

export async function createCheckIn(userId: string, raw: unknown, profileVector: number[] = []) {
  const payload = checkInSchema.parse(raw);
  const prediction = predictStress(payload, profileVector);
  const metrics = derivePrivacyPreservingMetrics(payload, prediction);
  const supportFlag = hasSupportFlag(metrics, prediction);

  const saved = await prisma.checkIn.create({
    data: {
      userId,
      source: payload.source,
      timestamp: new Date(metrics.timestamp as string),
      derivedMetrics: metrics,
      prediction,
      stressScore: prediction.score,
      stressLevel: prediction.stress_level,
      supportFlag
    }
  });

  return {
    id: saved.id,
    prediction,
    derivedMetrics: metrics,
    supportFlag,
    privacy: {
      stored: "derived_metrics_only",
      rawContextStored: false,
      profileVectorStoredInCheckIn: false
    }
  };
}

export async function listUserCheckIns(userId: string) {
  const rows = await prisma.checkIn.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    take: 25
  });

  return rows.map((row) => ({
    id: row.id,
    timestamp: row.timestamp.toISOString(),
    prediction: row.prediction,
    derivedMetrics: row.derivedMetrics,
    supportFlag: row.supportFlag
  }));
}
