import type { Request, Response } from "express";
import { createCheckIn, listUserCheckIns } from "../services/checkInService.js";

function errorResponse(res: Response, error: unknown): void {
  const message = error instanceof Error ? error.message : "Unexpected error";
  res.status(400).json({ error: message });
}

export async function createCheckInController(req: Request, res: Response): Promise<void> {
  try {
    if (!req.session.userId) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }
    const result = await createCheckIn(req.session.userId, req.body, req.session.recoveredVector ?? []);
    res.status(201).json(result);
  } catch (error) {
    errorResponse(res, error);
  }
}

export async function listCheckInsController(req: Request, res: Response): Promise<void> {
  try {
    if (!req.session.userId) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }
    res.json({ items: await listUserCheckIns(req.session.userId) });
  } catch (error) {
    errorResponse(res, error);
  }
}
