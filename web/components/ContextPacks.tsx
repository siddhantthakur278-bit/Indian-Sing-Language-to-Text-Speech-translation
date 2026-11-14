"use client";

import React, { useState } from "react";

interface ContextPhrase {
  glosses: string[];
  english: string;
  hindi: string;
}

interface ContextPack {
  id: string;
  title: string;
  icon: string;
  phrases: ContextPhrase[];
}

const CONTEXT_PACKS: ContextPack[] = [
  {
    id: "hospital",
    title: "Hospital & Medical",
    icon: "🏥",
    phrases: [
      { glosses: ["DOCTOR", "NEED"], english: "I need a doctor.", hindi: "मुझे डॉक्टर की जरूरत है।" },
      { glosses: ["ME", "PAIN"], english: "I am experiencing pain.", hindi: "मुझे दर्द हो रहा है।" },
      { glosses: ["MEDICINE", "WHERE"], english: "Where is the pharmacy?", hindi: "दवा की दुकान कहाँ है?" },
      { glosses: ["HOSPITAL", "GO", "NEED"], english: "I need to go to the hospital.", hindi: "मुझे अस्पताल जाना है।" },
    ],
  },
  {
    id: "police",
    title: "Police & Security",
    icon: "👮",
    phrases: [
      { glosses: ["POLICE", "CALL", "PLEASE"], english: "Please call the police immediately.", hindi: "कृपया पुलिस को बुलाएं।" },
      { glosses: ["HELP", "ME"], english: "Please help me.", hindi: "कृपया मेरी सहायता करें।" },
      { glosses: ["ACCIDENT", "HELP"], english: "There has been an accident, please help.", hindi: "दुर्घटना हो गई है, मदद करें।" },
    ],
  },
  {
    id: "transit",
    title: "Railway & Transport",
    icon: "🚆",
    phrases: [
      { glosses: ["WHERE", "GO"], english: "Where should I go?", hindi: "कहाँ जाना है?" },
      { glosses: ["TICKET", "BUY", "WHERE"], english: "Where can I buy a ticket?", hindi: "टिकट कहाँ से खरीदें?" },
      { glosses: ["TIME", "WHAT"], english: "What time is it?", hindi: "कितना समय हुआ है?" },
    ],
  },
  {
    id: "daily",
    title: "Daily Needs & Food",
    icon: "🍽️",
    phrases: [
      { glosses: ["FOOD", "WANT"], english: "I want food.", hindi: "मुझे खाना चाहिए।" },
      { glosses: ["WATER", "PLEASE"], english: "Could I please have water?", hindi: "कृपया पानी दीजिए।" },
      { glosses: ["TOILET", "WHERE"], english: "Where is the washroom?", hindi: "शौचालय कहाँ है?" },
    ],
  },
];

interface ContextPacksProps {
  onSelectPhrase: (glosses: string[], english: string, hindi: string) => void;
}

export const ContextPacks: React.FC<ContextPacksProps> = ({ onSelectPhrase }) => {
  const [activePackId, setActivePackId] = useState<string>("hospital");

  const currentPack = CONTEXT_PACKS.find((p) => p.id === activePackId) || CONTEXT_PACKS[0];

  return (
    <div className="w-full bg-space-900 border border-gold-500/25 rounded-2xl p-6 shadow-2xl flex flex-col gap-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-space-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>🎒 Scenario-Based Context Vocabulary Packs</span>
          </h3>
          <p className="text-xs text-slate-400">
            Rapid access to curated domain-specific phrases for hospitals, transport, and emergency desks
          </p>
        </div>
      </div>

      {/* Pack Category Tabs */}
      <div className="flex flex-wrap gap-2">
        {CONTEXT_PACKS.map((pack) => (
          <button
            key={pack.id}
            onClick={() => setActivePackId(pack.id)}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition ${
              activePackId === pack.id
                ? "bg-gradient-to-r from-gold-400 to-gold-500 text-space-950 shadow-md font-extrabold"
                : "bg-space-850 text-slate-300 hover:text-white hover:bg-space-800 border border-space-700"
            }`}
          >
            <span>{pack.icon}</span>
            <span>{pack.title}</span>
          </button>
        ))}
      </div>

      {/* Phrases Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {currentPack.phrases.map((phrase, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl bg-space-850/80 border border-space-700/80 flex flex-col justify-between hover:border-gold-500/40 transition group shadow-sm"
          >
            <div>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {phrase.glosses.map((g, gIdx) => (
                  <span
                    key={gIdx}
                    className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-space-950 text-gold-300 border border-gold-500/30"
                  >
                    {g}
                  </span>
                ))}
              </div>
              <h4 className="text-sm font-bold text-white mb-0.5 group-hover:text-gold-200 transition">{phrase.english}</h4>
              <p className="text-xs text-gold-400 font-semibold">{phrase.hindi}</p>
            </div>

            <button
              onClick={() => onSelectPhrase(phrase.glosses, phrase.english, phrase.hindi)}
              className="mt-3.5 w-full py-2 rounded-lg bg-space-900 group-hover:bg-gradient-to-r group-hover:from-gold-400 group-hover:to-gold-500 group-hover:text-space-950 text-slate-200 text-xs font-bold transition flex items-center justify-center gap-1.5 border border-space-700 group-hover:border-gold-400"
            >
              <span>Use This Phrase</span>
              <span>→</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
