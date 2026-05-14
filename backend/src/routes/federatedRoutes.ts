import { Router } from "express";
import {
  globalSharedModelController,
  regionalSharedModelController,
  submitFederatedUpdateController
} from "../controllers/federatedController.js";

const router = Router();

router.get("/global-model", globalSharedModelController);
router.get("/regional-model", regionalSharedModelController);
router.post("/updates", submitFederatedUpdateController);

export default router;
