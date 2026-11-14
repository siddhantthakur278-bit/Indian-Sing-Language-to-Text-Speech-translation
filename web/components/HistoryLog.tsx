"use client";

import React, { useState } from "react";
import { Clock, Copy, Check, Bookmark, Database, Trash2 } from "lucide-react";

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
  onBookmark?: (item: HistoryItem) => void;
}

export const HistoryLog: React.FC<HistoryLogProps> = ({ items, onClear, onBookmark }) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1800);
  };

  return (
    <div className="p-5 rounded-2xl bg-space-900 border border-gold-500/20 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-gold-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            Translation History
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-space-850 text-gold-400 border border-gold-500/30">
              Prisma DB
            </span>
          </h4>
        </div>

        {items.length > 0 && (
          <button
            onClick={onClear}
            className="text-[11px] font-semibold text-slate-400 hover:text-ruby-400 flex items-center gap-1 transition"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="text-xs text-slate-400 italic py-3 text-center">
          Recognized sentences will be automatically archived into your database here.
        </p>
      ) : (
        <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
          {items.map((item) => (
            <div
              key={item.id}
              className={`p-3 rounded-xl border text-xs flex items-center justify-between gap-3 transition ${
                item.isEmergency
                  ? "bg-ruby-950/40 border-ruby-500/50 text-ruby-100 shadow-sm"
                  : "bg-space-850/80 hover:bg-space-800 border-space-700/60 hover:border-gold-500/30 text-slate-200"
              }`}
            >
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-slate-400">{item.time}</span>
                  {item.isEmergency && (
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-ruby-600 text-white">
                      EMERGENCY
                    </span>
                  )}
                  <span className="font-semibold text-white truncate">{item.english}</span>
                </div>
                <span className="text-gold-300 font-bold mt-1 text-[13px]">{item.translated}</span>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                {onBookmark && (
                  <button
                    onClick={() => onBookmark(item)}
                    className="p-1.5 rounded-lg bg-space-900 text-slate-400 hover:text-gold-400 border border-space-700 hover:border-gold-500/40 transition"
                    title="Bookmark phrase to database"
                  >
                    <Bookmark className="w-3.5 h-3.5" />
                  </button>
                )}

                <button
                  onClick={() => copyToClipboard(item.id, item.translated)}
                  className="px-2 py-1 rounded-lg bg-space-900 text-slate-300 hover:text-white border border-space-700 hover:border-gold-500/40 text-[11px] font-medium flex items-center gap-1 transition"
                  title="Copy translation"
                >
                  {copiedId === item.id ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
