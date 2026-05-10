import { z } from "zod";
import {
  QUESTION_KEYS,
  type QuestionnaireAnswers,
  type QuestionnaireKey,
  type NormalizedVector
} from "../domain/questionnaire.js";

const questionnaireSchema = z.object(
  Object.fromEntries(QUESTION_KEYS.map((key) => [key, z.number().min(0).max(100)])) as Record<QuestionnaireKey, z.ZodNumber>
);

export function validateQuestionnaire(input: unknown): QuestionnaireAnswers {
  return questionnaireSchema.parse(input);
}

export function normalizeAnswers(answers: QuestionnaireAnswers): NormalizedVector {
  return {
    dimensionOrder: QUESTION_KEYS,
    values: QUESTION_KEYS.map((key) => answers[key] / 100)
  };
}
