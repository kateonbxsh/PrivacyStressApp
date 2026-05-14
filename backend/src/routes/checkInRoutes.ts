import { Router } from "express";
import { createCheckInController, listCheckInsController } from "../controllers/checkInController.js";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = Router();

router.use(requireAuth);
router.post("/", createCheckInController);
router.get("/", listCheckInsController);

export default router;
