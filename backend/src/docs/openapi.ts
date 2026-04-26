import type { OpenAPIV3 } from "openapi-types";

export const openApiDocument: OpenAPIV3.Document = {
  openapi: "3.0.3",
  info: {
    title: "PrivacyStressApp Backend API",
    version: "1.0.0",
    description: "Backend API for authentication and privacy-preserving profile storage."
  },
  servers: [{ url: "http://localhost:4000" }],
  tags: [
    { name: "System", description: "Health and system routes" },
    { name: "Auth", description: "Authentication/session routes" },
    { name: "Privacy", description: "Sensitive profile proof routes" }
  ],
  paths: {
    "/api/health": {
      get: {
        tags: ["System"],
        summary: "Health check",
        responses: {
          "200": {
            description: "Service is healthy",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: { status: { type: "string", example: "ok" } },
                  required: ["status"]
                }
              }
            }
          }
        }
      }
    },
    "/api/auth/signup": {
      post: {
        tags: ["Auth"],
        summary: "Create account and protected sensitive profile",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  email: { type: "string", format: "email" },
                  password: { type: "string", minLength: 8 },
                  questionnaire: { type: "object", additionalProperties: { type: "number" } }
                },
                required: ["email", "password", "questionnaire"]
              }
            }
          }
        },
        responses: {
          "201": {
            description: "Created",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    userId: { type: "string" },
                    normalizedVector: { type: "array", items: { type: "number" } }
                  }
                }
              }
            }
          },
          "400": { description: "Validation or business error" }
        }
      }
    },
    "/api/auth/login": {
      post: {
        tags: ["Auth"],
        summary: "Authenticate and reconstruct sensitive vector",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  email: { type: "string", format: "email" },
                  password: { type: "string" }
                },
                required: ["email", "password"]
              }
            }
          }
        },
        responses: {
          "200": {
            description: "Authenticated",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    userId: { type: "string" },
                    email: { type: "string" },
                    recoveredVector: { type: "array", items: { type: "number" } },
                    matrixProof: {
                      type: "object",
                      properties: {
                        dimension: { type: "integer" },
                        matrixKu: {
                          type: "array",
                          items: { type: "array", items: { type: "number" } }
                        },
                        transformedVector: { type: "array", items: { type: "number" } }
                      }
                    }
                  }
                }
              }
            }
          },
          "400": { description: "Invalid credentials or other error" }
        }
      }
    },
    "/api/auth/me": {
      get: {
        tags: ["Auth"],
        summary: "Get authenticated session payload (legacy route)",
        responses: {
          "200": { description: "Session payload" },
          "401": { description: "Unauthorized" }
        }
      }
    },
    "/api/auth/session": {
      get: {
        tags: ["Auth"],
        summary: "Get authenticated session payload",
        responses: {
          "200": { description: "Session payload" },
          "401": { description: "Unauthorized" }
        }
      },
      delete: {
        tags: ["Auth"],
        summary: "Destroy current session",
        responses: {
          "200": { description: "Session destroyed" },
          "401": { description: "Unauthorized" }
        }
      }
    },
    "/api/auth/logout": {
      post: {
        tags: ["Auth"],
        summary: "Destroy current session (legacy route)",
        responses: {
          "200": { description: "Session destroyed" }
        }
      }
    },
    "/api/auth/storage-proof": {
      get: {
        tags: ["Privacy"],
        summary: "Get separated encrypted storage representation for current user",
        responses: {
          "200": { description: "Storage proof payload" },
          "401": { description: "Unauthorized" }
        }
      }
    },
    "/api/docs/openapi.json": {
      get: {
        tags: ["System"],
        summary: "Get raw OpenAPI document",
        responses: {
          "200": { description: "OpenAPI JSON" }
        }
      }
    },
    "/api/docs": {
      get: {
        tags: ["System"],
        summary: "Swagger UI page",
        responses: {
          "200": { description: "Swagger UI HTML" }
        }
      }
    }
  }
};
