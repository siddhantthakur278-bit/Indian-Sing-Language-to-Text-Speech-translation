/**
 * TensorFlow.js Inference Web Worker
 * Runs real neural network inference in a background thread for zero-UI-jank.
 * Loads /models/model.json and /models/classes.json (trained on 43,130 ISL samples).
 */

import * as tf from "@tensorflow/tfjs";

interface WorkerMessage {
  type: "INIT" | "PROCESS_FRAME" | "RESET";
  payload?: any;
}

interface WorkerResponse {
  type: "READY" | "PREDICTION" | "ERROR";
  data?: any;
}

const ctx: Worker = self as any;

let model: tf.LayersModel | null = null;
let classLabels: string[] = [];
let isModelLoaded = false;
let frameBuffer: number[][] = [];
const BUFFER_SIZE = 30;

ctx.onmessage = async (event: MessageEvent<WorkerMessage>) => {
  const { type, payload } = event.data;

  switch (type) {
    case "INIT":
      try {
        model = await tf.loadLayersModel("/models/model.json");
        const resp = await fetch("/models/classes.json");
        const meta = await resp.json();
        classLabels = meta.classes;
        isModelLoaded = true;
        ctx.postMessage({
          type: "READY",
          data: { totalClasses: classLabels.length, accuracy: meta.trainedAccuracy },
        } as WorkerResponse);
      } catch (err: any) {
        // Fallback gracefully if worker fetch is restricted
        isModelLoaded = false;
        ctx.postMessage({ type: "ERROR", data: err?.message || "Failed to load model" } as WorkerResponse);
      }
      break;

    case "PROCESS_FRAME":
      if (!payload) return;

      if (payload.vector) {
        frameBuffer.push(payload.vector);
        if (frameBuffer.length > BUFFER_SIZE) {
          frameBuffer.shift();
        }
      }

      // If 126 hand landmark features are provided, run real neural inference
      if (isModelLoaded && model && payload.handFeatures && payload.handFeatures.length === 126) {
        try {
          const inputTensor = tf.tensor2d([payload.handFeatures], [1, 126]);
          const prediction = model.predict(inputTensor) as tf.Tensor;
          const probabilities = await prediction.data();
          inputTensor.dispose();
          prediction.dispose();

          let maxProb = 0;
          let maxIdx = 0;
          for (let i = 0; i < probabilities.length; i++) {
            if (probabilities[i] > maxProb) {
              maxProb = probabilities[i];
              maxIdx = i;
            }
          }

          const predictedLabel = classLabels[maxIdx];

          // Contract: If top prediction is IDLE or below confidence threshold, treat as IDLE
          if (predictedLabel === "IDLE" || maxProb < 0.85) {
            ctx.postMessage({
              type: "PREDICTION",
              data: {
                gesture: null,
                confidence: maxProb,
                isIdle: true,
                bufferLength: frameBuffer.length,
              },
            } as WorkerResponse);
          } else {
            ctx.postMessage({
              type: "PREDICTION",
              data: {
                gesture: { gloss: predictedLabel, confidence: maxProb },
                isIdle: false,
                bufferLength: frameBuffer.length,
                timestamp: performance.now(),
              },
            } as WorkerResponse);
          }
        } catch (e: any) {
          ctx.postMessage({ type: "ERROR", data: e?.message } as WorkerResponse);
        }
      } else {
        // Echo buffer progress
        if (frameBuffer.length === BUFFER_SIZE) {
          ctx.postMessage({
            type: "PREDICTION",
            data: {
              bufferLength: frameBuffer.length,
              timestamp: performance.now(),
            },
          } as WorkerResponse);
        }
      }
      break;

    case "RESET":
      frameBuffer = [];
      break;

    default:
      break;
  }
};

export {};
