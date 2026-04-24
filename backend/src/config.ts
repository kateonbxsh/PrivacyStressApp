import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const config = {
  port: Number(process.env.PORT ?? 4000),
  nodeEnv: process.env.NODE_ENV ?? "development",
  clientOrigin: process.env.CLIENT_ORIGIN ?? "http://localhost:5173",
  sessionSecret: required("SESSION_SECRET"),
  serverKek: required("SERVER_KEK"),
  https: (process.env.HTTPS ?? "false") === "true",
  sslKeyPath: process.env.SSL_KEY_PATH ?? "",
  sslCertPath: process.env.SSL_CERT_PATH ?? ""
};
