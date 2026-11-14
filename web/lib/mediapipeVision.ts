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
  // Buffer for temporal consensus voting to eliminate spurious frames
  private consensusBuffer: Array<string | null> = [];

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
   * Strict IDLE filtering and multi-frame consensus
   */
  private classifyLiveGesture(results: HolisticResults, timestamp: number): DetectedGesture | null {
    const rawCandidate = this.evaluateCandidateGesture(results, timestamp);

    // Multi-frame consensus voting: require 4 out of last 5 frames to agree
    this.consensusBuffer.push(rawCandidate ? rawCandidate.gloss : null);
    if (this.consensusBuffer.length > 5) {
      this.consensusBuffer.shift();
    }

    if (!rawCandidate) {
      return null;
    }

    const matchingCount = this.consensusBuffer.filter((g) => g === rawCandidate.gloss).length;
    if (matchingCount >= 4) {
      return rawCandidate;
    }

    return null;
  }

  private evaluateCandidateGesture(results: HolisticResults, timestamp: number): DetectedGesture | null {
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

    const midShoulderY = pose && pose[11] && pose[12] ? (pose[11].y + pose[12].y) / 2 : 0.45;
    const midShoulderX = pose && pose[11] && pose[12] ? (pose[11].x + pose[12].x) / 2 : 0.5;
    const nose = pose && pose[0] ? pose[0] : { x: 0.5, y: 0.25 };

    // 0. STRICT IDLE FILTER:
    // If hand is resting low on desk/lap (wrist below midShoulder by > 0.18, or y > 0.70), it is IDLE
    if (wrist.y > midShoulderY + 0.18 || wrist.y > 0.70) {
      return null;
    }

    // Record motion history
    this.previousHandPositions.push({ x: wrist.x, y: wrist.y, time: timestamp });
    if (this.previousHandPositions.length > 15) {
      this.previousHandPositions.shift();
    }

    // Compute recent horizontal and overall motion
    let horizontalDelta = 0;
    let totalMovement = 0;
    if (this.previousHandPositions.length >= 8) {
      const first = this.previousHandPositions[0];
      const last = this.previousHandPositions[this.previousHandPositions.length - 1];
      horizontalDelta = Math.abs(last.x - first.x);

      for (let i = 1; i < this.previousHandPositions.length; i++) {
        totalMovement += Math.hypot(
          this.previousHandPositions[i].x - this.previousHandPositions[i - 1].x,
          this.previousHandPositions[i].y - this.previousHandPositions[i - 1].y
        );
      }
    }

    // Compute finger extensions (distance from tip to wrist vs MCP knuckle to wrist)
    const isIndexExtended = indexTip.y < hand[6].y - 0.02;
    const isMiddleExtended = middleTip.y < hand[10].y - 0.02;
    const isRingExtended = ringTip.y < hand[14].y - 0.02;
    const isPinkyExtended = pinkyTip.y < hand[18].y - 0.02;
    const isThumbExtended = Math.abs(thumbTip.x - wrist.x) > Math.abs(hand[2].x - wrist.x) + 0.02;

    const extendedFingerCount =
      (isIndexExtended ? 1 : 0) +
      (isMiddleExtended ? 1 : 0) +
      (isRingExtended ? 1 : 0) +
      (isPinkyExtended ? 1 : 0);

    // 1. EMERGENCY: HELP / SOS (Both hands held up above chest with open palms)
    if (results.leftHandLandmarks && results.rightHandLandmarks) {
      const leftWrist = results.leftHandLandmarks[0];
      const rightWrist = results.rightHandLandmarks[0];
      if (leftWrist.y < midShoulderY + 0.05 && rightWrist.y < midShoulderY + 0.05) {
        return { gloss: "HELP", confidence: 0.96 };
      }
    }

    // 2. GREETING: HELLO (Hand raised above shoulder level AND actively waving side-to-side)
    if (wrist.y < midShoulderY - 0.05 && extendedFingerCount >= 3) {
      if (horizontalDelta > 0.08) {
        return { gloss: "HELLO", confidence: 0.95 };
      }
      // If hand is raised high near head and open, require clear horizontal motion
      if (wrist.y < nose.y + 0.05 && middleTip.y < wrist.y - 0.12 && horizontalDelta > 0.04) {
        return { gloss: "HELLO", confidence: 0.91 };
      }
    }

    // 3. STOP (All 4 fingers pointing straight up, palm forward, steady in upper chest region)
    const isPalmVertical = middleTip.y < wrist.y - 0.12;
    if (
      extendedFingerCount >= 4 &&
      isPalmVertical &&
      wrist.y > midShoulderY - 0.08 &&
      wrist.y < midShoulderY + 0.12 &&
      totalMovement < 0.10 // Steady, deliberate hold
    ) {
      return { gloss: "STOP", confidence: 0.93 };
    }

    // 4. ME (Index finger pointing inward and touching/approaching center of chest)
    if (isIndexExtended && !isMiddleExtended && !isRingExtended && !isPinkyExtended) {
      const distToChest = Math.hypot(indexTip.x - midShoulderX, indexTip.y - midShoulderY);
      if (distToChest < 0.13) {
        return { gloss: "ME", confidence: 0.94 };
      }
      // YOU (Index finger pointing forward away from body with arm extended)
      if (indexTip.y < wrist.y && Math.abs(indexTip.x - midShoulderX) > 0.12 && distToChest > 0.20) {
        return { gloss: "YOU", confidence: 0.90 };
      }
    }

    // 5. THANK_YOU (Fingers flat near chin/mouth and moving slightly forward)
    const distToMouth = Math.hypot(indexTip.x - nose.x, indexTip.y - (nose.y + 0.08));
    if (distToMouth < 0.10 && extendedFingerCount >= 3 && wrist.y < midShoulderY) {
      return { gloss: "THANK_YOU", confidence: 0.94 };
    }

    // 6. WATER / DRINK (Thumb tip touching mouth, other 4 fingers curled down)
    const thumbDistToMouth = Math.hypot(thumbTip.x - nose.x, thumbTip.y - (nose.y + 0.08));
    if (thumbDistToMouth < 0.09 && isThumbExtended && extendedFingerCount <= 1) {
      return { gloss: "WATER", confidence: 0.92 };
    }

    // 7. FOOD / EAT (Fingertips clustered/pinched together near mouth)
    const fingerCluster = Math.hypot(indexTip.x - thumbTip.x, indexTip.y - thumbTip.y);
    if (distToMouth < 0.11 && fingerCluster < 0.04) {
      return { gloss: "FOOD", confidence: 0.91 };
    }

    // 8. NUMERALS (ONE, TWO, THREE, FOUR, FIVE) - Deliberate upright hand at upper chest
    if (wrist.y < midShoulderY + 0.12 && wrist.y > midShoulderY - 0.15 && isPalmVertical) {
      if (extendedFingerCount === 1 && isIndexExtended && !isThumbExtended) {
        return { gloss: "ONE", confidence: 0.95 };
      }
      if (extendedFingerCount === 2 && isIndexExtended && isMiddleExtended && !isRingExtended && !isThumbExtended) {
        return { gloss: "TWO", confidence: 0.96 };
      }
      if (extendedFingerCount === 3 && isIndexExtended && isMiddleExtended && isRingExtended && !isPinkyExtended) {
        return { gloss: "THREE", confidence: 0.94 };
      }
      if (extendedFingerCount === 4 && !isThumbExtended) {
        return { gloss: "FOUR", confidence: 0.94 };
      }
      if (extendedFingerCount === 4 && isThumbExtended) {
        return { gloss: "FIVE", confidence: 0.96 };
      }
    }

    return null; // IDLE
  }
}

// Global Singleton Instance
export const liveVision = new LiveVisionTracker();
