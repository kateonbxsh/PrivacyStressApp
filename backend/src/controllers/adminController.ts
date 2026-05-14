import type { Request, Response } from "express";
import { getAdminDashboard } from "../services/adminService.js";

export async function dashboardController(req: Request, res: Response): Promise<void> {
  if (!req.session.userId || !["researcher", "admin"].includes(req.session.role ?? "")) {
    res.status(403).json({ error: "Forbidden" });
    return;
  }

  res.json(await getAdminDashboard());
}
