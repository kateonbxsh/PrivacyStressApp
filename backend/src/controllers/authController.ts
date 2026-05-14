import type { Request, Response } from "express";
import { login, signup, getStorageProof } from "../services/authService.js";

function errorResponse(res: Response, error: unknown): void {
  const message = error instanceof Error ? error.message : "Unexpected error";
  res.status(400).json({ error: message });
}

export async function signupController(req: Request, res: Response): Promise<void> {
  try {
    const result = await signup(req.body);
    res.status(201).json(result);
  } catch (error) {
    errorResponse(res, error);
  }
}

export async function loginController(req: Request, res: Response): Promise<void> {
  try {
    const result = await login(req.body);
    req.session.userId = result.userId;
    req.session.email = result.email;
    req.session.role = result.role;
    req.session.displayName = result.displayName;
    req.session.recoveredVector = result.recoveredVector;
    req.session.matrixProof = result.matrixProof;

    res.json({
      userId: result.userId,
      email: result.email,
      displayName: result.displayName,
      role: result.role,
      recoveredVector: result.recoveredVector,
      matrixProof: result.matrixProof
    });
  } catch (error) {
    errorResponse(res, error);
  }
}

export function meController(req: Request, res: Response): void {
  if (!req.session.userId || !req.session.email) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }

  res.json({
    userId: req.session.userId,
    email: req.session.email,
    displayName: req.session.displayName ?? null,
    role: req.session.role ?? "user",
    recoveredVector: req.session.recoveredVector ?? null,
    matrixProof: req.session.matrixProof ?? null
  });
}

export function logoutController(req: Request, res: Response): void {
  req.session.destroy(() => {
    res.json({ ok: true });
  });
}

export async function storageProofController(req: Request, res: Response): Promise<void> {
  try {
    const userId = req.session.userId;
    if (!userId) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const proof = await getStorageProof(userId);
    res.json(proof);
  } catch (error) {
    errorResponse(res, error);
  }
}
