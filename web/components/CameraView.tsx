"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";
import { liveVision, DetectedGesture } from "@/lib/mediapipeVision";
import { areHandsDetected, HolisticResults } from "@/lib/landmarks";

interface CameraViewProps {
  detectedSign: string | null;
  confidence: number;
  handsDetected: boolean;
  fps: number;
  isActive: boolean;
  onToggleActive: () => void;
  onLiveDetection?: (data: {
    results: HolisticResults;
    gesture: DetectedGesture | null;
    fps: number;
    handsDetected: boolean;
  }) => void;
}

export const CameraView: React.FC<CameraViewProps> = ({
  detectedSign,
  confidence,
  handsDetected,
  fps,
  isActive,
  onToggleActive,
  onLiveDetection,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isVisionLoading, setIsVisionLoading] = useState<boolean>(true);
  const [localFps, setLocalFps] = useState<number>(fps || 30);
  const [localHandsDetected, setLocalHandsDetected] = useState<boolean>(handsDetected);

  const animationFrameId = useRef<number | null>(null);
  const lastFrameTime = useRef<number>(performance.now());
  const frameCount = useRef<number>(0);

  // Initialize MediaPipe Vision Tasks on mount
  useEffect(() => {
    let isMounted = true;
    liveVision
      .initialize()
      .then((ready) => {
        if (isMounted) {
          setIsVisionLoading(!ready);
        }
      })
      .catch((err) => {
        console.error("Vision tracker initialization error:", err);
        if (isMounted) setIsVisionLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // WebCam Stream Setup
  useEffect(() => {
    let stream: MediaStream | null = null;

    if (isActive) {
      navigator.mediaDevices
        ?.getUserMedia({
          video: { width: 640, height: 480, facingMode: "user" },
          audio: false,
        })
        .then((s) => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play();
          }
          setCameraError(null);
        })
        .catch((err) => {
          console.error("Camera access error:", err);
          setCameraError("Camera access denied or unavailable. Please enable permissions.");
        });
    } else {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach((t) => t.stop());
        videoRef.current.srcObject = null;
      }
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [isActive]);

  // Main Detection Loop
  const runDetectionLoop = useCallback(() => {
    if (!isActive || !videoRef.current || !canvasRef.current) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const now = performance.now();

    if (video.readyState >= 2 && video.videoWidth > 0) {
      frameCount.current += 1;
      const delta = now - lastFrameTime.current;
      if (delta >= 1000) {
        const measuredFps = Math.round((frameCount.current * 1000) / delta);
        setLocalFps(measuredFps);
        frameCount.current = 0;
        lastFrameTime.current = now;
      }

      // Process frame through MediaPipe Holistic
      const frameData = liveVision.processFrame(video, canvas, now);
      if (frameData) {
        const hasHands = areHandsDetected(frameData.results);
        setLocalHandsDetected(hasHands);

        if (onLiveDetection) {
          onLiveDetection({
            results: frameData.results,
            gesture: frameData.gesture,
            fps: localFps,
            handsDetected: hasHands,
          });
        }
      }
    }

    animationFrameId.current = requestAnimationFrame(runDetectionLoop);
  }, [isActive, localFps, onLiveDetection]);

  useEffect(() => {
    if (isActive) {
      animationFrameId.current = requestAnimationFrame(runDetectionLoop);
    } else {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    }

    return () => {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [isActive, runDetectionLoop]);

  return (
    <div className="relative w-full aspect-[4/3] bg-space-950 rounded-2xl overflow-hidden border border-gold-500/30 shadow-2xl flex flex-col items-center justify-center">
      {isActive && (
        <video
          ref={videoRef}
          className="w-full h-full object-cover transform -scale-x-100"
          playsInline
          muted
        />
      )}

      {/* Real-Time Joint Overlay Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none transform -scale-x-100"
      />

      {/* Top Status Bar Chips */}
      <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-10 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md ${
              localHandsDetected
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50"
                : "bg-amber-500/20 text-amber-300 border border-amber-500/50"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                localHandsDetected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            {localHandsDetected ? "Hands Detected" : "Hands Resting"}
          </span>

          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-space-900/90 text-gold-300 border border-gold-500/30">
            {localFps} FPS
          </span>

          {isVisionLoading && (
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-gold-500/20 text-gold-300 border border-gold-500/40 animate-pulse">
              Loading AI Engine...
            </span>
          )}
        </div>

        {detectedSign && (
          <div className="px-3.5 py-1 rounded-full text-xs font-extrabold bg-gradient-to-r from-gold-400 to-gold-500 text-space-950 border border-gold-300 shadow-lg shadow-gold-500/30 flex items-center gap-2 animate-bounce">
            <span className="text-[10px] uppercase tracking-wider text-space-900">Sign:</span>
            <span className="tracking-wide uppercase font-black">{detectedSign}</span>
            <span className="text-[10px] bg-space-950 px-1.5 py-0.5 rounded text-gold-300 font-mono">
              {Math.round(confidence * 100)}%
            </span>
          </div>
        )}
      </div>

      {/* Camera Guidance Notice */}
      <div className="absolute bottom-4 left-4 z-10 px-3 py-1.5 rounded-lg bg-space-900/90 backdrop-blur text-[11px] text-slate-300 border border-gold-500/20">
        MediaPipe Holistic Landmark Engine &bull; Upper Body &amp; 42 Hand Joints Active
      </div>

      {/* Placeholder / Error State */}
      {(!isActive || cameraError) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-space-950/95 z-20">
          <div className="w-16 h-16 rounded-full bg-space-850 border border-gold-500/30 flex items-center justify-center mb-4 text-gold-400 text-2xl">
            📷
          </div>
          <h3 className="text-lg font-bold text-white mb-2">
            {cameraError ? "Camera Error" : "Camera is Paused"}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mb-6">
            {cameraError ||
              "Enable camera access to begin real-time Indian Sign Language recognition."}
          </p>
          <button
            onClick={onToggleActive}
            className="px-6 py-2.5 rounded-xl font-bold bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 text-space-950 transition-all duration-200 shadow-lg"
          >
            {isActive ? "Retry Camera" : "Start Camera"}
          </button>
        </div>
      )}
    </div>
  );
};
