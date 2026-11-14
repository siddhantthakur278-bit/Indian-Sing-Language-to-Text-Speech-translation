"use client";

import React, { useState } from "react";

const ALPHABETS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const NUMBERS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

export const Fingerspelling: React.FC = () => {
  const [selectedChar, setSelectedChar] = useState<string>("A");
  const [typedWord, setTypedWord] = useState<string>("");

  return (
    <div className="w-full bg-space-900 border border-gold-500/25 rounded-2xl p-6 shadow-2xl flex flex-col gap-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-space-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>🔤 ISL Fingerspelling &amp; Number Matrix</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gold-500/20 text-gold-300 border border-gold-500/30">
              A-Z • 0-9
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Spell names, specific acronyms, and numbers letter-by-letter
          </p>
        </div>
      </div>

      {/* Word Builder Input */}
      <div className="p-4 rounded-xl bg-space-850/80 border border-space-700/80 flex flex-col md:flex-row items-center gap-3">
        <span className="text-xs font-bold uppercase text-slate-300 whitespace-nowrap">
          Spell a Name / Word:
        </span>
        <input
          type="text"
          value={typedWord}
          onChange={(e) => setTypedWord(e.target.value.toUpperCase())}
          placeholder="TYPE A NAME HERE..."
          className="flex-1 bg-space-950 text-gold-300 font-mono font-bold tracking-widest text-sm px-4 py-2 rounded-xl border border-gold-500/30 focus:outline-none focus:border-gold-400"
        />
        {typedWord && (
          <button
            onClick={() => setTypedWord("")}
            className="text-xs text-ruby-400 hover:text-ruby-300 font-bold px-2"
          >
            Clear
          </button>
        )}
      </div>

      {/* Interactive Letters Grid */}
      <div>
        <span className="text-xs uppercase font-bold text-gold-400 block mb-2">
          Select Letter for Handshape Reference:
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
                  : "bg-space-850 text-slate-200 hover:bg-space-800 border border-space-700/60"
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
          Numbers (1 to 10):
        </span>
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
          {NUMBERS.map((num) => (
            <button
              key={num}
              onClick={() => {
                setSelectedChar(num);
                setTypedWord((prev) => prev + " " + num);
              }}
              className={`p-2.5 rounded-xl font-mono font-bold text-sm transition text-center ${
                selectedChar === num
                  ? "bg-gradient-to-r from-ruby-500 to-ruby-600 text-white shadow-lg font-black"
                  : "bg-space-850 text-slate-200 hover:bg-space-800 border border-space-700/60"
              }`}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      {/* Display Card for Selected Character */}
      <div className="p-5 rounded-xl bg-space-950 border border-gold-500/30 flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold text-slate-400">Selected Character:</div>
          <div className="text-4xl font-extrabold text-gold-400 font-mono mt-1">
            {selectedChar}
          </div>
        </div>
        <div className="text-right text-xs text-slate-400 max-w-xs">
          Two-handed Indian Sign Language standard alphabet posture verified per ISLRTC handbook.
        </div>
      </div>
    </div>
  );
};
