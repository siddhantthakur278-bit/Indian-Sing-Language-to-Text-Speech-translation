"use client";

import React from "react";

interface CaptionPanelProps {
  glosses: string[];
  englishSentence: string;
  translatedSentence: string;
  targetLangName: string;
  isTranslating: boolean;
  onClear: () => void;
  onDeleteLastGloss: () => void;
  onSpeak: () => void;
  isSpeaking: boolean;
}

export const CaptionPanel: React.FC<CaptionPanelProps> = ({
  glosses,
  englishSentence,
  translatedSentence,
  targetLangName,
  isTranslating,
  onClear,
  onDeleteLastGloss,
  onSpeak,
  isSpeaking,
}) => {
  return (
    <div className="flex flex-col gap-5 p-6 rounded-2xl bg-navy border border-slate-700 shadow-xl">
      {/* 1. Gloss Sequence Row */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-bold text-slate-400">
            Detected Gloss Sequence
          </span>
          {glosses.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                onClick={onDeleteLastGloss}
                className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
                title="Remove last sign"
              >
                ⌫ Backspace
              </button>
              <button
                onClick={onClear}
                className="text-xs text-alert-red hover:underline ml-2"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        <div className="min-h-[48px] p-2.5 rounded-xl bg-slate-900/60 border border-slate-700/60 flex flex-wrap gap-2 items-center">
          {glosses.length === 0 ? (
            <span className="text-sm text-slate-500 italic">
              Perform signs in front of the camera to detect glosses...
            </span>
          ) : (
            glosses.map((g, idx) => (
              <span
                key={`${g}-${idx}`}
                className="px-3 py-1 rounded-lg text-sm font-semibold tracking-wide bg-navy-light text-teal-light border border-teal/30 shadow-sm"
              >
                {g}
              </span>
            ))
          )}
        </div>
      </div>

      {/* 2. English Natural Sentence */}
      <div>
        <span className="text-xs uppercase tracking-wider font-bold text-slate-400 mb-1 block">
          Natural English Sentence
        </span>
        <div className="min-h-[56px] p-3 rounded-xl bg-slate-900/40 border border-slate-700/50 flex items-center">
          <p className="text-xl md:text-2xl font-medium text-white leading-relaxed">
            {englishSentence || (
              <span className="text-slate-500 text-base font-normal">
                Natural sentence will appear automatically when hands lower...
              </span>
            )}
          </p>
        </div>
      </div>

      {/* 3. Translated Sentence Card */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-teal/10 to-transparent border-l-4 border-teal bg-slate-900/60">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs uppercase tracking-wider font-bold text-teal-light">
            Translation ({targetLangName})
          </span>
          {isTranslating && (
            <span className="text-xs text-amber-400 animate-pulse">Translating...</span>
          )}
        </div>
        <p className="text-2xl md:text-3xl font-bold text-accent-orange leading-relaxed tracking-wide min-h-[44px]">
          {translatedSentence || "..."}
        </p>
      </div>

      {/* 4. Action Buttons */}
      <div className="flex items-center gap-3 pt-2">
        <button
          onClick={onSpeak}
          disabled={!translatedSentence || isSpeaking}
          className={`flex-1 py-3 px-6 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all duration-200 shadow-lg ${
            isSpeaking
              ? "bg-amber-500 text-navy-dark animate-pulse"
              : translatedSentence
              ? "bg-accent-orange hover:bg-orange-600 text-white cursor-pointer"
              : "bg-slate-800 text-slate-500 cursor-not-allowed"
          }`}
        >
          <span>{isSpeaking ? "🔊 Speaking..." : "🔊 Speak Sentence"}</span>
        </button>

        <button
          onClick={onClear}
          className="py-3 px-6 rounded-xl font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
        >
          Clear
        </button>
      </div>
    </div>
  );
};
