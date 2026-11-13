"use client";

import React, { useState, useEffect, useCallback } from "react";
import { CameraView } from "@/components/CameraView";
import { CaptionPanel } from "@/components/CaptionPanel";
import { LanguageSelect, SUPPORTED_LANGUAGES } from "@/components/LanguageSelect";
import { EmergencyBar } from "@/components/EmergencyBar";
import { HistoryLog, HistoryItem } from "@/components/HistoryLog";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { AriaAnnouncer } from "@/components/AriaAnnouncer";
import { speakText, stopSpeaking } from "@/lib/speech";
import { requestSentenceTranslation } from "@/lib/api";
import { soundEffects } from "@/lib/audioFeedback";

export default function Home() {
  // Application State
  const [isCameraActive, setIsCameraActive] = useState<boolean>(true);
  const [detectedSign, setDetectedSign] = useState<string | null>("HELLO");
  const [confidence, setConfidence] = useState<number>(0.94);
  const [handsDetected, setHandsDetected] = useState<boolean>(true);
  const [fps, setFps] = useState<number>(30);

  // Linguistic & Translation State
  const [targetLang, setTargetLang] = useState<string>("hi");
  const [glosses, setGlosses] = useState<string[]>(["ME", "HOSPITAL", "GO"]);
  const [englishSentence, setEnglishSentence] = useState<string>("I am going to the hospital.");
  const [translatedSentence, setTranslatedSentence] = useState<string>("मैं अस्पताल जा रहा हूँ।");
  const [isTranslating, setIsTranslating] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  // History & Settings
  const [history, setHistory] = useState<HistoryItem[]>([
    {
      id: "h1",
      time: "12:01",
      english: "Hello, how are you?",
      translated: "नमस्ते, आप कैसे हैं?",
      lang: "hi",
    },
    {
      id: "h2",
      time: "12:02",
      english: "Please help me.",
      translated: "कृपया मेरी मदद करें।",
      lang: "hi",
      isEmergency: true,
    },
  ]);

  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [autoSpeak, setAutoSpeak] = useState<boolean>(true);
  const [speechRate, setSpeechRate] = useState<number>(1.0);
  const [highContrast, setHighContrast] = useState<boolean>(false);

  const currentLangObj = SUPPORTED_LANGUAGES.find((l) => l.code === targetLang) || SUPPORTED_LANGUAGES[0];

  // Global keyboard shortcuts for accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is focusing an input or select
      if (["INPUT", "SELECT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        setIsCameraActive((prev) => !prev);
      } else if (e.key === "s" || e.key === "S") {
        handleSpeak();
      } else if (e.key === "c" || e.key === "C") {
        handleClear();
      } else if (e.key === "e" || e.key === "E") {
        handleEmergencyTrigger("Please help me immediately!", "कृपया तुरंत मेरी सहायता करें!");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [translatedSentence, targetLang, speechRate]);
  const triggerTranslation = useCallback(async (currentGlosses: string[], lang: string) => {
    if (currentGlosses.length === 0) return;
    setIsTranslating(true);
    try {
      const res = await requestSentenceTranslation(currentGlosses, lang);
      setEnglishSentence(res.sentence);
      setTranslatedSentence(res.translated);

      // Add to history
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
      setHistory((prev) => [
        {
          id: Math.random().toString(),
          time: timeStr,
          english: res.sentence,
          translated: res.translated,
          lang: res.lang,
          isEmergency: res.emergency,
        },
        ...prev,
      ]);

      if (autoSpeak && res.translated) {
        setIsSpeaking(true);
        speakText(res.translated, res.lang, speechRate, () => setIsSpeaking(false), () => setIsSpeaking(false));
      }
    } catch (err) {
      console.error("Translation request failed:", err);
    } finally {
      setIsTranslating(false);
    }
  }, [autoSpeak, speechRate]);

  // Handle manual speak
  const handleSpeak = () => {
    if (!translatedSentence) return;
    setIsSpeaking(true);
    speakText(
      translatedSentence,
      targetLang,
      speechRate,
      () => setIsSpeaking(false),
      () => setIsSpeaking(false)
    );
  };

  // Handle emergency phrase trigger
  const handleEmergencyTrigger = (phrase: string, translationHi: string) => {
    setGlosses(["HELP", "EMERGENCY"]);
    setEnglishSentence(phrase);
    setTranslatedSentence(translationHi);

    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
    setHistory((prev) => [
      {
        id: Math.random().toString(),
        time: timeStr,
        english: phrase,
        translated: translationHi,
        lang: "hi",
        isEmergency: true,
      },
      ...prev,
    ]);

    setIsSpeaking(true);
    speakText(translationHi, "hi", 1.0, () => setIsSpeaking(false), () => setIsSpeaking(false));
  };

  const handleClear = () => {
    stopSpeaking();
    setGlosses([]);
    setEnglishSentence("");
    setTranslatedSentence("");
    setIsSpeaking(false);
  };

  const handleDeleteLastGloss = () => {
    if (glosses.length > 0) {
      const nextGlosses = glosses.slice(0, -1);
      setGlosses(nextGlosses);
      if (nextGlosses.length > 0) {
        triggerTranslation(nextGlosses, targetLang);
      } else {
        handleClear();
      }
    }
  };

  return (
    <div className={`min-h-screen flex flex-col justify-between ${highContrast ? "contrast-125" : ""}`}>
      {/* Top Navigation Bar */}
      <header className="w-full bg-navy border-b border-slate-700/80 px-4 md:px-8 py-3.5 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-teal to-accent-orange flex items-center justify-center font-black text-navy-dark shadow-md text-sm">
            ISL
          </div>
          <div>
            <h1 className="text-base md:text-lg font-bold tracking-tight text-white flex items-center gap-2">
              ISL Translator
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 md:gap-4">
          <LanguageSelect selectedCode={targetLang} onChange={(code) => setTargetLang(code)} />

          <button
            onClick={() => handleEmergencyTrigger("Please help me immediately!", "कृपया तुरंत मेरी सहायता करें!")}
            className="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-alert-red hover:bg-red-700 text-white transition shadow-md flex items-center gap-1.5"
          >
            <span>🚨</span>
            <span>SOS</span>
          </button>

          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-xl bg-navy-light text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 transition"
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* Main Translation Studio Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8 flex flex-col gap-6">
        {/* Top Emergency Trigger Bar */}
        <EmergencyBar onTriggerEmergency={handleEmergencyTrigger} />

        {/* 2-Column Desktop Grid / Stacked Mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Camera Feed & Skeleton Detection */}
          <section className="lg:col-span-7 flex flex-col gap-3">
            <CameraView
              detectedSign={detectedSign}
              confidence={confidence}
              handsDetected={handsDetected}
              fps={fps}
              isActive={isCameraActive}
              onToggleActive={() => setIsCameraActive(!isCameraActive)}
            />
          </section>

          {/* Right: Caption, Translation & Voice Panel */}
          <section className="lg:col-span-5 flex flex-col gap-4">
            <CaptionPanel
              glosses={glosses}
              englishSentence={englishSentence}
              translatedSentence={translatedSentence}
              targetLangName={currentLangObj.name}
              isTranslating={isTranslating}
              onClear={handleClear}
              onDeleteLastGloss={handleDeleteLastGloss}
              onSpeak={handleSpeak}
              isSpeaking={isSpeaking}
            />

            {/* Translation History Log */}
            <HistoryLog items={history} onClear={() => setHistory([])} />
          </section>
        </div>
      </main>

      {/* Footer & Accreditations */}
      <footer className="w-full bg-navy/80 border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-400 flex flex-col md:flex-row items-center justify-between gap-2">
        <div>
          Problem Statement 2024 • Ministry of Social Justice and Empowerment (ISLRTC & DePWD)
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>On-Device Privacy Preserved</span>
          <span>•</span>
          <span>Team: Siddhant • Parth • Abhi</span>
        </div>
      </footer>

      {/* Screen Reader ARIA Live Announcer */}
      <AriaAnnouncer message={translatedSentence || (detectedSign ? `Sign detected: ${detectedSign}` : "")} />

      {/* Accessibility & Settings Drawer */}
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        autoSpeak={autoSpeak}
        onToggleAutoSpeak={() => setAutoSpeak(!autoSpeak)}
        speechRate={speechRate}
        onChangeSpeechRate={setSpeechRate}
        highContrast={highContrast}
        onToggleHighContrast={() => setHighContrast(!highContrast)}
      />
    </div>
  );
}
