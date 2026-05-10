import "express-session";

declare module "express-session" {
  interface SessionData {
    userId?: string;
    email?: string;
    recoveredVector?: number[];
    matrixProof?: {
      dimension: number;
      matrixKu: number[][];
      transformedVector: number[];
    };
  }
}
