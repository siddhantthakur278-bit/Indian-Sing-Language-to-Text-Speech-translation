/**
 * Normalization Module for Browser MediaPipe Inference (Contract 7.1)
 * Must produce identical numerical results to ml/preprocess.py normalize().
 * Tolerance limit: 1e-4
 */

export interface LandmarkVectorOptions {
  tolerance?: number;
}

/**
 * Normalizes a 2D array of sequence frames of shape [seqLen, 258].
 * Each frame consists of:
 * - 0:132   : Pose landmarks (33 * 4 [x, y, z, visibility])
 * - 132:195 : Left Hand landmarks (21 * 3 [x, y, z])
 * - 195:258 : Right Hand landmarks (21 * 3 [x, y, z])
 */
export function normalize(sequence: number[][]): number[][] {
  return sequence.map((frame) => {
    const normalizedFrame = [...frame];

    // Left shoulder: index 11 (values at indices 44, 45, 46)
    const lsX = frame[44];
    const lsY = frame[45];
    const lsZ = frame[46];

    // Right shoulder: index 12 (values at indices 48, 49, 50)
    const rsX = frame[48];
    const rsY = frame[49];
    const rsZ = frame[50];

    // Midpoint between shoulders
    const centerX = (lsX + rsX) / 2.0;
    const centerY = (lsY + rsY) / 2.0;
    const centerZ = (lsZ + rsZ) / 2.0;

    // Euclidean distance between shoulders (+ 1e-6)
    const dx = lsX - rsX;
    const dy = lsY - rsY;
    const dz = lsZ - rsZ;
    const scale = Math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6;

    // 1. Normalize Pose Landmarks (33 landmarks: x, y, z adjusted, visibility unmodified)
    for (let i = 0; i < 33; i++) {
      const idx = i * 4;
      normalizedFrame[idx] = (frame[idx] - centerX) / scale;
      normalizedFrame[idx + 1] = (frame[idx + 1] - centerY) / scale;
      normalizedFrame[idx + 2] = (frame[idx + 2] - centerZ) / scale;
      // frame[idx + 3] is visibility and remains unchanged
    }

    // 2. Normalize Left Hand (21 landmarks: indices 132 to 194)
    for (let i = 0; i < 21; i++) {
      const idx = 132 + i * 3;
      const hx = frame[idx];
      const hy = frame[idx + 1];
      const hz = frame[idx + 2];

      // If hand is present (non-zero)
      if (Math.abs(hx) > 1e-5 || Math.abs(hy) > 1e-5 || Math.abs(hz) > 1e-5) {
        normalizedFrame[idx] = (hx - centerX) / scale;
        normalizedFrame[idx + 1] = (hy - centerY) / scale;
        normalizedFrame[idx + 2] = (hz - centerZ) / scale;
      } else {
        normalizedFrame[idx] = 0.0;
        normalizedFrame[idx + 1] = 0.0;
        normalizedFrame[idx + 2] = 0.0;
      }
    }

    // 3. Normalize Right Hand (21 landmarks: indices 195 to 257)
    for (let i = 0; i < 21; i++) {
      const idx = 195 + i * 3;
      const hx = frame[idx];
      const hy = frame[idx + 1];
      const hz = frame[idx + 2];

      // If hand is present (non-zero)
      if (Math.abs(hx) > 1e-5 || Math.abs(hy) > 1e-5 || Math.abs(hz) > 1e-5) {
        normalizedFrame[idx] = (hx - centerX) / scale;
        normalizedFrame[idx + 1] = (hy - centerY) / scale;
        normalizedFrame[idx + 2] = (hz - centerZ) / scale;
      } else {
        normalizedFrame[idx] = 0.0;
        normalizedFrame[idx + 1] = 0.0;
        normalizedFrame[idx + 2] = 0.0;
      }
    }

    return normalizedFrame;
  });
}
