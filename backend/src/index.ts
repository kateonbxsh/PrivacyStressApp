import fs from "node:fs";
import https from "node:https";
import { createApp } from "./app.js";
import { config } from "./config.js";
import { prisma } from "./db/prisma.js";

async function start() {
  const app = createApp();

  if (config.https && config.sslKeyPath && config.sslCertPath) {
    const key = fs.readFileSync(config.sslKeyPath);
    const cert = fs.readFileSync(config.sslCertPath);
    https.createServer({ key, cert }, app).listen(config.port, () => {
      process.stdout.write(`HTTPS server listening on https://localhost:${config.port}\n`);
    });
  } else {
    app.listen(config.port, () => {
      process.stdout.write(`HTTP server listening on http://localhost:${config.port}\n`);
    });
  }
}

start().catch(async (error) => {
  process.stderr.write(`Startup error: ${error instanceof Error ? error.message : String(error)}\n`);
  await prisma.$disconnect();
  process.exit(1);
});

process.on("SIGINT", async () => {
  await prisma.$disconnect();
  process.exit(0);
});

process.on("SIGTERM", async () => {
  await prisma.$disconnect();
  process.exit(0);
});
