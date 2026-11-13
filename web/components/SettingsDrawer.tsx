"use client";

import React from "react";

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
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-sm h-full bg-navy border-l border-slate-700 p-6 flex flex-col justify-between shadow-2xl">
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-700 mb-6">
            <h3 className="text-lg font-bold text-white">Accessibility & Settings</h3>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 text-lg font-mono"
            >
              ✕
            </button>
          </div>

          <div className="flex flex-col gap-6">
            {/* Auto-Speak Toggle */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-semibold text-white block">Auto-Speak Sentences</label>
                <span className="text-xs text-slate-400">Play speech automatically on translation</span>
              </div>
              <button
                onClick={onToggleAutoSpeak}
                className={`w-12 h-6 rounded-full transition-colors p-1 ${
                  autoSpeak ? "bg-teal" : "bg-slate-700"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    autoSpeak ? "translate-x-6" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Speech Rate Slider */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-semibold text-white">Voice Speech Rate</label>
                <span className="text-xs font-mono text-teal-light">{speechRate}x</span>
              </div>
              <input
                type="range"
                min="0.75"
                max="1.5"
                step="0.05"
                value={speechRate}
                onChange={(e) => onChangeSpeechRate(parseFloat(e.target.value))}
                className="w-full accent-teal cursor-pointer"
              />
            </div>

            {/* High Contrast Mode */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-semibold text-white block">High Contrast Mode</label>
                <span className="text-xs text-slate-400">Enhance caption and UI readability (WCAG AAA)</span>
              </div>
              <button
                onClick={onToggleHighContrast}
                className={`w-12 h-6 rounded-full transition-colors p-1 ${
                  highContrast ? "bg-teal" : "bg-slate-700"
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

        <div className="text-xs text-slate-500 text-center border-t border-slate-800 pt-4">
          ISL Translator • MoSJE / ISLRTC Initiative
        </div>
      </div>
    </div>
  );
};
