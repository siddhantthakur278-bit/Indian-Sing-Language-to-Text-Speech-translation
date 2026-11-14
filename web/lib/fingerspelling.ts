/**
 * ISL Fingerspelling & Number Classifier
 * Powered by TensorFlow.js and trained on the Prathum Arikeri ISL Character Dataset (41,930 samples).
 * Recognizes A-Z and 1-9 handshapes from normalized dual-hand MediaPipe keypoints.
 */

import * as tf from "@tensorflow/tfjs";
import { HolisticResults } from "./landmarks";

export interface FingerspellingPrediction {
  char: string;
  confidence: number;
  isIdle: boolean;
}

export class FingerspellingClassifier {
  private model: tf.LayersModel | null = null;
  private classes: string[] = [];
  private isLoading = false;
  private isReady = false;

  // Smoothing & Stability Buffer
  private recentChars: string[] = [];
  private lastChar: string | null = null;
  private charHoldCount = 0;

  /**
   * Initialize and load the TensorFlow.js model in the browser
   */
  public async load(): Promise<boolean> {
    if (this.isReady) return true;
    if (this.isLoading) return false;
    if (typeof window === "undefined") return false;

    this.isLoading = true;
    try {
      // Load model topology & weights
      this.model = await tf.loadLayersModel("/models/model.json");

      // Load class metadata
      const res = await fetch("/models/classes.json");
      const meta = await res.json();
      this.classes = meta.classes;

      this.isReady = true;
      this.isLoading = false;
      return true;
    } catch (err) {
      console.error("Failed to load fingerspelling model:", err);
      this.isLoading = false;
      return false;
    }
  }

  public isLoaded(): boolean {
    return this.isReady;
  }

  /**
   * Normalize 21 hand landmarks relative to the wrist and scaled by middle-MCP distance.
   * Matches the exact coordinate system used in data/processed/landmark_dataset_with_orientation.csv
   */
  private normalizeHand(landmarks: Array<{ x: number; y: number; z: number }>): number[] {
    const wrist = landmarks[0];
    const mcp = landmarks[9]; // Middle MCP knuckle

    const dx = mcp.x - wrist.x;
    const dy = mcp.y - wrist.y;
    const dz = mcp.z - wrist.z;
    const scale = Math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6;

    const coords: number[] = [];
    for (let i = 0; i < 21; i++) {
      const lm = landmarks[i];
      coords.push((lm.x - wrist.x) / scale);
      coords.push((lm.y - wrist.y) / scale);
      coords.push((lm.z - wrist.z) / scale);
    }
    return coords;
  }

  /**
   * Extract 126-dimensional feature vector for both hands
   */
  public extractFeatures(results: HolisticResults): Float32Array | null {
    const hand1 = results.rightHandLandmarks || results.leftHandLandmarks;
    if (!hand1 || hand1.length < 21) {
      return null;
    }

    const hand1Coords = this.normalizeHand(hand1);

    // If both hands are present, hand2 is the secondary hand; otherwise fill 63 zeros
    let hand2Coords: number[] = new Array(63).fill(0.0);
    if (results.rightHandLandmarks && results.leftHandLandmarks && results.leftHandLandmarks.length >= 21) {
      hand2Coords = this.normalizeHand(results.leftHandLandmarks);
    }

    const fullVector = new Float32Array(126);
    fullVector.set(hand1Coords, 0);
    fullVector.set(hand2Coords, 63);

    return fullVector;
  }

  /**
   * Predict the current character/number from holistic results
   */
  public predict(results: HolisticResults): FingerspellingPrediction | null {
    if (!this.isReady || !this.model || this.classes.length === 0) {
      return null;
    }

    const features = this.extractFeatures(results);
    if (!features) {
      return { char: "IDLE", confidence: 1.0, isIdle: true };
    }

    const input = tf.tensor2d([Array.from(features)], [1, 126]);
    try {
      const prediction = this.model.predict(input) as tf.Tensor;
      const probabilities = prediction.dataSync();
      prediction.dispose();

      let maxIdx = 0;
      let maxProb = 0;
      for (let i = 0; i < probabilities.length; i++) {
        if (probabilities[i] > maxProb) {
          maxProb = probabilities[i];
          maxIdx = i;
        }
      }

      const rawChar = this.classes[maxIdx] || "IDLE";
      const isIdle = rawChar === "IDLE" || maxProb < 0.80;

      // Temporal stabilization: smooth jitter across 3 frames
      this.recentChars.push(rawChar);
      if (this.recentChars.length > 4) {
        this.recentChars.shift();
      }

      const matchingCount = this.recentChars.filter((c) => c === rawChar).length;
      const stableChar = matchingCount >= 3 ? rawChar : (this.lastChar || rawChar);

      if (stableChar === this.lastChar) {
        this.charHoldCount++;
      } else {
        this.lastChar = stableChar;
        this.charHoldCount = 1;
      }

      return {
        char: isIdle ? "IDLE" : stableChar,
        confidence: maxProb,
        isIdle,
      };
    } finally {
      input.dispose();
    }
  }

  public getHoldCount(): number {
    return this.charHoldCount;
  }

  public resetHold(): void {
    this.charHoldCount = 0;
    this.lastChar = null;
    this.recentChars = [];
  }
}

// Global Singleton Instance
export const fingerspellingClassifier = new FingerspellingClassifier();
