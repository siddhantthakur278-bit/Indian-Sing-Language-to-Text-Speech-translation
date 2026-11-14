"use client";

import React, { useState } from "react";

interface ChatMessage {
  id: string;
  sender: "signer" | "hearing";
  text: string;
  glosses?: string[];
  time: string;
}

interface TwoWayChatProps {
  onSpeak: (text: string) => void;
}

export const TwoWayChat: React.FC<TwoWayChatProps> = ({ onSpeak }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      sender: "signer",
      text: "I am going to the hospital.",
      glosses: ["ME", "HOSPITAL", "GO"],
      time: "12:01",
    },
    {
      id: "2",
      sender: "hearing",
      text: "Okay. Which doctor do you need to see?",
      glosses: ["OKAY", "WHICH", "DOCTOR", "SEE"],
      time: "12:02",
    },
    {
      id: "3",
      sender: "signer",
      text: "Heart doctor, please.",
      glosses: ["DOCTOR", "HEART", "PLEASE"],
      time: "12:02",
    },
    {
      id: "4",
      sender: "hearing",
      text: "Room 12, second floor.",
      glosses: ["ROOM", "TWELVE", "FLOOR", "TWO"],
      time: "12:03",
    },
  ]);

  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);

  // Web Speech Recognition for hearing user
  const startSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome/Edge or type directly.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      const speechResult = event.results[0][0].transcript;
      setInputText(speechResult);
      handleSendHearingMessage(speechResult);
    };

    recognition.start();
  };

  const handleSendHearingMessage = async (textToSend: string) => {
    if (!textToSend.trim()) return;

    try {
      const res = await fetch("/api/text-to-gloss", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToSend }),
      });
      const data = await res.json();

      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;

      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          sender: "hearing",
          text: textToSend,
          glosses: data.glosses || ["HELLO"],
          time: timeStr,
        },
      ]);
      setInputText("");
    } catch (e) {
      console.error("Text-to-gloss error:", e);
    }
  };

  return (
    <div className="w-full flex flex-col h-[560px] bg-space-900 border border-gold-500/25 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
      {/* Header */}
      <div className="p-4 bg-space-950 border-b border-space-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <span>💬 Two-Way Communication Bridge</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gold-500/20 text-gold-300 border border-gold-500/30">
              Deaf ↔ Hearing
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Signer signs via camera • Hearing partner speaks into microphone
          </p>
        </div>
      </div>

      {/* Message Transcript */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3.5 bg-space-950/60">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col max-w-[80%] ${
              m.sender === "signer" ? "self-start items-start" : "self-end items-end"
            }`}
          >
            <div className="text-[10px] font-mono text-slate-400 mb-1 px-1">
              {m.sender === "signer" ? "🖐️ Deaf Signer" : "🗣️ Hearing Partner"} • {m.time}
            </div>
            <div
              className={`p-3.5 rounded-2xl text-sm ${
                m.sender === "signer"
                  ? "bg-space-850 text-white border border-gold-500/30 rounded-tl-sm shadow"
                  : "bg-ruby-950/60 text-white border border-ruby-500/40 rounded-tr-sm shadow"
              }`}
            >
              <p className="font-medium">{m.text}</p>
              {m.glosses && m.glosses.length > 0 && (
                <div className="mt-2 pt-2 border-t border-space-700/60 flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] font-bold uppercase text-gold-400">ISL Glosses:</span>
                  {m.glosses.map((g, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-space-950 text-gold-300 border border-gold-500/30"
                    >
                      {g}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Hearing User Speech Input Bar */}
      <div className="p-3.5 bg-space-950 border-t border-space-800 flex items-center gap-2">
        <button
          onClick={startSpeechRecognition}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition shadow ${
            isListening
              ? "bg-ruby-500 text-white animate-pulse"
              : "bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 text-space-950"
          }`}
          title="Click to speak using microphone"
        >
          <span>{isListening ? "🔴 Listening..." : "🎤 Speak into Mic"}</span>
        </button>

        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSendHearingMessage(inputText);
          }}
          placeholder="Hearing user types or speaks here..."
          className="flex-1 bg-space-850 text-white text-xs px-3.5 py-2.5 rounded-xl border border-space-700 focus:outline-none focus:border-gold-500"
        />

        <button
          onClick={() => handleSendHearingMessage(inputText)}
          className="px-4 py-2.5 rounded-xl bg-space-800 hover:bg-space-700 text-gold-300 text-xs font-bold transition border border-space-700 hover:border-gold-500/40"
        >
          Send
        </button>
      </div>
    </div>
  );
};
