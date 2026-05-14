import { Router } from "express";
import { dashboardController } from "../controllers/adminController.js";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = Router();

router.use(requireAuth);
router.get("/dashboard", dashboardController);

export default router;
