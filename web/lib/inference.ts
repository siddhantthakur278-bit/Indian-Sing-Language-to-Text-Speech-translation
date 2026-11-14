/**
 * Real-Time Sign Language Inference State Machine & Temporal Smoothing Logic
 * Mirrors the logic from Section 11 of the Project Guide:
 * - Rolling 30-frame keypoint buffer
 * - Inference step every 3 frames
 * - 0.80 Confidence threshold
 * - 5-frame Temporal voting (>= 4 matches)
 * - 30-frame refractory cooldown (~1s)
 * - IDLE class rejection
 * - 1.5s No-hand pause detection triggering sentence conversion
 */

export interface InferenceConfig {
  threshold: number;
  cooldownFrames: number;
  votingWindow: number;
  votingConsensus: number;
  pauseThresholdMs: number;
}

export const DEFAULT_INFERENCE_CONFIG: InferenceConfig = {
  threshold: 0.80,
  cooldownFrames: 30, // ~1s at 30fps
  votingWindow: 5,
  votingConsensus: 4,
  pauseThresholdMs: 1500, // 1.5s pause signals end-of-sentence
};

export class SignSequenceBuffer {
  private buffer: number[][] = [];
  private recentPredictions: number[] = [];
  private lastAddedFrame = -999;
  private frameCount = 0;
  private lastHandTime = Date.now();
  private config: InferenceConfig;

  constructor(config: Partial<InferenceConfig> = {}) {
    this.config = { ...DEFAULT_INFERENCE_CONFIG, ...config };
  }

  public pushFrame(
    frameVector: number[],
    handsVisible: boolean,
    onSignRecognized?: (signIndex: number) => void,
    onPauseDetected?: () => void,
    predictFn?: (normalizedSeq: number[][]) => { index: number; confidence: number }
  ): void {
    this.frameCount++;
    const now = Date.now();

    if (handsVisible) {
      this.lastHandTime = now;
    } else {
      if (now - this.lastHandTime > this.config.pauseThresholdMs) {
        onPauseDetected?.();
      }
    }

    this.buffer.push(frameVector);
    if (this.buffer.length > 30) {
      this.buffer.shift();
    }

    // Run inference every 3 frames once buffer is filled
    if (this.buffer.length === 30 && this.frameCount % 3 === 0 && predictFn && handsVisible) {
      const pred = predictFn(this.buffer);

      if (pred.confidence >= this.config.threshold) {
        this.recentPredictions.push(pred.index);
      } else {
        this.recentPredictions.push(-1);
      }

      if (this.recentPredictions.length > this.config.votingWindow) {
        this.recentPredictions.shift();
      }

      // Consensus Voting
      const voteCounts = new Map<number, number>();
      for (const idx of this.recentPredictions) {
        if (idx !== -1) {
          voteCounts.set(idx, (voteCounts.get(idx) || 0) + 1);
        }
      }

      let topIndex = -1;
      let topCount = 0;
      voteCounts.forEach((count, idx) => {
        if (count > topCount) {
          topIndex = idx;
          topCount = count;
        }
      });

      // Check consensus, IDLE (index 0), and refractory cooldown
      if (
        topIndex > 0 &&
        topCount >= this.config.votingConsensus &&
        this.frameCount - this.lastAddedFrame > this.config.cooldownFrames
      ) {
        this.lastAddedFrame = this.frameCount;
        onSignRecognized?.(topIndex);
      }
    }
  }

  public reset(): void {
    this.buffer = [];
    this.recentPredictions = [];
    this.lastAddedFrame = -999;
    this.frameCount = 0;
  }
}
