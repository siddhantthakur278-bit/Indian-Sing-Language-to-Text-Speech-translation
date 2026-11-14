"use client";

import React from "react";
import { Globe } from "lucide-react";

export interface LanguageOption {
  code: string;
  name: string;
  nativeName: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "hi", name: "Hindi", nativeName: "हिन्दी" },
  { code: "mr", name: "Marathi", nativeName: "मराठी" },
  { code: "en", name: "English", nativeName: "English" },
  { code: "ta", name: "Tamil", nativeName: "தமிழ்" },
  { code: "bn", name: "Bengali", nativeName: "বাংলা" },
  { code: "te", name: "Telugu", nativeName: "తెలుగు" },
  { code: "gu", name: "Gujarati", nativeName: "ગુજરાતી" },
  { code: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ" },
  { code: "ml", name: "Malayalam", nativeName: "മലയാളം" },
  { code: "pa", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ" },
];

interface LanguageSelectProps {
  selectedCode: string;
  onChange: (code: string) => void;
}

export const LanguageSelect: React.FC<LanguageSelectProps> = ({ selectedCode, onChange }) => {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1.5 text-gold-400">
        <Globe className="w-4 h-4" />
        <label htmlFor="lang-select" className="text-xs font-bold uppercase tracking-wider text-slate-300 hidden sm:inline">
          Target:
        </label>
      </div>
      <select
        id="lang-select"
        value={selectedCode}
        onChange={(e) => onChange(e.target.value)}
        className="bg-space-850 text-white text-xs font-bold border border-gold-500/30 rounded-xl px-3 py-1.5 focus:outline-none focus:border-gold-400 cursor-pointer shadow-md hover:border-gold-400 transition"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-space-950 text-white font-medium">
            {lang.name} ({lang.nativeName})
          </option>
        ))}
      </select>
    </div>
  );
};
