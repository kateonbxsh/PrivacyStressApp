import { Router } from "express";
import {
  signupController,
  loginController,
  meController,
  logoutController,
  storageProofController
} from "../controllers/authController.js";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = Router();

router.post("/signup", signupController);
router.post("/login", loginController);
router.get("/me", meController);
router.get("/session", requireAuth, meController);
router.post("/logout", logoutController);
router.delete("/session", requireAuth, logoutController);
router.get("/storage-proof", requireAuth, storageProofController);

export default router;
