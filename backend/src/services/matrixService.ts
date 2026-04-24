import { createHash } from "node:crypto";
import { inv, matrix, multiply } from "mathjs";

class DeterministicRng {
  private counter = 0;
  private buffer = Buffer.alloc(0);
  private offset = 0;

  constructor(private readonly seed: Buffer) {}

  private refill(): void {
    const counterBytes = Buffer.alloc(4);
    counterBytes.writeUInt32BE(this.counter, 0);
    this.counter += 1;
    this.buffer = createHash("sha256").update(this.seed).update(counterBytes).digest();
    this.offset = 0;
  }

  nextFloat(): number {
    if (this.offset + 4 > this.buffer.length) {
      this.refill();
    }

    const value = this.buffer.readUInt32BE(this.offset);
    this.offset += 4;
    return value / 0xffffffff;
  }
}

export function generateInvertibleMatrix(seed: Buffer, dimension: number): number[][] {
  const rng = new DeterministicRng(seed);
  const result: number[][] = Array.from({ length: dimension }, () => Array.from({ length: dimension }, () => 0));

  for (let row = 0; row < dimension; row += 1) {
    let offDiagonalAbsSum = 0;
    for (let col = 0; col < dimension; col += 1) {
      if (row === col) continue;
      const value = (rng.nextFloat() - 0.5) * 0.5;
      result[row][col] = value;
      offDiagonalAbsSum += Math.abs(value);
    }

    // Strict diagonal dominance ensures invertibility and numerical stability.
    result[row][row] = offDiagonalAbsSum + 1;
  }

  return result;
}

export function transformVector(matrixK: number[][], vectorX: number[]): number[] {
  const y = multiply(matrix(matrixK), matrix(vectorX));
  return (y as { toArray(): number[] }).toArray();
}

export function recoverVector(matrixK: number[][], vectorY: number[]): number[] {
  const inverse = inv(matrix(matrixK));
  const x = multiply(inverse, matrix(vectorY));
  return (x as { toArray(): number[] }).toArray();
}
