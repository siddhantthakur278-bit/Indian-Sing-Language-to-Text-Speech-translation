"use client";

import React from "react";

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
      <label htmlFor="lang-select" className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
        Target:
      </label>
      <select
        id="lang-select"
        value={selectedCode}
        onChange={(e) => onChange(e.target.value)}
        className="bg-navy-light text-white text-sm font-medium border border-slate-700 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal cursor-pointer shadow-inner"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-navy text-white">
            {lang.name} ({lang.nativeName})
          </option>
        ))}
      </select>
    </div>
  );
};
