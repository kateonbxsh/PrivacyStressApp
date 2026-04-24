export const QUESTION_KEYS = [
  "avoidNoise",
  "avoidCrowds",
  "avoidBrightLight",
  "avoidConstruction",
  "preferSamePath",
  "preferTram",
  "preferMetro",
  "preferBus"
] as const;

export type QuestionnaireKey = (typeof QUESTION_KEYS)[number];
export type QuestionnaireAnswers = Record<QuestionnaireKey, number>;

export interface NormalizedVector {
  dimensionOrder: readonly QuestionnaireKey[];
  values: number[];
}
