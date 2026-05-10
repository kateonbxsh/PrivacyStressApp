import cors from "cors";
import express from "express";
import session from "express-session";
import swaggerUi from "swagger-ui-express";
import authRoutes from "./routes/authRoutes.js";
import { config } from "./config.js";
import { openApiDocument } from "./docs/openapi.js";

export function createApp() {
  const app = express();

  app.use(
    cors({
      origin: config.clientOrigin,
      credentials: true
    })
  );

  app.use(express.json({ limit: "1mb" }));

  app.use(
    session({
      secret: config.sessionSecret,
      resave: false,
      saveUninitialized: false,
      cookie: {
        httpOnly: true,
        sameSite: "lax",
        secure: config.nodeEnv === "production"
      }
    })
  );

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok" });
  });

  app.get("/api", (_req, res) => {
    res.json({
      name: "PrivacyStressApp backend",
      docs: "/api/docs",
      openapi: "/api/docs/openapi.json",
      authBase: "/api/auth"
    });
  });

  app.get("/api/docs/openapi.json", (_req, res) => {
    res.json(openApiDocument);
  });
  app.use("/api/docs", swaggerUi.serve, swaggerUi.setup(openApiDocument));

  app.use("/api/auth", authRoutes);

  return app;
}
