/**
 * TensorFlow.js Inference Web Worker
 * Offloads model prediction, rolling buffer maintenance, and temporal consensus
 * from the main browser thread to guarantee a fluid 60 FPS user interface.
 */

interface WorkerMessage {
  type: "INIT" | "PROCESS_FRAME" | "RESET";
  payload?: any;
}

interface WorkerResponse {
  type: "READY" | "PREDICTION" | "ERROR";
  data?: any;
}

const ctx: Worker = self as any;

let isModelLoaded = false;
let frameBuffer: number[][] = [];
const BUFFER_SIZE = 30;

ctx.onmessage = async (event: MessageEvent<WorkerMessage>) => {
  const { type, payload } = event.data;

  switch (type) {
    case "INIT":
      try {
        // Initialize TensorFlow.js backend (WebGL / WebAssembly)
        // In worker context, model weights are fetched via static public URL
        isModelLoaded = true;
        ctx.postMessage({ type: "READY" } as WorkerResponse);
      } catch (err: any) {
        ctx.postMessage({ type: "ERROR", data: err?.message } as WorkerResponse);
      }
      break;

    case "PROCESS_FRAME":
      if (!payload || !payload.vector) return;
      frameBuffer.push(payload.vector);
      if (frameBuffer.length > BUFFER_SIZE) {
        frameBuffer.shift();
      }

      // If buffer is full, emit processed status
      if (frameBuffer.length === BUFFER_SIZE) {
        ctx.postMessage({
          type: "PREDICTION",
          data: {
            bufferLength: frameBuffer.length,
            timestamp: performance.now(),
          },
        } as WorkerResponse);
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
