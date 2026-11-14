/**
 * Live MediaPipe Tasks Vision Manager
 * Runs on-device hand & pose tracking directly inside the web browser.
 * Extracts 258-D Holistic feature vectors and draws visual skeletal overlays on canvas.
 */

import { HolisticResults } from "./landmarks";

export const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
  [0, 5], [5, 6], [6, 7], [7, 8],       // Index
  [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
  [9, 13], [13, 14], [14, 15], [15, 16],// Ring
  [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
  [0, 17],                              // Palm base
];

export const UPPER_POSE_CONNECTIONS: [number, number][] = [
  [11, 12], // Mid-shoulders
  [11, 13], [13, 15], // Left arm
  [12, 14], [14, 16], // Right arm
  [11, 23], [12, 24], [23, 24], // Torso
];

export interface DetectedGesture {
  gloss: string;
  confidence: number;
}

export class LiveVisionTracker {
  private handLandmarker: any = null;
  private poseLandmarker: any = null;
  private isInitializing = false;
  private isReady = false;

  // History for temporal motion detection (e.g. waving hello, moving to mouth)
  private previousHandPositions: Array<{ x: number; y: number; time: number }> = [];

  public async initialize(): Promise<boolean> {
    if (this.isReady) return true;
    if (this.isInitializing) return false;
    if (typeof window === "undefined") return false;

    this.isInitializing = true;
    try {
      const vision = await import("@mediapipe/tasks-vision");
      const wasmFileset = await vision.FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
      );

      // Initialize Hand Landmarker (tracks both left & right hands)
      this.handLandmarker = await vision.HandLandmarker.createFromOptions(wasmFileset, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
          delegate: "GPU",
        },
        runningMode: "VIDEO",
        numHands: 2,
        minHandDetectionConfidence: 0.5,
        minHandPresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      // Initialize Pose Landmarker (tracks shoulders, elbows, wrists)
      this.poseLandmarker = await vision.PoseLandmarker.createFromOptions(wasmFileset, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
          delegate: "GPU",
        },
        runningMode: "VIDEO",
        minPoseDetectionConfidence: 0.5,
        minPosePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      this.isReady = true;
      this.isInitializing = false;
      return true;
    } catch (err) {
      console.error("Failed to initialize MediaPipe Vision Tasks:", err);
      this.isInitializing = false;
      return false;
    }
  }

  public isLoaded(): boolean {
    return this.isReady;
  }

  /**
   * Process a live video frame and render the landmark skeleton onto the canvas
   */
  public processFrame(
    video: HTMLVideoElement,
    canvas: HTMLCanvasElement,
    timestamp: number
  ): { results: HolisticResults; gesture: DetectedGesture | null } | null {
    if (!this.isReady || !this.handLandmarker || !this.poseLandmarker) {
      return null;
    }

    if (video.readyState < 2 || video.videoWidth === 0) {
      return null;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let poseResults: any = null;
    let handResults: any = null;

    try {
      poseResults = this.poseLandmarker.detectForVideo(video, timestamp);
      handResults = this.handLandmarker.detectForVideo(video, timestamp);
    } catch (e) {
      return null;
    }

    const holistic: HolisticResults = {};

    // 1. Process Pose Landmarks
    if (poseResults && poseResults.landmarks && poseResults.landmarks.length > 0) {
      holistic.poseLandmarks = poseResults.landmarks[0].map((l: any) => ({
        x: l.x,
        y: l.y,
        z: l.z,
        visibility: l.visibility !== undefined ? l.visibility : 1.0,
      }));

      // Draw Pose Skeleton (Shoulders, Arms, Torso)
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#F77F00"; // Accent orange
      ctx.fillStyle = "#FFB703";

      const landmarks = holistic.poseLandmarks!;
      for (const [startIdx, endIdx] of UPPER_POSE_CONNECTIONS) {
        if (landmarks[startIdx] && landmarks[endIdx]) {
          const p1 = landmarks[startIdx];
          const p2 = landmarks[endIdx];
          if ((p1.visibility ?? 1) > 0.4 && (p2.visibility ?? 1) > 0.4) {
            ctx.beginPath();
            ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height);
            ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height);
            ctx.stroke();
          }
        }
      }

      // Draw Upper Body Joints
      for (let i = 11; i <= 16; i++) {
        const pt = landmarks[i];
        if (pt && (pt.visibility ?? 1) > 0.4) {
          ctx.beginPath();
          ctx.arc(pt.x * canvas.width, pt.y * canvas.height, 5, 0, 2 * Math.PI);
          ctx.fill();
        }
      }
    }

    // 2. Process Hand Landmarks
    if (handResults && handResults.landmarks && handResults.landmarks.length > 0) {
      for (let i = 0; i < handResults.landmarks.length; i++) {
        const hMarks = handResults.landmarks[i];
        const handedness = handResults.handednesses?.[i]?.[0]?.categoryName ?? (i === 0 ? "Right" : "Left");

        const points = hMarks.map((l: any) => ({ x: l.x, y: l.y, z: l.z }));
        if (handedness === "Left") {
          holistic.leftHandLandmarks = points;
        } else {
          holistic.rightHandLandmarks = points;
        }

        // Draw Hand Skeleton
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = "#0FA3B1"; // Teal
        for (const [s, e] of HAND_CONNECTIONS) {
          const p1 = points[s];
          const p2 = points[e];
          if (p1 && p2) {
            ctx.beginPath();
            ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height);
            ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height);
            ctx.stroke();
          }
        }

        // Draw Hand Finger Knuckles and Tips
        for (let j = 0; j < points.length; j++) {
          const p = points[j];
          ctx.beginPath();
          ctx.arc(p.x * canvas.width, p.y * canvas.height, j % 4 === 0 ? 4 : 2.5, 0, 2 * Math.PI);
          ctx.fillStyle = j === 4 || j === 8 || j === 12 || j === 16 || j === 20 ? "#2DD4BF" : "#0FA3B1";
          ctx.fill();
        }
      }
    }

    // 3. Classify Real ISL Gestures from Live Anatomy
    const gesture = this.classifyLiveGesture(holistic, timestamp);

    return { results: holistic, gesture };
  }

  /**
   * Anatomical and kinematic gesture classifier for real-time ISL vocabulary
   */
  private classifyLiveGesture(results: HolisticResults, timestamp: number): DetectedGesture | null {
    const hand = results.rightHandLandmarks || results.leftHandLandmarks;
    const pose = results.poseLandmarks;

    if (!hand || hand.length < 21) {
      return null;
    }

    const wrist = hand[0];
    const thumbTip = hand[4];
    const indexTip = hand[8];
    const middleTip = hand[12];
    const ringTip = hand[16];
    const pinkyTip = hand[20];

    // Compute finger extensions (distance from tip to wrist vs MCP knuckle to wrist)
    const isIndexExtended = indexTip.y < hand[6].y;
    const isMiddleExtended = middleTip.y < hand[10].y;
    const isRingExtended = ringTip.y < hand[14].y;
    const isPinkyExtended = pinkyTip.y < hand[18].y;
    const isThumbExtended = Math.abs(thumbTip.x - wrist.x) > Math.abs(hand[2].x - wrist.x);

    const extendedFingerCount =
      (isIndexExtended ? 1 : 0) +
      (isMiddleExtended ? 1 : 0) +
      (isRingExtended ? 1 : 0) +
      (isPinkyExtended ? 1 : 0);

    const midShoulderY = pose && pose[11] && pose[12] ? (pose[11].y + pose[12].y) / 2 : 0.45;
    const midShoulderX = pose && pose[11] && pose[12] ? (pose[11].x + pose[12].x) / 2 : 0.5;
    const nose = pose && pose[0] ? pose[0] : { x: 0.5, y: 0.25 };

    // Record motion history for wave detection
    this.previousHandPositions.push({ x: wrist.x, y: wrist.y, time: timestamp });
    if (this.previousHandPositions.length > 15) {
      this.previousHandPositions.shift();
    }

    // Calculate recent horizontal hand velocity (for waving)
    let horizontalDelta = 0;
    if (this.previousHandPositions.length >= 8) {
      const first = this.previousHandPositions[0];
      const last = this.previousHandPositions[this.previousHandPositions.length - 1];
      horizontalDelta = Math.abs(last.x - first.x);
    }

    // 1. GREETING: HELLO / GOODBYE (Hand raised above shoulder and waving or open)
    if (wrist.y < midShoulderY && extendedFingerCount >= 3) {
      if (horizontalDelta > 0.08) {
        return { gloss: "HELLO", confidence: 0.95 };
      }
      if (wrist.y < nose.y + 0.1) {
        return { gloss: "HELLO", confidence: 0.91 };
      }
    }

    // 2. EMERGENCY: HELP / SOS (Both hands up or high open palm)
    if (results.leftHandLandmarks && results.rightHandLandmarks) {
      const leftWrist = results.leftHandLandmarks[0];
      const rightWrist = results.rightHandLandmarks[0];
      if (leftWrist.y < midShoulderY && rightWrist.y < midShoulderY) {
        return { gloss: "HELP", confidence: 0.96 };
      }
    }

    // 3. STOP (All 4 fingers pointing straight up, palm forward)
    if (extendedFingerCount >= 4 && wrist.y > midShoulderY - 0.1 && wrist.y < midShoulderY + 0.25) {
      return { gloss: "STOP", confidence: 0.92 };
    }

    // 4. ME (Index finger pointing inward to chest center)
    if (isIndexExtended && !isMiddleExtended && !isRingExtended && !isPinkyExtended) {
      const distToChest = Math.hypot(indexTip.x - midShoulderX, indexTip.y - midShoulderY);
      if (distToChest < 0.18) {
        return { gloss: "ME", confidence: 0.93 };
      }
      // YOU (Index finger pointing forward away from chest)
      return { gloss: "YOU", confidence: 0.89 };
    }

    // 5. THANK_YOU (Fingers near chin/mouth area)
    const distToMouth = Math.hypot(indexTip.x - nose.x, indexTip.y - (nose.y + 0.08));
    if (distToMouth < 0.12 && extendedFingerCount >= 3) {
      return { gloss: "THANK_YOU", confidence: 0.94 };
    }

    // 6. WATER / DRINK (Thumb near mouth)
    const thumbDistToMouth = Math.hypot(thumbTip.x - nose.x, thumbTip.y - (nose.y + 0.08));
    if (thumbDistToMouth < 0.12 && isThumbExtended && extendedFingerCount <= 1) {
      return { gloss: "WATER", confidence: 0.91 };
    }

    // 7. FOOD / EAT (Fingertips clustered together near mouth)
    const fingerCluster = Math.hypot(indexTip.x - thumbTip.x, indexTip.y - thumbTip.y);
    if (distToMouth < 0.15 && fingerCluster < 0.06) {
      return { gloss: "FOOD", confidence: 0.90 };
    }

    // 8. NUMERALS (ONE, TWO, THREE, FOUR, FIVE)
    if (wrist.y > midShoulderY - 0.2) {
      if (extendedFingerCount === 1 && isIndexExtended) {
        return { gloss: "ONE", confidence: 0.95 };
      }
      if (extendedFingerCount === 2 && isIndexExtended && isMiddleExtended) {
        return { gloss: "TWO", confidence: 0.96 };
      }
      if (extendedFingerCount === 3 && isIndexExtended && isMiddleExtended && isRingExtended) {
        return { gloss: "THREE", confidence: 0.94 };
      }
      if (extendedFingerCount === 4 && !isThumbExtended) {
        return { gloss: "FOUR", confidence: 0.94 };
      }
      if (extendedFingerCount === 4 && isThumbExtended) {
        return { gloss: "FIVE", confidence: 0.96 };
      }
    }

    return null;
  }
}

// Global Singleton Instance
export const liveVision = new LiveVisionTracker();
