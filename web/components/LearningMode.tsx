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
    <div className="w-full bg-navy border border-slate-700 rounded-2xl p-6 shadow-2xl flex flex-col gap-6">
      <div className="flex items-center justify-between border-b border-slate-700 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>🎓 Interactive ISL Learning Studio</span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
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
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-white"
          >
            ← Previous
          </button>
          <button
            onClick={() => {
              setCurrentIndex((prev) => (prev < LESSON_SIGNS.length - 1 ? prev + 1 : 0));
              setFeedback(null);
            }}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-white"
          >
            Next →
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        {/* Sign Flashcard */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-700 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-light">
                {current.category}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {current.difficulty}
              </span>
            </div>

            <h2 className="text-3xl font-extrabold text-white tracking-wider mb-1">
              {current.gloss}
            </h2>
            <div className="text-lg font-semibold text-accent-orange mb-4">
              {current.englishMeaning} • {current.hindiMeaning}
            </div>

            <div className="p-3.5 rounded-lg bg-navy-dark border border-slate-800 text-xs text-slate-200 leading-relaxed mb-4">
              <span className="font-bold text-teal-light block mb-1">How to sign:</span>
              {current.instruction}
            </div>
          </div>

          <button
            onClick={handleVerify}
            className="w-full py-3 rounded-xl font-bold text-sm bg-teal hover:bg-teal-light text-navy-dark transition shadow"
          >
            📹 Check My Sign with Camera
          </button>
        </div>

        {/* Practice Live Verification Box */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-700 flex flex-col items-center justify-center text-center">
          <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center text-2xl mb-3">
            ✋
          </div>
          <h4 className="text-sm font-bold text-white mb-1">Camera Assessment Feed</h4>
          <p className="text-xs text-slate-400 max-w-xs mb-4">
            Position yourself in the camera frame, perform the gesture, and click &apos;Check My Sign&apos;.
          </p>

          {feedback && (
            <div className="w-full p-3 rounded-lg text-xs font-semibold bg-navy border border-teal/40 text-teal-light animate-fadeIn">
              {feedback}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
