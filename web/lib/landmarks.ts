/**
 * Landmark Vector Extraction from Browser MediaPipe Holistic results
 * Generates the standard 258-dimensional vector matching Contract 7.1.
 */

export interface HolisticResults {
  poseLandmarks?: Array<{ x: number; y: number; z: number; visibility?: number }>;
  leftHandLandmarks?: Array<{ x: number; y: number; z: number }>;
  rightHandLandmarks?: Array<{ x: number; y: number; z: number }>;
}

export function extractLandmarkVector(results: HolisticResults): number[] {
  const vector = new Array<number>(258).fill(0.0);

  // 1. Pose landmarks (33 * 4 = 132 floats)
  if (results.poseLandmarks && results.poseLandmarks.length >= 33) {
    for (let i = 0; i < 33; i++) {
      const p = results.poseLandmarks[i];
      const offset = i * 4;
      vector[offset] = p.x;
      vector[offset + 1] = p.y;
      vector[offset + 2] = p.z;
      vector[offset + 3] = p.visibility !== undefined ? p.visibility : 1.0;
    }
  }

  // 2. Left Hand landmarks (21 * 3 = 63 floats)
  if (results.leftHandLandmarks && results.leftHandLandmarks.length >= 21) {
    for (let i = 0; i < 21; i++) {
      const p = results.leftHandLandmarks[i];
      const offset = 132 + i * 3;
      vector[offset] = p.x;
      vector[offset + 1] = p.y;
      vector[offset + 2] = p.z;
    }
  }

  // 3. Right Hand landmarks (21 * 3 = 63 floats)
  if (results.rightHandLandmarks && results.rightHandLandmarks.length >= 21) {
    for (let i = 0; i < 21; i++) {
      const p = results.rightHandLandmarks[i];
      const offset = 195 + i * 3;
      vector[offset] = p.x;
      vector[offset + 1] = p.y;
      vector[offset + 2] = p.z;
    }
  }

  return vector;
}

export function areHandsDetected(results: HolisticResults): boolean {
  const hasLeft = Boolean(results.leftHandLandmarks && results.leftHandLandmarks.length > 0);
  const hasRight = Boolean(results.rightHandLandmarks && results.rightHandLandmarks.length > 0);
  return hasLeft || hasRight;
}
