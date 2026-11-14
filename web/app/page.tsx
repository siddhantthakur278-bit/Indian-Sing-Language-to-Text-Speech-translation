"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Image from "next/image";
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
import { VerticalNavbar, NavTabId } from "@/components/VerticalNavbar";
import { GlitterCanvas } from "@/components/GlitterCanvas";
import { UserProfileModal } from "@/components/UserProfileModal";
import { SavedPhrasesModal } from "@/components/SavedPhrasesModal";
import { speakText, stopSpeaking } from "@/lib/speech";
import { requestSentenceTranslation } from "@/lib/api";
import { soundEffects } from "@/lib/audioFeedback";
import { DetectedGesture } from "@/lib/mediapipeVision";
import { HolisticResults } from "@/lib/landmarks";
import {
  Video,
  MessageSquare,
  GraduationCap,
  Sparkles,
  Layers,
  BookOpen,
  Bookmark,
  AlertTriangle,
  User,
  Sliders,
  Volume2,
  VolumeX,
} from "lucide-react";

export default function Home() {
  // Navigation & View Mode
  const [activeTab, setActiveTab] = useState<NavTabId>("live");

  // Application & Hardware State
  const [isCameraActive, setIsCameraActive] = useState<boolean>(true);
  const [detectedSign, setDetectedSign] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0);
  const [handsDetected, setHandsDetected] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(30);

  // Linguistic & Translation State
  const [targetLang, setTargetLang] = useState<string>("hi");
  const [glosses, setGlosses] = useState<string[]>([]);
  const [englishSentence, setEnglishSentence] = useState<string>("");
  const [translatedSentence, setTranslatedSentence] = useState<string>("");
  const [isTranslating, setIsTranslating] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [signMode, setSignMode] = useState<"auto" | "hold">("auto");
  const [isHoldingSpace, setIsHoldingSpace] = useState<boolean>(false);

  // Modals & Panels
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isProfileOpen, setIsProfileOpen] = useState<boolean>(false);
  const [isSavedPhrasesOpen, setIsSavedPhrasesOpen] = useState<boolean>(false);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);

  // Accessibility & Preferences
  const [autoSpeak, setAutoSpeak] = useState<boolean>(true);
  const [speechRate, setSpeechRate] = useState<number>(1.0);
  const [highContrast, setHighContrast] = useState<boolean>(false);
  const [userName, setUserName] = useState<string>("Siddhant");
  const [userRole, setUserRole] = useState<string>("Signer");

  // Quick Bookmarks cache for instant camera bar
  const [quickBookmarks, setQuickBookmarks] = useState<any[]>([]);

  // History State
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

  // 1. Initial Load from Prisma Database (User Profile, History & Quick Bookmarks)
  useEffect(() => {
    // Fetch User Profile
    fetch("/api/user")
      .then((res) => res.json())
      .then((data) => {
        if (data.user) {
          if (data.user.name) setUserName(data.user.name);
          if (data.user.role) setUserRole(data.user.role);
          if (data.user.preferredLang) setTargetLang(data.user.preferredLang);
          if (data.user.speechRate) setSpeechRate(data.user.speechRate);
          if (typeof data.user.autoSpeak === "boolean") setAutoSpeak(data.user.autoSpeak);
          if (data.user.signMode) setSignMode(data.user.signMode);
        }
      })
      .catch((err) => console.log("Profile fetch note:", err));

    // Fetch Database History
    fetch("/api/history")
      .then((res) => res.json())
      .then((data) => {
        if (data.history && data.history.length > 0) {
          setHistory(data.history);
        }
      })
      .catch((err) => console.log("History fetch note:", err));

    // Fetch Quick Saved Phrases
    fetch("/api/saved-phrases")
      .then((res) => res.json())
      .then((data) => {
        if (data.phrases) {
          setQuickBookmarks(data.phrases.slice(0, 5));
        }
      })
      .catch(() => {});
  }, []);

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
    const newItem: HistoryItem = {
      id: Math.random().toString(),
      time: timeStr,
      english: phrase,
      translated: translationHi,
      lang: "hi",
      isEmergency: true,
    };

    setHistory((prev) => [newItem, ...prev]);

    // Save Emergency to Prisma DB
    fetch("/api/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        glosses: ["HELP", "EMERGENCY"],
        english: phrase,
        translated: translationHi,
        lang: "hi",
        isEmergency: true,
      }),
    }).catch(() => {});

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

  const triggerTranslation = useCallback(
    async (currentGlosses: string[], lang: string) => {
      if (currentGlosses.length === 0) return;
      setIsTranslating(true);
      try {
        const res = await requestSentenceTranslation(currentGlosses, lang);
        setEnglishSentence(res.sentence);
        setTranslatedSentence(res.translated);

        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
        const newRecord: HistoryItem = {
          id: Math.random().toString(),
          time: timeStr,
          english: res.sentence,
          translated: res.translated,
          lang: res.lang,
          isEmergency: res.emergency,
        };

        setHistory((prev) => [newRecord, ...prev]);

        // Persist to Prisma Database
        fetch("/api/history", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            glosses: currentGlosses,
            english: res.sentence,
            translated: res.translated,
            lang: res.lang,
            isEmergency: res.emergency,
          }),
        }).catch(() => {});

        if (autoSpeak && res.translated) {
          setIsSpeaking(true);
          speakText(res.translated, res.lang, speechRate, () => setIsSpeaking(false), () => setIsSpeaking(false));
        }
      } catch (err) {
        console.error("Translation request failed:", err);
      } finally {
        setIsTranslating(false);
      }
    },
    [autoSpeak, speechRate]
  );

  // Bookmark phrase to Prisma DB
  const handleBookmarkSentence = async (english: string, translated: string, currentGlosses: string[]) => {
    try {
      await fetch("/api/saved-phrases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: english.slice(0, 32),
          glosses: currentGlosses,
          english,
          translated,
          category: "Live",
        }),
      });
      // Refresh quick bookmarks
      const res = await fetch("/api/saved-phrases");
      const data = await res.json();
      if (data.phrases) setQuickBookmarks(data.phrases.slice(0, 5));
    } catch (err) {
      console.error("Failed to bookmark phrase:", err);
    }
  };

  const handleClearHistory = async () => {
    setHistory([]);
    try {
      await fetch("/api/history", { method: "DELETE" });
    } catch (err) {
      console.error("Failed to clear DB history:", err);
    }
  };

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

  // Live detection event handler from MediaPipe vision stream
  const handleLiveDetection = useCallback(
    (data: {
      results: HolisticResults;
      gesture: DetectedGesture | null;
      fps: number;
      handsDetected: boolean;
    }) => {
      setFps(data.fps);
      setHandsDetected(data.handsDetected);

      if (signModeRef.current === "hold" && !isHoldingSpaceRef.current) {
        setDetectedSign(null);
        return;
      }

      if (data.gesture) {
        setDetectedSign(data.gesture.gloss);
        setConfidence(data.gesture.confidence);

        if (sentenceTimerRef.current) {
          clearTimeout(sentenceTimerRef.current);
          sentenceTimerRef.current = null;
        }

        const now = performance.now();
        if (
          data.gesture.confidence >= 0.88 &&
          now - lastAddedSignRef.current.time > 1200 &&
          (data.gesture.gloss !== lastAddedSignRef.current.sign || now - lastAddedSignRef.current.time > 2500)
        ) {
          lastAddedSignRef.current = { sign: data.gesture.gloss, time: now };
          if (soundEnabled) soundEffects.playSignRecognizedTone();

          setGlosses((prev) => {
            if (isSentenceFinalizedRef.current) {
              isSentenceFinalizedRef.current = false;
              return [data.gesture!.gloss];
            }
            return [...prev, data.gesture!.gloss];
          });
        }
      } else {
        setDetectedSign(null);

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
    [triggerTranslation, soundEnabled]
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
    <div className={`min-h-screen flex text-slate-100 bg-space-950 relative selection:bg-gold-500 selection:text-space-950 ${highContrast ? "contrast-125" : ""}`}>
      {/* Ambient Stardust & Twinkle Glitter Particles */}
      <GlitterCanvas density={55} />

      {/* Sleek Vertical Navigation Bar (Left Column Dock on Desktop) */}
      <VerticalNavbar
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        onOpenSavedPhrases={() => setIsSavedPhrasesOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
        onTriggerEmergency={() => handleEmergencyTrigger("Please help me immediately!", "कृपया तुरंत मेरी सहायता करें!")}
        soundEnabled={soundEnabled}
        onToggleSound={() => setSoundEnabled(!soundEnabled)}
        userName={userName}
        userRole={userRole}
      />

      {/* Main Content Workspace Column */}
      <div className="flex-1 flex flex-col min-w-0 z-10 overflow-x-hidden">
        {/* Top Header Bar */}
        <header className="w-full bg-space-900/80 border-b border-gold-500/20 px-4 md:px-8 py-3.5 flex items-center justify-between sticky top-0 z-20 backdrop-blur-xl">
          {/* Mobile Logo Brand */}
          <div className="flex items-center gap-3">
            <div className="md:hidden w-8 h-8 rounded-xl bg-space-950 border border-gold-500/40 p-0.5 shadow-md overflow-hidden">
              <Image src="/icon.svg" alt="Sanket Logo" width={32} height={32} className="w-full h-full object-contain" />
            </div>
            <div>
              <h1 className="text-sm md:text-base font-extrabold tracking-tight text-white flex items-center gap-2">
                <span>Sanket</span>
                <span className="text-gold-400 font-bold text-xs">संकेत</span>
                <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-gold-500/20 text-gold-300 border border-gold-500/40">
                  <span className="w-1.5 h-1.5 rounded-full bg-gold-400 animate-sparkle" />
                  Sign to Speech
                </span>
              </h1>
            </div>
          </div>

          {/* Top Actions: Language Select, Emergency SOS, Profile & Settings */}
          <div className="flex items-center gap-2.5 md:gap-3.5">
            <LanguageSelect selectedCode={targetLang} onChange={(code) => setTargetLang(code)} />

            {/* Quick Saved Bookmarks Icon (Visible on small screens) */}
            <button
              onClick={() => setIsSavedPhrasesOpen(true)}
              className="p-2 rounded-xl bg-space-850 hover:bg-space-800 text-gold-400 border border-gold-500/30 transition shadow-sm"
              title="Saved Phrases"
            >
              <Bookmark className="w-4 h-4" />
            </button>

            {/* Quick Profile Icon (Mobile) */}
            <button
              onClick={() => setIsProfileOpen(true)}
              className="md:hidden p-2 rounded-xl bg-space-850 hover:bg-space-800 text-slate-300 border border-space-700 transition"
              title="User Profile"
            >
              <User className="w-4 h-4 text-gold-400" />
            </button>

            {/* Emergency SOS Button */}
            <button
              onClick={() => handleEmergencyTrigger("Please help me immediately!", "कृपया तुरंत मेरी सहायता करें!")}
              className="px-3 py-1.5 rounded-xl font-extrabold text-xs bg-gradient-to-r from-ruby-600 to-ruby-500 hover:from-ruby-500 hover:to-ruby-600 text-white transition shadow-lg shadow-ruby-950/50 flex items-center gap-1.5 border border-ruby-400/50 active:scale-95"
            >
              <AlertTriangle className="w-3.5 h-3.5 animate-bounce" />
              <span>SOS</span>
            </button>

            {/* Settings Trigger */}
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-xl bg-space-850 text-slate-300 hover:text-white border border-space-700 hover:border-gold-500/40 transition"
              title="Settings"
            >
              <Sliders className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Mobile Horizontal Navigation Tabs */}
        <div className="md:hidden flex items-center gap-1 p-2 bg-space-900 border-b border-space-800 overflow-x-auto no-scrollbar">
          {[
            { id: "live", label: "📹 Live", full: "Live Translate" },
            { id: "twoway", label: "💬 Two-Way", full: "Two-Way Chat" },
            { id: "learning", label: "🎓 Learn", full: "Learning Studio" },
            { id: "fingerspelling", label: "🔤 Spell", full: "Fingerspelling" },
            { id: "context", label: "🎒 Packs", full: "Context Packs" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as NavTabId)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold shrink-0 transition ${
                activeTab === tab.id
                  ? "bg-gold-500/20 text-gold-300 border border-gold-500/40 shadow-sm"
                  : "text-slate-400 hover:text-white bg-space-850"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Main Interactive Studio Body */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8 flex flex-col gap-6">
          {/* Top SOS Emergency Bar */}
          <EmergencyBar onTriggerEmergency={handleEmergencyTrigger} />

          {/* Quick Bookmarks Row (Under SOS Bar) */}
          {quickBookmarks.length > 0 && activeTab === "live" && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar text-xs">
              <span className="text-[11px] font-bold uppercase tracking-wider text-gold-400 flex items-center gap-1 shrink-0">
                <Bookmark className="w-3.5 h-3.5" />
                Quick Bookmarks:
              </span>
              {quickBookmarks.map((phrase) => (
                <button
                  key={phrase.id}
                  onClick={() => {
                    setGlosses(phrase.glosses || []);
                    setEnglishSentence(phrase.english);
                    setTranslatedSentence(phrase.translated);
                    if (autoSpeak) speakText(phrase.translated, targetLang, speechRate);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-space-900 hover:bg-space-850 border border-gold-500/20 hover:border-gold-500/50 text-slate-300 hover:text-gold-300 font-semibold shrink-0 transition flex items-center gap-1.5 shadow-sm"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-gold-400" />
                  <span>{phrase.title}</span>
                </button>
              ))}
              <button
                onClick={() => setIsSavedPhrasesOpen(true)}
                className="text-[11px] text-gold-400 hover:text-gold-300 font-bold underline shrink-0 ml-1"
              >
                + More
              </button>
            </div>
          )}

          {/* Mode 1: Live Translation Grid */}
          {activeTab === "live" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start animate-fadeIn">
              {/* Left Column: Camera Feed & Skeleton Detection */}
              <section className="lg:col-span-7 flex flex-col gap-3">
                {/* Signing Mode Selector & Push-To-Sign Bar */}
                <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-2xl bg-space-900 border border-gold-500/25 shadow-lg backdrop-blur-md">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-slate-300">Sign Mode:</span>
                    <button
                      onClick={() => setSignMode("auto")}
                      className={`px-3 py-1 rounded-xl text-xs font-bold transition ${
                        signMode === "auto"
                          ? "bg-gradient-to-r from-gold-400 to-gold-500 text-space-950 shadow-md font-extrabold"
                          : "bg-space-850 text-slate-300 hover:text-white"
                      }`}
                    >
                      ✨ Hands-Free Auto
                    </button>
                    <button
                      onClick={() => setSignMode("hold")}
                      className={`px-3 py-1 rounded-xl text-xs font-bold transition ${
                        signMode === "hold"
                          ? "bg-gradient-to-r from-ruby-500 to-ruby-600 text-white shadow-md font-extrabold"
                          : "bg-space-850 text-slate-300 hover:text-white"
                      }`}
                    >
                      ⌨️ Push-to-Sign (Space)
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
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition select-none flex items-center gap-1.5 ${
                        isHoldingSpace
                          ? "bg-emerald-500 text-white shadow-lg animate-pulse"
                          : "bg-space-850 text-slate-200 border border-gold-500/30 hover:bg-space-800"
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${isHoldingSpace ? "bg-white" : "bg-emerald-400"}`} />
                      {isHoldingSpace ? "Recording Sign... Release when done" : "Hold Space or Click to Sign"}
                    </button>
                  ) : (
                    <span className="text-[11px] text-slate-400 hidden sm:inline">
                      Sign freely &bull; Lower hands 1.5s to synthesize sentence
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

              {/* Right Column: Caption, Translation & History */}
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
                  onBookmarkSentence={handleBookmarkSentence}
                />

                {/* Database Synced Translation History Log */}
                <HistoryLog
                  items={history}
                  onClear={handleClearHistory}
                  onBookmark={(item) => handleBookmarkSentence(item.english, item.translated, [])}
                />
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
        <footer className="w-full bg-space-950/90 border-t border-space-850 px-6 py-4 text-center text-xs text-slate-400 flex flex-col md:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gold-400" />
            <span>Problem Statement 2024 &bull; Ministry of Social Justice and Empowerment (ISLRTC &amp; DePWD)</span>
          </div>
          <div className="flex items-center gap-3 text-slate-400">
            <span>Client-Side Privacy Preserved</span>
            <span>&bull;</span>
            <span className="text-gold-300 font-semibold">Prisma SQLite Local DB</span>
            <span>&bull;</span>
            <span>Team: Siddhant &bull; Parth &bull; Abhi</span>
          </div>
        </footer>
      </div>

      {/* Screen Reader ARIA Live Announcer */}
      <AriaAnnouncer message={translatedSentence || (detectedSign ? `Sign detected: ${detectedSign}` : "")} />

      {/* User Profile & Database Statistics Modal */}
      <UserProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        onUserUpdated={() => {
          fetch("/api/user")
            .then((res) => res.json())
            .then((data) => {
              if (data.user?.name) setUserName(data.user.name);
              if (data.user?.role) setUserRole(data.user.role);
            });
        }}
      />

      {/* Saved Phrases Quick Bookmark Modal */}
      <SavedPhrasesModal
        isOpen={isSavedPhrasesOpen}
        onClose={() => setIsSavedPhrasesOpen(false)}
        targetLang={targetLang}
        onSelectPhrase={(phraseGlosses, en, trans) => {
          setGlosses(phraseGlosses);
          setEnglishSentence(en);
          setTranslatedSentence(trans);
          setActiveTab("live");
          if (autoSpeak) speakText(trans, targetLang, speechRate);
        }}
      />

      {/* Accessibility & Audio Settings Drawer */}
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
