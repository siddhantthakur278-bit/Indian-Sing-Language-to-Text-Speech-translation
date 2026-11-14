"use client";

import React, { useState } from "react";
import { Volume2, VolumeX, Sparkles, Bookmark, Check, Trash2, ArrowRight } from "lucide-react";
import { AudioWaveform } from "@/components/AudioWaveform";

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
  onBookmarkSentence?: (english: string, translated: string, glosses: string[]) => void;
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
  onBookmarkSentence,
}) => {
  const [bookmarked, setBookmarked] = useState(false);

  const handleBookmark = () => {
    if (!englishSentence || !translatedSentence) return;
    if (onBookmarkSentence) {
      onBookmarkSentence(englishSentence, translatedSentence, glosses);
      setBookmarked(true);
      setTimeout(() => setBookmarked(false), 2000);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-5 md:p-6 rounded-2xl bg-space-900 border border-gold-500/25 shadow-2xl backdrop-blur-xl">
      {/* 1. Gloss Sequence Row */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider font-extrabold text-gold-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-gold-400 animate-sparkle" />
            Detected Gloss Sequence
          </span>
          {glosses.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                onClick={onDeleteLastGloss}
                className="text-xs font-semibold text-slate-400 hover:text-white transition-colors"
                title="Remove last sign"
              >
                ⌫ Backspace
              </button>
              <button
                onClick={onClear}
                className="text-xs font-semibold text-ruby-400 hover:text-ruby-300 ml-1"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        <div className="min-h-[48px] p-2.5 rounded-xl bg-space-850 border border-space-700/80 flex flex-wrap gap-2 items-center">
          {glosses.length === 0 ? (
            <span className="text-xs text-slate-400 italic">
              Perform ISL signs before the camera. Recognized glosses stream here...
            </span>
          ) : (
            glosses.map((g, idx) => (
              <span
                key={`${g}-${idx}`}
                className="px-3 py-1 rounded-lg text-xs font-extrabold tracking-wider bg-space-950 text-gold-300 border border-gold-500/40 shadow-sm animate-fadeIn"
              >
                {g}
              </span>
            ))
          )}
        </div>
      </div>

      {/* 2. English Natural Sentence */}
      <div>
        <span className="text-xs uppercase tracking-wider font-extrabold text-slate-400 mb-1.5 block">
          Natural English Sentence
        </span>
        <div className="min-h-[52px] p-3.5 rounded-xl bg-space-850/80 border border-space-700/60 flex items-center">
          <p className="text-lg md:text-xl font-semibold text-white leading-relaxed">
            {englishSentence || (
              <span className="text-slate-500 text-sm font-normal">
                Natural sentence reconstructs automatically when hands lower or space is released...
              </span>
            )}
          </p>
        </div>
      </div>

      {/* 3. Translated Sentence Card */}
      <div className="relative p-4 md:p-5 rounded-xl bg-gradient-to-r from-gold-500/10 via-ruby-500/10 to-transparent border-l-4 border-gold-400 bg-space-850/90 border border-space-700/80 shadow-lg overflow-hidden">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs uppercase tracking-wider font-extrabold text-gold-300 flex items-center gap-1.5">
            <span>Translation</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-space-950 text-white border border-gold-500/30">
              {targetLangName}
            </span>
          </span>
          {isTranslating && (
            <span className="text-xs font-bold text-gold-400 animate-pulse flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-gold-400 animate-ping" />
              Synthesizing...
            </span>
          )}
        </div>

        <p className="text-2xl md:text-3xl font-extrabold text-white leading-relaxed tracking-wide min-h-[48px] py-1">
          {translatedSentence || "..."}
        </p>

        {/* Action Controls for Translation */}
        <div className="mt-3 pt-3 border-t border-space-700/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={onSpeak}
              disabled={!translatedSentence || isSpeaking}
              className={`px-4 py-2 rounded-xl font-bold text-xs flex items-center gap-2 transition shadow-md ${
                isSpeaking
                  ? "bg-ruby-500 text-white animate-pulse"
                  : translatedSentence
                  ? "bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 text-space-950"
                  : "bg-space-800 text-slate-500 cursor-not-allowed"
              }`}
            >
              <Volume2 className="w-4 h-4" />
              <span>{isSpeaking ? "Speaking..." : "Speak Translation (S)"}</span>
            </button>

            {/* Live Audio Equalizer Waveform */}
            <AudioWaveform isActive={isSpeaking} />

            {translatedSentence && (
              <button
                onClick={handleBookmark}
                className="px-3 py-2 rounded-xl text-xs font-semibold bg-space-950 hover:bg-space-800 text-slate-200 border border-space-700 hover:border-gold-500/40 transition flex items-center gap-1.5"
                title="Bookmark to Prisma Database"
              >
                {bookmarked ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Saved</span>
                  </>
                ) : (
                  <>
                    <Bookmark className="w-3.5 h-3.5 text-gold-400" />
                    <span>Bookmark</span>
                  </>
                )}
              </button>
            )}
          </div>

          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Shortcuts: <kbd className="px-1 py-0.5 rounded bg-space-950 border border-space-700 text-gold-300 font-mono">S</kbd> Speak &bull; <kbd className="px-1 py-0.5 rounded bg-space-950 border border-space-700 text-ruby-300 font-mono">C</kbd> Clear
          </span>
        </div>
      </div>
    </div>
  );
};
