"use client";

import React, { useState } from "react";
import { AlertCircle, ChevronDown, ChevronUp, Siren } from "lucide-react";

interface EmergencyBarProps {
  onTriggerEmergency: (phrase: string, translationHi: string) => void;
}

export const EMERGENCY_PHRASES = [
  { text: "Please help me immediately!", hi: "कृपया तुरंत मेरी मदद करें!", code: "HELP" },
  { text: "I need a doctor urgently.", hi: "मुझे तत्काल डॉक्टर की आवश्यकता है।", code: "DOCTOR" },
  { text: "Call an ambulance!", hi: "कृपया तुरंत एम्बुलेंस को कॉल करें!", code: "AMBULANCE" },
  { text: "Call the police now!", hi: "कृपया तुरंत पुलिस को बुलाएं!", code: "POLICE" },
  { text: "I am in severe pain.", hi: "मुझे बहुत तेज असहनीय दर्द हो रहा है।", code: "PAIN" },
  { text: "I am deaf, please read this.", hi: "मैं मूक-बधिर हूँ, कृपया यह पढ़ें।", code: "DEAF" },
];

export const EmergencyBar: React.FC<EmergencyBarProps> = ({ onTriggerEmergency }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="w-full">
      {/* Quick SOS Trigger Button */}
      <div className="flex items-center justify-between p-3 px-4 rounded-xl bg-ruby-950/40 border border-ruby-500/40 shadow-lg backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center">
            <span className="w-3 h-3 rounded-full bg-ruby-500 animate-ping absolute" />
            <span className="w-2.5 h-2.5 rounded-full bg-ruby-500" />
          </div>
          <span className="text-xs md:text-sm font-extrabold text-ruby-300 uppercase tracking-wider flex items-center gap-1.5">
            <Siren className="w-4 h-4 text-ruby-400" />
            Emergency SOS Priority Mode
          </span>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-xs font-bold px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-ruby-600 to-ruby-500 hover:from-ruby-500 hover:to-ruby-600 text-white transition shadow-md flex items-center gap-1.5"
        >
          <span>{isOpen ? "Hide Emergency Phrases" : "Open Emergency Phrases"}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Expanded Emergency Buttons */}
      {isOpen && (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 p-4 rounded-xl bg-ruby-950/20 border border-ruby-500/30 animate-fadeIn">
          {EMERGENCY_PHRASES.map((phrase) => (
            <button
              key={phrase.code}
              onClick={() => onTriggerEmergency(phrase.text, phrase.hi)}
              className="p-3 text-left rounded-xl bg-gradient-to-br from-ruby-700 to-ruby-900 hover:from-ruby-600 hover:to-ruby-800 text-white font-bold text-xs transition active:scale-95 shadow-md border border-ruby-400/40 flex flex-col justify-between group"
            >
              <span className="group-hover:text-gold-200 transition">{phrase.text}</span>
              <span className="text-[11px] font-normal text-ruby-200 mt-1">{phrase.hi}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
