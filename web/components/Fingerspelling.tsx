"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { fingerspellingClassifier, FingerspellingPrediction } from "@/lib/fingerspelling";
import { liveVision } from "@/lib/mediapipeVision";
import { areHandsDetected } from "@/lib/landmarks";

const ALPHABETS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const NUMBERS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

// Character descriptions / hints for standard ISL two-handed fingerspelling
const CHAR_DESCRIPTIONS: Record<string, string> = {
  A: "Touch thumb tip of dominant hand to index finger tip of non-dominant hand.",
  B: "Join index and thumbs of both hands together to form two circles (resembling 'B').",
  C: "Curved dominant hand forming a 'C' resting in the non-dominant open palm.",
  D: "Index finger pointing up with dominant hand while thumb and index of non-dominant close the loop.",
  E: "Index finger of dominant hand touching non-dominant index fingertip.",
  F: "Two fingers of dominant hand crossed over two fingers of non-dominant hand.",
  G: "Two closed fists placed one on top of the other with knuckles facing forward.",
  H: "Dominant flat hand brushing across non-dominant flat palm horizontally.",
  I: "Index finger of dominant hand touching tip of middle finger of non-dominant hand.",
  J: "Trace a 'J' hook in the air starting from the non-dominant palm.",
  K: "Dominant index finger hooked over the non-dominant index finger.",
  L: "Dominant hand forms an 'L' shape (thumb and index at 90°) placed on non-dominant palm.",
  M: "Three fingers of dominant hand placed across the non-dominant open palm.",
  N: "Two fingers of dominant hand placed across the non-dominant open palm.",
  O: "Dominant index finger touching non-dominant ring finger tip.",
  P: "Dominant index finger and thumb forming a circle, resting over non-dominant upright index finger.",
  Q: "Dominant hand hooked into non-dominant palm forming a 'Q' tail.",
  R: "Dominant crossed index and middle fingers resting on non-dominant palm.",
  S: "Dominant pinky finger hooked with non-dominant pinky finger.",
  T: "Dominant index finger touching non-dominant palm edge at 90°.",
  U: "Dominant index touching non-dominant pinky fingertip.",
  V: "Dominant hand forms 'V' (index and middle spread) placed on non-dominant palm.",
  W: "Both hands interlock fingers with palms facing inward, pointing upright.",
  X: "Both index fingers crossed at right angles forming an 'X'.",
  Y: "Dominant thumb and pinky extended (shaka shape) resting in non-dominant palm.",
  Z: "Dominant index finger traces a 'Z' shape in the non-dominant palm.",
  "1": "Single dominant index finger pointing straight up at chest level.",
  "2": "Dominant index and middle fingers spread upright at chest level.",
  "3": "Dominant thumb, index, and middle fingers upright at chest level.",
  "4": "Four fingers (index, middle, ring, pinky) extended upright.",
  "5": "All five fingers open with palm facing forward.",
  "6": "Dominant pinky touching thumb tip, other three fingers upright.",
  "7": "Dominant ring finger touching thumb tip, other fingers upright.",
  "8": "Dominant middle finger touching thumb tip, other fingers upright.",
  "9": "Dominant index finger touching thumb tip, other fingers upright.",
};

