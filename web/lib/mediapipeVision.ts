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

    // Multi-frame consensus voting: require 5 out of last 7 frames to agree
    this.consensusBuffer.push(rawCandidate ? rawCandidate.gloss : null);
    if (this.consensusBuffer.length > 7) {
      this.consensusBuffer.shift();
    }

    if (!rawCandidate) {
      return null;
    }

    const matchingCount = this.consensusBuffer.filter((g) => g === rawCandidate.gloss).length;
    if (matchingCount >= 5) {
      return rawCandidate;
    }

    return null;
  }

  private evaluateCandidateGesture(results: HolisticResults, timestamp: number): DetectedGesture | null {
    const leftHand = results.leftHandLandmarks;
    const rightHand = results.rightHandLandmarks;
    const pose = results.poseLandmarks;

    // Must have at least one hand detected
    if ((!leftHand || leftHand.length < 21) && (!rightHand || rightHand.length < 21)) {
      return null;
    }

    const midShoulderY = pose && pose[11] && pose[12] ? (pose[11].y + pose[12].y) / 2 : 0.45;
    const midShoulderX = pose && pose[11] && pose[12] ? (pose[11].x + pose[12].x) / 2 : 0.5;
    const nose = pose && pose[0] ? pose[0] : { x: 0.5, y: 0.25 };

    // Helper to evaluate finger extensions relative to palm
    const getFingerExtensions = (h: Array<{ x: number; y: number; z: number }>) => {
      const w = h[0];
      const isExt = (tipIdx: number, mcpIdx: number) => {
        const dTip = Math.hypot(h[tipIdx].x - w.x, h[tipIdx].y - w.y);
        const dMcp = Math.hypot(h[mcpIdx].x - w.x, h[mcpIdx].y - w.y);
        return dTip > dMcp * 1.30;
      };

      const thumbExt = Math.hypot(h[4].x - w.x, h[4].y - w.y) > Math.hypot(h[2].x - w.x, h[2].y - w.y) * 1.25;
      const indexExt = isExt(8, 5);
      const middleExt = isExt(12, 9);
      const ringExt = isExt(16, 13);
      const pinkyExt = isExt(20, 17);

      const count = (indexExt ? 1 : 0) + (middleExt ? 1 : 0) + (ringExt ? 1 : 0) + (pinkyExt ? 1 : 0);
      return { thumbExt, indexExt, middleExt, ringExt, pinkyExt, count };
    };

    // 0. STRICT IDLE FILTER
    // If both hands are resting low (near lap/desk below chest), it is strictly IDLE
    if (leftHand && rightHand) {
      if (leftHand[0].y > midShoulderY + 0.12 && rightHand[0].y > midShoulderY + 0.12) {
        return null; // IDLE: Hands resting down
      }
    }

    // Dominant active hand
    const activeHand = (rightHand && rightHand.length >= 21) ? rightHand : leftHand!;
    const wrist = activeHand[0];
    const thumbTip = activeHand[4];
    const indexTip = activeHand[8];
    const middleTip = activeHand[12];

    // Single active hand resting low down
    if (wrist.y > midShoulderY + 0.16 || wrist.y > 0.68) {
      return null; // IDLE: Hand below signing area
    }

    // Record motion history of active wrist
    this.previousHandPositions.push({ x: wrist.x, y: wrist.y, time: timestamp });
    if (this.previousHandPositions.length > 15) {
      this.previousHandPositions.shift();
    }

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

    const { thumbExt, indexExt, middleExt, ringExt, pinkyExt, count: extendedFingerCount } = getFingerExtensions(activeHand);

    // =========================================================================
    // 1. TWO-HANDED GESTURES (Strictly verified)
    // =========================================================================
    if (leftHand && rightHand && leftHand.length >= 21 && rightHand.length >= 21) {
      const leftWrist = leftHand[0];
      const rightWrist = rightHand[0];
      const leftExt = getFingerExtensions(leftHand);
      const rightExt = getFingerExtensions(rightHand);
      const handsDistance = Math.hypot(leftWrist.x - rightWrist.x, leftWrist.y - rightWrist.y);

      // 1A. WELCOME / NAMASTE (Palms together in prayer at chest level)
      const tipsDistance = Math.hypot(leftHand[8].x - rightHand[8].x, leftHand[8].y - rightHand[8].y);
      if (
        handsDistance < 0.12 &&
        tipsDistance < 0.09 &&
        leftHand[12].y < leftWrist.y &&
        rightHand[12].y < rightWrist.y &&
        leftWrist.y < midShoulderY + 0.15
      ) {
        return { gloss: "WELCOME", confidence: 0.95 };
      }

      // 1B. ISL HELP (Standard ISLRTC: One flat open palm facing up with closed fist on top of it)
      const isOneFlatOneFist =
        (leftExt.count >= 4 && rightExt.count <= 1) ||
        (rightExt.count >= 4 && leftExt.count <= 1);
      if (
        handsDistance < 0.14 &&
        isOneFlatOneFist &&
        leftWrist.y < midShoulderY + 0.12 &&
        rightWrist.y < midShoulderY + 0.12
      ) {
        return { gloss: "HELP", confidence: 0.96 };
      }

      // 1C. EMERGENCY SOS: Both hands raised HIGH above chest/shoulders with open waving/raised palms
      if (
        leftWrist.y < midShoulderY - 0.10 &&
        rightWrist.y < midShoulderY - 0.10 &&
        leftExt.count >= 4 &&
        rightExt.count >= 4 &&
        handsDistance > 0.15
      ) {
        return { gloss: "HELP", confidence: 0.95 };
      }
    }

    // =========================================================================
    // 2. SINGLE-HAND DELIBERATE GESTURES
    // =========================================================================

    // 2A. GREETING: HELLO (Hand raised HIGH near temple/ear, open palm actively waving)
    if (wrist.y < midShoulderY - 0.08 && extendedFingerCount >= 3) {
      if (horizontalDelta > 0.05 || (wrist.y < nose.y + 0.08 && middleTip.y < wrist.y - 0.10)) {
        return { gloss: "HELLO", confidence: 0.95 };
      }
    }

    // 2B. STOP (Palm vertical facing forward at chest level, all 4 fingers extended together, held steady)
    const isPalmVertical = middleTip.y < wrist.y - 0.12;
    if (
      extendedFingerCount >= 4 &&
      isPalmVertical &&
      wrist.y > midShoulderY - 0.10 &&
      wrist.y < midShoulderY + 0.12 &&
      totalMovement < 0.08
    ) {
      return { gloss: "STOP", confidence: 0.93 };
    }

    // 2C. ME (Index finger pointing inward and touching/approaching center of chest)
    if (indexExt && !middleExt && !ringExt && !pinkyExt) {
      const distToChest = Math.hypot(indexTip.x - midShoulderX, indexTip.y - midShoulderY);
      if (distToChest < 0.12) {
        return { gloss: "ME", confidence: 0.94 };
      }
      // YOU (Index finger pointing forward away from body towards camera)
      if (indexTip.y < wrist.y && Math.abs(indexTip.x - midShoulderX) > 0.10 && distToChest > 0.20) {
        return { gloss: "YOU", confidence: 0.91 };
      }
    }

    // 2D. THANK_YOU (Fingers flat near chin/mouth and moving forward away from face)
    const distToMouth = Math.hypot(indexTip.x - nose.x, indexTip.y - (nose.y + 0.08));
    if (distToMouth < 0.10 && extendedFingerCount >= 3 && wrist.y < midShoulderY) {
      return { gloss: "THANK_YOU", confidence: 0.94 };
    }

    // 2E. WATER / DRINK (Thumb tip touching or approaching mouth, other 4 fingers curled)
    const thumbDistToMouth = Math.hypot(thumbTip.x - nose.x, thumbTip.y - (nose.y + 0.08));
    if (thumbDistToMouth < 0.09 && thumbExt && extendedFingerCount <= 1) {
      return { gloss: "WATER", confidence: 0.93 };
    }

    // 2F. FOOD / EAT (Fingertips clustered/pinched together moving near mouth)
    const fingerCluster = Math.hypot(indexTip.x - thumbTip.x, indexTip.y - thumbTip.y);
    if (distToMouth < 0.11 && fingerCluster < 0.04) {
      return { gloss: "FOOD", confidence: 0.92 };
    }

    // 2G. NUMERALS (ONE, TWO, THREE, FOUR, FIVE) - Deliberate upright fingers in front of chest
    if (wrist.y < midShoulderY + 0.12 && wrist.y > midShoulderY - 0.14 && isPalmVertical) {
      if (extendedFingerCount === 1 && indexExt && !thumbExt) {
        return { gloss: "ONE", confidence: 0.95 };
      }
      if (extendedFingerCount === 2 && indexExt && middleExt && !ringExt && !thumbExt) {
        return { gloss: "TWO", confidence: 0.96 };
      }
      if (extendedFingerCount === 3 && indexExt && middleExt && ringExt && !pinkyExt) {
        return { gloss: "THREE", confidence: 0.94 };
      }
      if (extendedFingerCount === 4 && !thumbExt) {
        return { gloss: "FOUR", confidence: 0.94 };
      }
      if (extendedFingerCount === 4 && thumbExt) {
        return { gloss: "FIVE", confidence: 0.96 };
      }
    }

    return null; // IDLE
  }
}

// Global Singleton Instance
export const liveVision = new LiveVisionTracker();
