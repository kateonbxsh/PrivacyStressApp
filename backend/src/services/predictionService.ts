import { z } from "zod";

export const checkInSchema = z.object({
  timestamp: z.string().datetime().optional(),
  source: z.string().default("manual_checkin"),
  user_context: z.object({
    energy_level: z.number().min(1).max(5).default(3),
    breathing_state: z.string().default("normal"),
    physical_discomfort: z.number().min(0).max(4).default(0),
    speaking_difficulty: z.string().default("none"),
    need_isolation: z.string().default("no")
  }),
  environment: z.object({
    noise_level: z.number().min(1).max(4).default(1),
    light_level: z.string().default("normal"),
    crowd_density: z.string().default("low"),
    routine_disruption: z.string().default("none"),
    transition_difficulty: z.string().default("none"),
    social_load: z.string().default("low"),
    calm_space_available: z.string().default("yes")
  }),
  sensor_data: z.object({
    heart_rate: z.number().nullable().optional(),
    has_wearable: z.boolean().default(false),
    hrv: z.number().nullable().optional(),
    sleep_quality: z.number().min(1).max(5).default(3)
  }),
  mobility_context: z.object({
    transport_mode: z.string().default("walking"),
    transport_difficulty: z.string().default("none")
  }),
  observable_signs: z.object({
    pacing_agitation: z.boolean().default(false),
    increased_stimming: z.boolean().default(false),
    shutdown_signs: z.boolean().default(false)
  })
});

export type CheckInInput = z.infer<typeof checkInSchema>;

function clamp(value: number, min = 0, max = 1): number {
  return Math.max(min, Math.min(max, value));
}

function difficulty(value: string): number {
  return {
    none: 0,
    no: 0,
    light: 0.08,
    mild: 0.08,
    a_little: 0.08,
    moderate: 0.16,
    yes: 0.18,
    high: 0.26,
    very_high: 0.3,
    strong: 0.28,
    unknown: 0.05
  }[value] ?? 0;
}

function normalizedDifficulty(value: string): number {
  return Math.round((difficulty(value) / 0.3) * 4);
}

function breathing(value: string): number {
  return { normal: 0, slightly_fast: 0.1, fast: 0.18, difficult: 0.28 }[value] ?? 0;
}

function lightScore(value: string): number {
  return { soft: 1, normal: 2, bright: 3, harsh: 4 }[value] ?? 2;
}

function crowdScore(value: string): number {
  return { none: 0, low: 1, medium: 2, high: 3, very_high: 4 }[value] ?? 1;
}