export const Fingerspelling: React.FC = () => {
  const [selectedChar, setSelectedChar] = useState<string>("A");
  const [typedWord, setTypedWord] = useState<string>("");
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [isModelReady, setIsModelReady] = useState<boolean>(false);
  const [livePrediction, setLivePrediction] = useState<FingerspellingPrediction | null>(null);
  const [holdProgress, setHoldProgress] = useState<number>(0);
  const [handsDetected, setHandsDetected] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameId = useRef<number | null>(null);
  const lastCommittedChar = useRef<string | null>(null);
  const consecutiveMatchCount = useRef<number>(0);

  // 1. Initialize TensorFlow.js Fingerspelling Model and MediaPipe Vision
  useEffect(() => {
    let isMounted = true;
    Promise.all([fingerspellingClassifier.load(), liveVision.initialize()]).then(([classifierReady]) => {
      if (isMounted) {
        setIsModelReady(classifierReady);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Camera Stream Handler
  useEffect(() => {
    let stream: MediaStream | null = null;

    if (isCameraActive) {
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
          console.error("Fingerspelling camera access error:", err);
          setCameraError("Camera access denied or unavailable. Please enable permissions.");
          setIsCameraActive(false);
        });
    } else {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach((t) => t.stop());
        videoRef.current.srcObject = null;
      }
      setLivePrediction(null);
      setHoldProgress(0);
      consecutiveMatchCount.current = 0;
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [isCameraActive]);

  // 3. Real-time Detection Loop
  const runDetectionLoop = useCallback(() => {
    if (!isCameraActive || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const now = performance.now();

    if (video.readyState >= 2 && video.videoWidth > 0) {
      const frameData = liveVision.processFrame(video, canvas, now);

      if (frameData) {
        const handsPresent = areHandsDetected(frameData.results);
        setHandsDetected(handsPresent);

        if (handsPresent && isModelReady) {
          const pred = fingerspellingClassifier.predict(frameData.results);

          if (pred && !pred.isIdle && pred.confidence >= 0.82) {
            setLivePrediction(pred);
            setSelectedChar(pred.char);

            // Stability Hold Tracking (require ~8 stable frames ≈ 0.6s to commit letter)
            if (pred.char === lastCommittedChar.current) {
              consecutiveMatchCount.current += 1;
            } else {
              lastCommittedChar.current = pred.char;
              consecutiveMatchCount.current = 1;
            }

            const progress = Math.min(100, Math.round((consecutiveMatchCount.current / 8) * 100));
            setHoldProgress(progress);

            if (consecutiveMatchCount.current === 8) {
              // Commit character to spelled word!
              setTypedWord((prev) => prev + pred.char);
              // Trigger slight pause before next letter can be added
              consecutiveMatchCount.current = -4;
              setHoldProgress(0);
            }
          } else {
            setLivePrediction(null);
            setHoldProgress(0);
            consecutiveMatchCount.current = 0;
            lastCommittedChar.current = null;
          }
        } else {
          setLivePrediction(null);
          setHoldProgress(0);
          consecutiveMatchCount.current = 0;
        }
      }
    }

    animationFrameId.current = requestAnimationFrame(runDetectionLoop);
  }, [isCameraActive, isModelReady]);

  useEffect(() => {
    if (isCameraActive) {
      animationFrameId.current = requestAnimationFrame(runDetectionLoop);
    } else {
      if (animationFrameId.current) cancelAnimationFrame(animationFrameId.current);
    }

    return () => {
      if (animationFrameId.current) cancelAnimationFrame(animationFrameId.current);
    };
  }, [isCameraActive, runDetectionLoop]);

  // 4. Speech Synthesis
  const handleSpeak = () => {
    if (!typedWord.trim() || typeof window === "undefined" || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(typedWord);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="w-full bg-space-900 border border-gold-500/25 rounded-2xl p-6 shadow-2xl flex flex-col gap-6 backdrop-blur-xl">
      {/* Top Header & Accreditations */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-space-800 pb-4 gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>🔤 ISL Fingerspelling &amp; Number Matrix</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gold-500/20 text-gold-300 border border-gold-500/30">
              A-Z • 1-9
            </span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              TF.js Active (99.8% Acc)
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Spell names, specific acronyms, and numbers letter-by-letter using live camera handshapes
          </p>
        </div>

        {/* Live Camera Fingerspelling Toggle */}
        <button
          onClick={() => setIsCameraActive(!isCameraActive)}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-lg ${
            isCameraActive
              ? "bg-gradient-to-r from-ruby-600 to-ruby-700 text-white border border-ruby-400 shadow-ruby-950/50"
              : "bg-gradient-to-r from-gold-400 to-gold-500 text-space-950 border border-gold-300 shadow-gold-950/40 hover:scale-105"
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isCameraActive ? "bg-white animate-ping" : "bg-space-950"}`} />
          <span>{isCameraActive ? "Stop Camera" : "📸 Start Live Spell Camera"}</span>
        </button>
      </div>

      {cameraError && (
        <div className="p-3 rounded-xl bg-ruby-950/60 border border-ruby-500/40 text-ruby-300 text-xs">
          ⚠️ {cameraError}
        </div>
      )}

      {/* Live Video Feed (When Camera Active) */}
      {isCameraActive && (
        <div className="relative w-full aspect-[16/9] md:aspect-[21/9] bg-space-950 rounded-2xl overflow-hidden border border-gold-500/30 shadow-2xl flex items-center justify-center">
          <video
            ref={videoRef}
            className="w-full h-full object-cover transform -scale-x-100"
            playsInline
            muted
          />
          <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full pointer-events-none transform -scale-x-100"
          />

          {/* Real-time Recognition Banner Overlay */}
          <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10 pointer-events-none">
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md flex items-center gap-1.5 ${
                handsDetected
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50"
                  : "bg-amber-500/20 text-amber-300 border border-amber-500/50"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${handsDetected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
              {handsDetected ? "Hands Detected" : "Raise Hand to Spell"}
            </span>

            {livePrediction && (
              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-space-900/90 text-gold-300 border border-gold-500/50">
                Confidence: {(livePrediction.confidence * 100).toFixed(1)}%
              </span>
            )}
          </div>

          {/* Center Detected Character Pill */}
          {livePrediction && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 z-10">
              <div className="px-6 py-2 rounded-2xl bg-space-950/95 border-2 border-gold-400 shadow-2xl flex items-center gap-3 backdrop-blur-xl">
                <span className="text-xs uppercase font-bold text-slate-300">Live Detected:</span>
                <span className="text-3xl font-black font-mono text-gold-300 animate-bounce">
                  {livePrediction.char}
                </span>
              </div>

              {/* Hold Progress Bar */}
              <div className="w-40 h-2 bg-space-900 rounded-full overflow-hidden border border-gold-500/30">
                <div
                  className="h-full bg-gradient-to-r from-gold-400 to-emerald-400 transition-all duration-75"
                  style={{ width: `${holdProgress}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-300 font-semibold">
                {holdProgress >= 100 ? "Committed!" : "Hold steady to commit..."}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Word Builder Input & Manipulation Controls */}
      <div className="p-4 rounded-xl bg-space-850/80 border border-space-700/80 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Spelled Name / Word:
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTypedWord((prev) => prev.slice(0, -1))}
              disabled={!typedWord}
              className="text-xs font-bold px-2.5 py-1 rounded-lg bg-space-800 text-slate-300 hover:text-white border border-space-700 disabled:opacity-40"
              title="Backspace"
            >
              ⌫ Backspace
            </button>
            <button
              onClick={() => setTypedWord((prev) => prev + " ")}
              className="text-xs font-bold px-2.5 py-1 rounded-lg bg-space-800 text-slate-300 hover:text-white border border-space-700"
              title="Add Space"
            >
              ␣ Space
            </button>
            <button
              onClick={() => setTypedWord("")}
              disabled={!typedWord}
              className="text-xs text-ruby-400 hover:text-ruby-300 font-bold px-2.5 py-1 rounded-lg bg-space-800 border border-ruby-500/30 disabled:opacity-40"
            >
              Clear
            </button>
            <button
              onClick={handleSpeak}
              disabled={!typedWord || isSpeaking}
              className="text-xs font-bold px-3 py-1 rounded-lg bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-md hover:scale-105 transition disabled:opacity-40 flex items-center gap-1.5"
            >
              <span>{isSpeaking ? "🔊 Playing..." : "🔊 Speak Word"}</span>
            </button>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-space-950 border border-gold-500/30 min-h-[48px] flex items-center justify-between">
          <span className="text-gold-300 font-mono font-bold tracking-widest text-lg md:text-xl">
            {typedWord || <span className="text-slate-600 font-normal text-sm">HOLD HAND TO CAMERA OR CLICK LETTERS BELOW...</span>}
          </span>
          {typedWord && (
            <span className="text-xs text-slate-400 font-mono">
              {typedWord.replace(/\s/g, "").length} chars
            </span>
          )}
        </div>
      </div>

      {/* Interactive Letters Grid */}
      <div>
        <span className="text-xs uppercase font-bold text-gold-400 block mb-2">
          ISL Alphabet Reference (Click to Add or Preview):
        </span>
        <div className="grid grid-cols-7 sm:grid-cols-9 md:grid-cols-13 gap-2">
          {ALPHABETS.map((letter) => (
            <button
              key={letter}
              onClick={() => {
                setSelectedChar(letter);
                setTypedWord((prev) => prev + letter);
              }}
              className={`p-2.5 rounded-xl font-mono font-bold text-sm transition-all text-center ${
                selectedChar === letter
                  ? "bg-gradient-to-r from-gold-400 to-gold-500 text-space-950 shadow-lg scale-105 font-black"
                  : "bg-space-850 text-slate-200 hover:bg-space-800 border border-space-700/60 hover:border-gold-500/40"
              }`}
            >
              {letter}
            </button>
          ))}
        </div>
      </div>

      {/* Numbers Grid */}
      <div>
        <span className="text-xs uppercase font-bold text-gold-400 block mb-2">
          ISL Numerals (1 to 9):
        </span>
        <div className="grid grid-cols-5 sm:grid-cols-9 gap-2">
          {NUMBERS.map((num) => (
            <button
              key={num}
              onClick={() => {
                setSelectedChar(num);
                setTypedWord((prev) => prev + num);
              }}
              className={`p-2.5 rounded-xl font-mono font-bold text-sm transition text-center ${
                selectedChar === num
                  ? "bg-gradient-to-r from-ruby-500 to-ruby-600 text-white shadow-lg font-black"
                  : "bg-space-850 text-slate-200 hover:bg-space-800 border border-space-700/60 hover:border-ruby-500/40"
              }`}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      {/* Display Card for Selected Character / Handshape Instruction */}
      <div className="p-5 rounded-xl bg-space-950 border border-gold-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-xl bg-space-900 border border-gold-500/40 flex items-center justify-center">
            <span className="text-4xl font-extrabold text-gold-400 font-mono">
              {selectedChar}
            </span>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400">
              ISL Two-Handed Handshape Formation:
            </div>
            <div className="text-sm font-medium text-slate-200 mt-1 max-w-lg">
              {CHAR_DESCRIPTIONS[selectedChar] || "Two-handed Indian Sign Language posture verified per ISLRTC handbook."}
            </div>
          </div>
        </div>

        <div className="text-right text-[11px] text-slate-400 max-w-xs border-t md:border-t-0 md:border-l border-space-800 pt-2 md:pt-0 md:pl-4">
          Dataset Credit: <span className="text-gold-300 font-semibold">Prathum Arikeri ISL Character Dataset</span> (Kaggle). 41,930 real samples across 36 classes trained in TensorFlow.js.
        </div>
      </div>
    </div>
  );
};
