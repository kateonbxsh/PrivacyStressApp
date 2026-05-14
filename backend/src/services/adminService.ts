import { prisma } from "../db/prisma.js";

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOUR_BUCKETS = [6, 8, 10, 12, 14, 16, 18, 20];

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function numberMetric(metrics: unknown, key: string): number {
  if (!metrics || typeof metrics !== "object") return 0;
  const value = (metrics as Record<string, unknown>)[key];
  return typeof value === "number" ? value : 0;
}

function stringMetric(metrics: unknown, key: string): string {
  if (!metrics || typeof metrics !== "object") return "";
  const value = (metrics as Record<string, unknown>)[key];
  return typeof value === "string" ? value : "";
}

function round(value: number, digits = 2): number {
  return Number(value.toFixed(digits));
}

export async function getAdminDashboard() {
  const [events, users, flUpdates, nodes] = await Promise.all([
    prisma.checkIn.findMany({ orderBy: { timestamp: "desc" }, take: 1000 }),
    prisma.user.count(),
    prisma.federatedUpdate.findMany({ orderBy: { createdAt: "desc" }, take: 100 }),
    prisma.mecNode.findMany({ orderBy: { name: "asc" } })
  ]);

  const stressScores = events.map((event) => event.stressScore);
  const overview = {
    active_sessions: users,
    avg_stress_score: round(mean(stressScores)),
    support_flags: events.filter((event) => event.supportFlag).length,
    last_update: events[0]?.timestamp.toISOString() ?? null
  };

  const dailyTrend = DAY_LABELS.map((day) => {
    const scores = events
      .filter((event) => stringMetric(event.derivedMetrics, "dayLabel") === day)
      .map((event) => event.stressScore);
    return { day, score: round(mean(scores)) };
  });

  const heatmapValues: number[][] = [];
  for (let dayIndex = 0; dayIndex < DAY_LABELS.length; dayIndex += 1) {
    for (let hourIndex = 0; hourIndex < HOUR_BUCKETS.length; hourIndex += 1) {
      const day = DAY_LABELS[dayIndex];
      const hour = HOUR_BUCKETS[hourIndex];
      const scores = events
        .filter((event) => stringMetric(event.derivedMetrics, "dayLabel") === day)
        .filter((event) => numberMetric(event.derivedMetrics, "hourBucket") === hour)
        .map((event) => event.stressScore);
      heatmapValues.push([hourIndex, dayIndex, Math.min(5, Math.round(mean(scores) * 5))]);
    }
  }

  const triggerWeights = new Map<string, number>();
  function addTrigger(label: string, value: number): void {
    triggerWeights.set(label, (triggerWeights.get(label) ?? 0) + value);
  }

  for (const event of events) {
    const m = event.derivedMetrics;
    addTrigger("Noise", numberMetric(m, "noiseLevel") * 1.6);
    addTrigger("Light", numberMetric(m, "lightLevel"));
    addTrigger("Crowd", numberMetric(m, "crowdDensity") * 1.5);
    addTrigger("Routine", numberMetric(m, "routineDisruption") * 1.4);
    addTrigger("Transitions", numberMetric(m, "transitionDifficulty") * 1.3);
    addTrigger("Social / Communication", (numberMetric(m, "socialLoad") + numberMetric(m, "speakingDifficulty")) * 1.2);
    addTrigger("Transit", numberMetric(m, "transportDifficulty") * 1.15);
    if (numberMetric(m, "calmSpaceAvailable") === 0) addTrigger("Quiet-space absence", 3);
    addTrigger("Fatigue / Sleep", (6 - numberMetric(m, "energyLevel") + 6 - numberMetric(m, "sleepQuality")) * 0.9);
  }

  const triggers = [...triggerWeights.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([label, value]) => ({ label, value: Math.round(value) }));

  const radar = events.length === 0
    ? { values: [0, 0, 0, 0, 0, 0] }
    : {
        values: [
          Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "noiseLevel"))) / 4 * 100),
          Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "lightLevel"))) / 4 * 100),
          Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "crowdDensity"))) / 4 * 100),
          Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "routineDisruption"))) / 4 * 100),
          Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "socialLoad") + numberMetric(e.derivedMetrics, "speakingDifficulty"))) / 8 * 100),
          Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "transportDifficulty"))) / 4 * 100)
        ]
      };

  const recommendations = [
    { label: "Quiet place", value: events.filter((e) => numberMetric(e.derivedMetrics, "calmSpaceAvailable") === 0 || numberMetric(e.derivedMetrics, "noiseLevel") >= 3).length || 1 },
    { label: "Breathing", value: events.filter((e) => e.stressLevel === "high" || numberMetric(e.derivedMetrics, "breathingLoad") >= 2).length || 1 },
    { label: "Short pause", value: events.filter((e) => numberMetric(e.derivedMetrics, "energyLevel") <= 2 || numberMetric(e.derivedMetrics, "transitionDifficulty") >= 2).length || 1 },
    { label: "Trusted contact", value: events.filter((e) => numberMetric(e.derivedMetrics, "shutdownSigns") === 1 || numberMetric(e.derivedMetrics, "socialLoad") >= 3).length || 1 }
  ];

  const recentAlerts = events
    .filter((event) => event.supportFlag)
    .slice(0, 5)
    .map((event) => ({
      time: event.timestamp.toISOString().slice(5, 16).replace("T", " "),
      level: event.stressLevel,
      title: "Support flag raised",
      details: `Noise ${numberMetric(event.derivedMetrics, "noiseLevel")} - Crowd ${numberMetric(event.derivedMetrics, "crowdDensity")} - Isolation ${numberMetric(event.derivedMetrics, "needIsolation")}`
    }));

  const latestRound = flUpdates[0]?.round ?? 0;
  return {
    overview,
    trends: {
      daily_trend: dailyTrend,
      heatmap: {
        hours: HOUR_BUCKETS.map((hour) => String(hour).padStart(2, "0")),
        days: DAY_LABELS,
        values: heatmapValues
      }
    },
    triggers,
    cohort_profile: radar,
    cohort_cards: {
      physiological_burden: round(mean(events.map((e) => numberMetric(e.derivedMetrics, "breathingLoad") + numberMetric(e.derivedMetrics, "physicalDiscomfort")))),
      sensory_load: round(mean(events.map((e) => numberMetric(e.derivedMetrics, "noiseLevel") + numberMetric(e.derivedMetrics, "lightLevel") + numberMetric(e.derivedMetrics, "crowdDensity")))),
      communication_friction: round(mean(events.map((e) => numberMetric(e.derivedMetrics, "socialLoad") + numberMetric(e.derivedMetrics, "speakingDifficulty")))),
      quiet_space_availability: Math.round(mean(events.map((e) => numberMetric(e.derivedMetrics, "calmSpaceAvailable"))) * 100)
    },
    recommendations,
    recent_alerts: recentAlerts,
    federated_status: {
      fl_round: latestRound,
      global_model_version: latestRound > 0 ? `global-r${latestRound}` : "global-v0",
      nodes: nodes.map((node) => ({
        name: node.name,
        region: node.region,
        health: node.health,
        status: node.status,
        model_version: node.modelVersion,
        last_heartbeat: node.lastHeartbeat.toISOString()
      }))
    },
    events_count: events.length,
    fl_updates_count: flUpdates.length
  };
}
