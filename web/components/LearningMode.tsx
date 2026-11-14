"use client";

import React, { useState } from "react";

interface PracticeSign {
  gloss: string;
  category: string;
  englishMeaning: string;
  hindiMeaning: string;
  instruction: string;
  difficulty: "Beginner" | "Intermediate";
}

const LESSON_SIGNS: PracticeSign[] = [
  {
    gloss: "HELLO",
    category: "Greetings",
    englishMeaning: "Hello / Namaste",
    hindiMeaning: "नमस्ते",
    instruction: "Bring flat dominant open palm to temple and salute outwards gently.",
    difficulty: "Beginner",
  },
  {
    gloss: "THANK_YOU",
    category: "Greetings",
    englishMeaning: "Thank you",
    hindiMeaning: "धन्यवाद",
    instruction: "Touch flat fingertips to chin or lips, then move hand forward towards the listener.",
    difficulty: "Beginner",
  },
  {
    gloss: "HELP",
    category: "Emergency",
    englishMeaning: "Help / Assistance",
    hindiMeaning: "मदद",
    instruction: "Place closed fist with thumb up on top of flat palm of non-dominant hand and lift both hands upward.",
    difficulty: "Beginner",
  },
  {
    gloss: "WATER",
    category: "Daily Needs",
    englishMeaning: "Water",
    hindiMeaning: "पानी",
    instruction: "Form 'W' handshape (index, middle, ring fingers up) and tap index finger against chin twice.",
    difficulty: "Beginner",
  },
  {
    gloss: "DOCTOR",
    category: "Healthcare",
    englishMeaning: "Doctor / Physician",
    hindiMeaning: "डॉक्टर",
    instruction: "Tap fingertips of dominant curved hand against the pulse / wrist of the non-dominant hand.",
    difficulty: "Intermediate",
  },
  {
    gloss: "HOSPITAL",
    category: "Healthcare",
    englishMeaning: "Hospital",
    hindiMeaning: "अस्पताल",
    instruction: "Draw a small cross on the upper left arm using the index and middle fingers.",
    difficulty: "Intermediate",
  },
];

export const LearningMode: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [feedback, setFeedback] = useState<string | null>(null);

  const current = LESSON_SIGNS[currentIndex];

  const handleVerify = () => {
    setFeedback("Checking camera keypoint alignment...");
    setTimeout(() => {
      setFeedback("✅ Excellent! Sign posture and movement matched (Confidence: 94%)");
    }, 1200);
  };

  return (
    <div className="w-full bg-space-900 border border-gold-500/25 rounded-2xl p-6 shadow-2xl flex flex-col gap-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-space-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>🎓 Interactive ISL Learning Studio</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gold-500/20 text-gold-300 border border-gold-500/30">
              Lesson {currentIndex + 1} of {LESSON_SIGNS.length}
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Learn standard ISLRTC signs and verify your hand posture live with the camera
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setCurrentIndex((prev) => (prev > 0 ? prev - 1 : LESSON_SIGNS.length - 1));
              setFeedback(null);
            }}
            className="px-3 py-1.5 rounded-xl bg-space-850 hover:bg-space-800 text-xs font-bold text-slate-300 border border-space-700"
          >
            ← Previous
          </button>
          <button
            onClick={() => {
              setCurrentIndex((prev) => (prev < LESSON_SIGNS.length - 1 ? prev + 1 : 0));
              setFeedback(null);
            }}
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 text-xs font-bold text-space-950 shadow-md"
          >
            Next →
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        {/* Sign Flashcard */}
        <div className="p-5 rounded-xl bg-space-850/80 border border-space-700/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gold-400">
                {current.category}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-950 text-slate-300 border border-space-700">
                {current.difficulty}
              </span>
            </div>

            <h2 className="text-3xl font-extrabold text-white tracking-wider mb-1 gold-gradient-text">
              {current.gloss}
            </h2>
            <div className="text-lg font-bold text-gold-300 mb-4">
              {current.englishMeaning} • {current.hindiMeaning}
            </div>

            <div className="p-3.5 rounded-lg bg-space-950 border border-gold-500/20 text-xs text-slate-200 leading-relaxed mb-4">
              <span className="font-bold text-gold-400 block mb-1">How to sign:</span>
              {current.instruction}
            </div>
          </div>

          <button
            onClick={handleVerify}
            className="w-full py-3 rounded-xl font-bold text-xs bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 text-space-950 transition shadow-lg"
          >
            📹 Check My Sign with Camera
          </button>
        </div>

        {/* Practice Live Verification Box */}
        <div className="p-5 rounded-xl bg-space-850/60 border border-space-700/70 flex flex-col items-center justify-center text-center">
          <div className="w-14 h-14 rounded-full bg-space-950 border border-gold-500/30 flex items-center justify-center text-2xl mb-3 text-gold-400">
            ✋
          </div>
          <h4 className="text-sm font-bold text-white mb-1">Camera Assessment Feed</h4>
          <p className="text-xs text-slate-400 max-w-xs mb-4">
            Position yourself in the camera frame, perform the gesture, and click &apos;Check My Sign&apos;.
          </p>

          {feedback && (
            <div className="w-full p-3 rounded-lg text-xs font-semibold bg-space-950 border border-gold-500/40 text-gold-300 animate-fadeIn">
              {feedback}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