export function predictStress(payload: CheckInInput, profileVector: number[] = []) {
  const user = payload.user_context;
  const environment = payload.environment;
  const sensors = payload.sensor_data;
  const mobility = payload.mobility_context;
  const signs = payload.observable_signs;

  const profileNoise = profileVector[0] ?? 0.5;
  const profileCrowd = profileVector[1] ?? 0.5;
  const profileLight = profileVector[2] ?? 0.5;
  const profileRoutine = profileVector[4] ?? 0.5;

  let score = 0.1;
  score += ({ 1: 0.28, 2: 0.2, 3: 0.1, 4: 0.03, 5: 0 }[user.energy_level] ?? 0.1);
  score += breathing(user.breathing_state);
  score += user.physical_discomfort * 0.05;
  score += difficulty(user.speaking_difficulty);
  score += difficulty(user.need_isolation);

  score += Math.max(0, environment.noise_level - 1) * (0.035 + profileNoise * 0.04);
  score += Math.max(0, lightScore(environment.light_level) - 2) * (0.025 + profileLight * 0.035);
  score += crowdScore(environment.crowd_density) * (0.025 + profileCrowd * 0.035);
  score += difficulty(environment.routine_disruption) * (0.75 + profileRoutine * 0.5);
  score += difficulty(environment.transition_difficulty);
  score += difficulty(environment.social_load);
  if (environment.calm_space_available === "no") score += 0.14;
  if (environment.calm_space_available === "unknown") score += 0.05;

  if (typeof sensors.heart_rate === "number") {
    if (sensors.heart_rate >= 110) score += 0.18;
    else if (sensors.heart_rate >= 95) score += 0.1;
    else if (sensors.heart_rate >= 85) score += 0.05;
  }

  if (typeof sensors.hrv === "number") {
    if (sensors.hrv < 20) score += 0.18;
    else if (sensors.hrv < 35) score += 0.1;
    else if (sensors.hrv < 50) score += 0.04;
  }

  if (sensors.sleep_quality <= 2) score += sensors.sleep_quality === 1 ? 0.18 : 0.1;
  else if (sensors.sleep_quality === 3) score += 0.03;

  score += difficulty(mobility.transport_difficulty);
  if (["bus", "metro", "train"].includes(mobility.transport_mode)) score += 0.03;
  if (signs.pacing_agitation) score += 0.1;
  if (signs.increased_stimming) score += 0.12;
  if (signs.shutdown_signs) score += 0.24;

  score = clamp(score);
  const stressLevel = score < 0.34 ? "calm" : score < 0.67 ? "alert" : "high";
  const recommendation = stressLevel === "high"
    ? "Move to a calm place if possible and begin a guided breathing or support routine."
    : stressLevel === "alert"
      ? "Try a short pause, reduce stimulation if possible, and check for a quieter space."
      : "You appear stable. This could be a good moment for a focused task.";
  const title = stressLevel === "high"
    ? "Your stress seems elevated"
    : stressLevel === "alert"
      ? "You may be under some pressure"
      : "You seem calm right now";

  return {
    stress_level: stressLevel,
    score: Number(score.toFixed(2)),
    confidence: Number(clamp(0.62 + score * 0.28, 0.62, 0.92).toFixed(2)),
    title,
    recommendation,
    model: "backend-contextual-v1"
  };
}

export function derivePrivacyPreservingMetrics(payload: CheckInInput, prediction: ReturnType<typeof predictStress>) {
  const dt = payload.timestamp ? new Date(payload.timestamp) : new Date();
  return {
    timestamp: dt.toISOString(),
    dayLabel: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][dt.getUTCDay()],
    hourBucket: Math.floor(dt.getUTCHours() / 2) * 2,
    source: payload.source,
    stressScore: prediction.score,
    stressLevel: prediction.stress_level,
    energyLevel: payload.user_context.energy_level,
    breathingLoad: Math.round((breathing(payload.user_context.breathing_state) / 0.28) * 4),
    physicalDiscomfort: payload.user_context.physical_discomfort,
    speakingDifficulty: normalizedDifficulty(payload.user_context.speaking_difficulty),
    needIsolation: normalizedDifficulty(payload.user_context.need_isolation),
    noiseLevel: payload.environment.noise_level,
    lightLevel: lightScore(payload.environment.light_level),
    crowdDensity: crowdScore(payload.environment.crowd_density),
    routineDisruption: normalizedDifficulty(payload.environment.routine_disruption),
    transitionDifficulty: normalizedDifficulty(payload.environment.transition_difficulty),
    socialLoad: normalizedDifficulty(payload.environment.social_load),
    calmSpaceAvailable: payload.environment.calm_space_available === "yes" ? 1 : 0,
    hasWearable: payload.sensor_data.has_wearable,
    sleepQuality: payload.sensor_data.sleep_quality,
    transportMode: payload.mobility_context.transport_mode,
    transportDifficulty: normalizedDifficulty(payload.mobility_context.transport_difficulty),
    pacingAgitation: payload.observable_signs.pacing_agitation ? 1 : 0,
    increasedStimming: payload.observable_signs.increased_stimming ? 1 : 0,
    shutdownSigns: payload.observable_signs.shutdown_signs ? 1 : 0
  };
}

export function hasSupportFlag(metrics: Record<string, unknown>, prediction: ReturnType<typeof predictStress>): boolean {
  return (
    prediction.stress_level === "high" ||
    Number(metrics.needIsolation ?? 0) >= 2 ||
    Number(metrics.calmSpaceAvailable ?? 1) === 0 ||
    Number(metrics.shutdownSigns ?? 0) === 1
  );
}
