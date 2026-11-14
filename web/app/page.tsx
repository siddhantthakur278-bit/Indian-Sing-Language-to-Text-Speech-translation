"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { CameraView } from "@/components/CameraView";
import { CaptionPanel } from "@/components/CaptionPanel";
import { LanguageSelect, SUPPORTED_LANGUAGES } from "@/components/LanguageSelect";
import { EmergencyBar } from "@/components/EmergencyBar";
import { HistoryLog, HistoryItem } from "@/components/HistoryLog";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { AriaAnnouncer } from "@/components/AriaAnnouncer";
import { TwoWayChat } from "@/components/TwoWayChat";
import { LearningMode } from "@/components/LearningMode";
import { Fingerspelling } from "@/components/Fingerspelling";
import { ContextPacks } from "@/components/ContextPacks";
import { speakText, stopSpeaking } from "@/lib/speech";
import { requestSentenceTranslation } from "@/lib/api";
import { soundEffects } from "@/lib/audioFeedback";
import { DetectedGesture } from "@/lib/mediapipeVision";
import { HolisticResults } from "@/lib/landmarks";

export default function Home() {
  // Application State
  const [isCameraActive, setIsCameraActive] = useState<boolean>(true);
  const [detectedSign, setDetectedSign] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0);
  const [handsDetected, setHandsDetected] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(30);
  const [activeTab, setActiveTab] = useState<"live" | "twoway" | "learning" | "fingerspelling" | "context">("live");

  // Linguistic & Translation State
  const [targetLang, setTargetLang] = useState<string>("hi");
  const [glosses, setGlosses] = useState<string[]>([]);
  const [englishSentence, setEnglishSentence] = useState<string>("");
  const [translatedSentence, setTranslatedSentence] = useState<string>("");
  const [isTranslating, setIsTranslating] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [signMode, setSignMode] = useState<"auto" | "hold">("auto");
  const [isHoldingSpace, setIsHoldingSpace] = useState<boolean>(false);

  // Synchronized refs to avoid stale closures in timeouts and callbacks
  const glossesRef = useRef<string[]>([]);
  useEffect(() => {
    glossesRef.current = glosses;
  }, [glosses]);

  const targetLangRef = useRef<string>(targetLang);
  useEffect(() => {
    targetLangRef.current = targetLang;
  }, [targetLang]);

  const signModeRef = useRef<"auto" | "hold">("auto");
  useEffect(() => {
    signModeRef.current = signMode;
  }, [signMode]);

  const isHoldingSpaceRef = useRef<boolean>(false);
  useEffect(() => {
    isHoldingSpaceRef.current = isHoldingSpace;
  }, [isHoldingSpace]);

  const sentenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastAddedSignRef = useRef<{ sign: string; time: number }>({ sign: "", time: 0 });
  const isSentenceFinalizedRef = useRef<boolean>(false);

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

  // Handle manual speak
  const handleSpeak = useCallback(() => {
    if (!translatedSentence) return;
    setIsSpeaking(true);
    speakText(
      translatedSentence,
      targetLang,
      speechRate,
      () => setIsSpeaking(false),
      () => setIsSpeaking(false)
    );
  }, [translatedSentence, targetLang, speechRate]);

  // Handle emergency phrase trigger
  const handleEmergencyTrigger = useCallback((phrase: string, translationHi: string) => {
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
  }, []);

  const handleClear = useCallback(() => {
    stopSpeaking();
    if (sentenceTimerRef.current) {
      clearTimeout(sentenceTimerRef.current);
      sentenceTimerRef.current = null;
    }
    setGlosses([]);
    setEnglishSentence("");
    setTranslatedSentence("");
    setIsSpeaking(false);
    isSentenceFinalizedRef.current = false;
  }, []);

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

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (["INPUT", "SELECT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      if (e.key === " " || e.code === "Space") {
        if (!e.repeat) {
          e.preventDefault();
          if (signModeRef.current === "hold") {
            setIsHoldingSpace(true);
          }
        }
      } else if (e.key === "s" || e.key === "S") {
        handleSpeak();
      } else if (e.key === "c" || e.key === "C") {
        handleClear();
      } else if (e.key === "e" || e.key === "E") {
        handleEmergencyTrigger("Please help me immediately!", "कृपया तुरंत मेरी सहायता करें!");
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (["INPUT", "SELECT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        if (signModeRef.current === "hold") {
          setIsHoldingSpace(false);
          // When releasing spacebar in hold mode, finalize and translate accumulated glosses
          if (glossesRef.current.length > 0) {
            isSentenceFinalizedRef.current = true;
            triggerTranslation(glossesRef.current, targetLangRef.current);
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [handleSpeak, handleClear, handleEmergencyTrigger, triggerTranslation]);

  // Live detection event handler from real MediaPipe vision stream
  const handleLiveDetection = useCallback(
    (data: {
      results: HolisticResults;
      gesture: DetectedGesture | null;
      fps: number;
      handsDetected: boolean;
    }) => {
      setFps(data.fps);
      setHandsDetected(data.handsDetected);

      // In "hold" mode: ignore detections unless Space is actively held
      if (signModeRef.current === "hold" && !isHoldingSpaceRef.current) {
        setDetectedSign(null);
        return;
      }

      if (data.gesture) {
        setDetectedSign(data.gesture.gloss);
        setConfidence(data.gesture.confidence);

        // Cancel any pending end-of-sentence timer while user is actively signing
        if (sentenceTimerRef.current) {
          clearTimeout(sentenceTimerRef.current);
          sentenceTimerRef.current = null;
        }

        const now = performance.now();
        // Cooldown between adding signs: 1200ms; same sign: 2500ms
        if (
          data.gesture.confidence >= 0.88 &&
          now - lastAddedSignRef.current.time > 1200 &&
          (data.gesture.gloss !== lastAddedSignRef.current.sign || now - lastAddedSignRef.current.time > 2500)
        ) {
          lastAddedSignRef.current = { sign: data.gesture.gloss, time: now };
          soundEffects.playSignRecognizedTone();

          setGlosses((prev) => {
            if (isSentenceFinalizedRef.current) {
              isSentenceFinalizedRef.current = false;
              return [data.gesture!.gloss];
            }
            return [...prev, data.gesture!.gloss];
          });
        }
      } else {
        // No gesture active (hands resting / IDLE)
        setDetectedSign(null);

        // In auto mode: when hands drop and stay idle for 1.5s, finalize sentence and speak ONCE
        if (
          signModeRef.current === "auto" &&
          glossesRef.current.length > 0 &&
          !sentenceTimerRef.current &&
          !isSentenceFinalizedRef.current
        ) {
          sentenceTimerRef.current = setTimeout(() => {
            if (glossesRef.current.length > 0) {
              isSentenceFinalizedRef.current = true;
              triggerTranslation(glossesRef.current, targetLangRef.current);
            }
            sentenceTimerRef.current = null;
          }, 1500);
        }
      }
    },
    [triggerTranslation]
  );

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
        {/* Navigation Mode Switcher Bar */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
          {[
            { id: "live", label: "📹 Live Translate", desc: "Camera ISL Sign Translation" },
            { id: "twoway", label: "💬 Two-Way Chat", desc: "Deaf ↔ Hearing Conversation" },
            { id: "learning", label: "🎓 Learning Studio", desc: "Interactive Sign Practice" },
            { id: "fingerspelling", label: "🔤 Fingerspelling", desc: "A-Z & Numbers 0-9" },
            { id: "context", label: "🎒 Context Packs", desc: "Hospital, Police & Travel" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === tab.id
                  ? "bg-teal text-navy-dark shadow-md"
                  : "bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60"
              }`}
            >
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Top Emergency Trigger Bar */}
        <EmergencyBar onTriggerEmergency={handleEmergencyTrigger} />

        {/* Mode 1: Live Translation Grid */}
        {activeTab === "live" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start animate-fadeIn">
            {/* Left: Camera Feed & Skeleton Detection */}
            <section className="lg:col-span-7 flex flex-col gap-3">
              {/* Signing Mode Selector & Push-To-Sign Bar */}
              <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-900/90 border border-slate-700/70 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-slate-400">Mode:</span>
                  <button
                    onClick={() => setSignMode("auto")}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      signMode === "auto"
                        ? "bg-teal text-navy-dark shadow-sm"
                        : "bg-slate-800 text-slate-300 hover:text-white"
                    }`}
                  >
                    ✨ Hands-Free Auto
                  </button>
                  <button
                    onClick={() => setSignMode("hold")}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      signMode === "hold"
                        ? "bg-accent-orange text-navy-dark shadow-sm"
                        : "bg-slate-800 text-slate-300 hover:text-white"
                    }`}
                  >
                    ⌨️ Push to Sign (Space)
                  </button>
                </div>

                {signMode === "hold" ? (
                  <button
                    onMouseDown={() => setIsHoldingSpace(true)}
                    onMouseUp={() => {
                      setIsHoldingSpace(false);
                      if (glossesRef.current.length > 0) {
                        isSentenceFinalizedRef.current = true;
                        triggerTranslation(glossesRef.current, targetLangRef.current);
                      }
                    }}
                    onTouchStart={() => setIsHoldingSpace(true)}
                    onTouchEnd={() => {
                      setIsHoldingSpace(false);
                      if (glossesRef.current.length > 0) {
                        isSentenceFinalizedRef.current = true;
                        triggerTranslation(glossesRef.current, targetLangRef.current);
                      }
                    }}
                    className={`px-3.5 py-1 rounded-lg text-xs font-bold transition select-none flex items-center gap-1.5 ${
                      isHoldingSpace
                        ? "bg-emerald-500 text-white animate-pulse"
                        : "bg-slate-800 text-slate-200 border border-slate-600 hover:bg-slate-700 active:bg-emerald-600"
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isHoldingSpace ? "bg-white" : "bg-emerald-400"}`} />
                    {isHoldingSpace ? "Recording Sign... Release when done" : "Hold Space or Click Here to Sign"}
                  </button>
                ) : (
                  <span className="text-[11px] text-slate-400 hidden sm:inline">
                    Sign freely &bull; Lower hands 1.5s to translate
                  </span>
                )}
              </div>

              <CameraView
                detectedSign={detectedSign}
                confidence={confidence}
                handsDetected={handsDetected}
                fps={fps}
                isActive={isCameraActive}
                onToggleActive={() => setIsCameraActive(!isCameraActive)}
                onLiveDetection={handleLiveDetection}
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
        )}

        {/* Mode 2: Two-Way Communication Bridge */}
        {activeTab === "twoway" && (
          <div className="animate-fadeIn">
            <TwoWayChat onSpeak={handleSpeak} />
          </div>
        )}

        {/* Mode 3: Interactive Learning Studio */}
        {activeTab === "learning" && (
          <div className="animate-fadeIn">
            <LearningMode />
          </div>
        )}

        {/* Mode 4: Fingerspelling & Number Matrix */}
        {activeTab === "fingerspelling" && (
          <div className="animate-fadeIn">
            <Fingerspelling />
          </div>
        )}

        {/* Mode 5: Scenario Context Packs */}
        {activeTab === "context" && (
          <div className="animate-fadeIn">
            <ContextPacks
              onSelectPhrase={(g, en, hi) => {
                setGlosses(g);
                setEnglishSentence(en);
                setTranslatedSentence(hi);
                setActiveTab("live");
              }}
            />
          </div>
        )}
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
