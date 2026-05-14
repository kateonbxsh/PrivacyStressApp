import "express-session";

declare module "express-session" {
  interface SessionData {
    userId?: string;
    email?: string;
    role?: string;
    displayName?: string | null;
    recoveredVector?: number[];
    matrixProof?: {
      dimension: number;
      matrixKu: number[][];
      transformedVector: number[];
    };
  }
}
