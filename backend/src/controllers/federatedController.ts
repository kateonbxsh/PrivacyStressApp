import type { Request, Response } from "express";
import { getGlobalSharedModel, getRegionalSharedModel, submitFederatedUpdate } from "../services/federatedService.js";

function errorResponse(res: Response, error: unknown): void {
  const message = error instanceof Error ? error.message : "Unexpected error";
  res.status(400).json({ error: message });
}

export async function submitFederatedUpdateController(req: Request, res: Response): Promise<void> {
  try {
    const result = await submitFederatedUpdate(req.body, req.session.userId);
    res.status(202).json(result);
  } catch (error) {
    errorResponse(res, error);
  }
}

export async function globalSharedModelController(_req: Request, res: Response): Promise<void> {
  res.json(await getGlobalSharedModel());
}

export async function regionalSharedModelController(req: Request, res: Response): Promise<void> {
  const region = typeof req.query.region === "string" ? req.query.region : "local-demo";
  const mecNodeName = typeof req.query.mecNodeName === "string" ? req.query.mecNodeName : `MEC ${region}`;
  res.json(await getRegionalSharedModel(region, mecNodeName));
}
