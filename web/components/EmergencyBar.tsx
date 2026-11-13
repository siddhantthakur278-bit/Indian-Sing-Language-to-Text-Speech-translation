"use client";

import React, { useState } from "react";

interface EmergencyBarProps {
  onTriggerEmergency: (phrase: string, translationHi: string) => void;
}

export const EMERGENCY_PHRASES = [
  { text: "Please help me!", hi: "कृपया मेरी मदद करें!", code: "HELP" },
  { text: "I need a doctor.", hi: "मुझे एक डॉक्टर की जरूरत है।", code: "DOCTOR" },
  { text: "Call an ambulance!", hi: "कृपया एम्बुलेंस को कॉल करें!", code: "AMBULANCE" },
  { text: "Call the police!", hi: "कृपया तुरंत पुलिस को बुलाएं!", code: "POLICE" },
  { text: "I am in severe pain.", hi: "मुझे बहुत तेज दर्द हो रहा है।", code: "PAIN" },
];

export const EmergencyBar: React.FC<EmergencyBarProps> = ({ onTriggerEmergency }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="w-full">
      {/* Quick SOS Trigger Button */}
      <div className="flex items-center justify-between p-3 px-4 rounded-xl bg-alert-red/10 border border-alert-red/30">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-alert-red animate-ping" />
          <span className="text-sm font-bold text-alert-red uppercase tracking-wider">
            Emergency Mode (Fixed Safety Templates)
          </span>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-xs font-semibold px-3 py-1 rounded-lg bg-alert-red text-white hover:bg-red-700 transition shadow"
        >
          {isOpen ? "Hide Quick SOS" : "Open Emergency Phrases"}
        </button>
      </div>

      {/* Expanded Emergency Buttons */}
      {isOpen && (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 p-4 rounded-xl bg-alert-red/5 border border-alert-red/40 animate-fadeIn">
          {EMERGENCY_PHRASES.map((phrase) => (
            <button
              key={phrase.code}
              onClick={() => onTriggerEmergency(phrase.text, phrase.hi)}
              className="p-3 text-left rounded-xl bg-alert-red hover:bg-red-700 text-white font-bold text-sm transition-transform active:scale-95 shadow-md flex flex-col justify-between"
            >
              <span>{phrase.text}</span>
              <span className="text-xs font-normal opacity-90 mt-1">{phrase.hi}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
