"use client";

import React from "react";

export interface HistoryItem {
  id: string;
  time: string;
  english: string;
  translated: string;
  lang: string;
  isEmergency?: boolean;
}

interface HistoryLogProps {
  items: HistoryItem[];
  onClear: () => void;
}

export const HistoryLog: React.FC<HistoryLogProps> = ({ items, onClear }) => {
  const copyToClipboard = (text: string) => {
    navigator.clipboard?.writeText(text);
  };

  return (
    <div className="p-5 rounded-2xl bg-navy border border-slate-700 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Recent Translation History
        </h4>
        {items.length > 0 && (
          <button
            onClick={onClear}
            className="text-xs text-slate-400 hover:text-alert-red transition"
          >
            Clear All
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="text-xs text-slate-500 italic py-2">
          Recognized sentences will be automatically archived here.
        </p>
      ) : (
        <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
          {items.map((item) => (
            <div
              key={item.id}
              className={`p-2.5 rounded-xl border text-xs flex items-center justify-between gap-3 ${
                item.isEmergency
                  ? "bg-alert-red/10 border-alert-red/40 text-red-200"
                  : "bg-slate-900/50 border-slate-700 text-slate-300"
              }`}
            >
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-slate-400">{item.time}</span>
                  <span className="font-medium text-white">{item.english}</span>
                </div>
                <span className="text-teal-light font-semibold mt-0.5">{item.translated}</span>
              </div>
              <button
                onClick={() => copyToClipboard(item.translated)}
                className="text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800 text-[10px]"
                title="Copy translation"
              >
                Copy
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
