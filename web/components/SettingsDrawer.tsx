"use client";

import React from "react";
import { Settings, X, Volume2, Eye, Sliders, Shield } from "lucide-react";

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  autoSpeak: boolean;
  onToggleAutoSpeak: () => void;
  speechRate: number;
  onChangeSpeechRate: (rate: number) => void;
  highContrast: boolean;
  onToggleHighContrast: () => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  isOpen,
  onClose,
  autoSpeak,
  onToggleAutoSpeak,
  speechRate,
  onChangeSpeechRate,
  highContrast,
  onToggleHighContrast,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-sm h-full bg-space-900 border-l border-gold-500/30 p-6 flex flex-col justify-between shadow-2xl relative">
        {/* Glow Line */}
        <div className="absolute top-0 left-0 bottom-0 w-1 bg-gradient-to-b from-gold-500 via-ruby-500 to-white" />

        <div>
          <div className="flex items-center justify-between pb-4 border-b border-space-800 mb-6">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gold-500/20 text-gold-400 flex items-center justify-center border border-gold-500/30">
                <Settings className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-white">Accessibility & Audio</h3>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-space-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-col gap-6">
            {/* Auto-Speak Toggle */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Volume2 className="w-4 h-4 text-gold-400" />
                  Auto-Speak Translation
                </label>
                <span className="text-xs text-slate-400">Play spoken synthesis immediately</span>
              </div>
              <button
                onClick={onToggleAutoSpeak}
                className={`w-12 h-6 rounded-full transition-colors p-1 ${
                  autoSpeak ? "bg-gradient-to-r from-gold-400 to-gold-500" : "bg-space-800"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-space-950 transition-transform ${
                    autoSpeak ? "translate-x-6" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Speech Rate Slider */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-gold-400" />
                  Voice Speech Speed
                </label>
                <span className="text-xs font-mono text-gold-400 font-bold">{speechRate.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.75"
                max="1.5"
                step="0.05"
                value={speechRate}
                onChange={(e) => onChangeSpeechRate(parseFloat(e.target.value))}
                className="w-full accent-gold-400 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>0.75x (Slow)</span>
                <span>1.0x (Normal)</span>
                <span>1.5x (Fast)</span>
              </div>
            </div>

            {/* High Contrast Mode */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Eye className="w-4 h-4 text-ruby-400" />
                  High Contrast (WCAG AAA)
                </label>
                <span className="text-xs text-slate-400">Boost text borders and luminance</span>
              </div>
              <button
                onClick={onToggleHighContrast}
                className={`w-12 h-6 rounded-full transition-colors p-1 ${
                  highContrast ? "bg-ruby-500" : "bg-space-800"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    highContrast ? "translate-x-6" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-space-800 text-[11px] text-slate-400 flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Config stored locally in Prisma DB SQLite session.</span>
        </div>
      </div>
    </div>
  );
};
