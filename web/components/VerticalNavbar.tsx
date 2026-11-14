"use client";

import React, { useState, useEffect } from "react";
import {
  Video,
  MessageSquare,
  GraduationCap,
  Sparkles,
  BookOpen,
  Bookmark,
  Settings,
  AlertTriangle,
  User,
  Volume2,
  VolumeX,
  Layers,
  ChevronRight,
  Database,
} from "lucide-react";

export type NavTabId = "live" | "twoway" | "learning" | "fingerspelling" | "context";

interface VerticalNavbarProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  onOpenSavedPhrases: () => void;
  onOpenSettings: () => void;
  onOpenProfile: () => void;
  onTriggerEmergency: () => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
  userName?: string;
  userRole?: string;
}

export const VerticalNavbar: React.FC<VerticalNavbarProps> = ({
  activeTab,
  onTabChange,
  onOpenSavedPhrases,
  onOpenSettings,
  onOpenProfile,
  onTriggerEmergency,
  soundEnabled,
  onToggleSound,
  userName = "Siddhant",
  userRole = "Signer",
}) => {
  const [dbUser, setDbUser] = useState<{ name: string; role: string }>({ name: userName, role: userRole });

  useEffect(() => {
    fetch("/api/user")
      .then((res) => res.json())
      .then((data) => {
        if (data.user) {
          setDbUser({
            name: data.user.name || userName,
            role: data.user.role || userRole,
          });
        }
      })
      .catch(() => {});
  }, [userName, userRole]);

  const navItems: { id: NavTabId; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: "live",
      label: "Live Translate",
      icon: <Video className="w-5 h-5" />,
      badge: "Realtime",
    },
    {
      id: "twoway",
      label: "Two-Way Chat",
      icon: <MessageSquare className="w-5 h-5" />,
    },
    {
      id: "learning",
      label: "Learning Studio",
      icon: <GraduationCap className="w-5 h-5" />,
    },
    {
      id: "fingerspelling",
      label: "Fingerspelling",
      icon: <Layers className="w-5 h-5" />,
    },
    {
      id: "context",
      label: "Context Packs",
      icon: <BookOpen className="w-5 h-5" />,
    },
  ];

  return (
    <aside className="w-64 shrink-0 hidden md:flex flex-col justify-between bg-space-900/90 border-r border-gold-500/20 backdrop-blur-xl h-screen sticky top-0 z-30 select-none">
      {/* Top Header & Emblem */}
      <div>
        <div className="p-5 border-b border-space-800">
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-tr from-gold-500 via-ruby-500 to-white p-0.5 shadow-lg group">
              <div className="w-full h-full bg-space-950 rounded-[10px] flex items-center justify-center font-black text-sm tracking-wider gold-gradient-text">
                ISL
              </div>
              <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-ruby-500 border-2 border-space-900 animate-pulse" />
            </div>

            <div>
              <h1 className="text-sm font-extrabold text-white flex items-center gap-1.5 tracking-tight">
                ISL Translator
              </h1>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-gold-400 animate-sparkle" />
                <span className="text-[10px] font-semibold text-gold-300/90 tracking-wide uppercase">
                  Gold & Ruby Edition
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Primary Vertical Navigation Tabs */}
        <div className="p-3 space-y-1.5">
          <div className="px-3 pt-2 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Navigation Studio
          </div>

          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition group ${
                  isActive
                    ? "bg-gradient-to-r from-gold-500/20 to-ruby-500/10 text-white border border-gold-500/50 shadow-md"
                    : "text-slate-300 hover:text-white hover:bg-space-850 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`transition ${
                      isActive ? "text-gold-400" : "text-slate-400 group-hover:text-gold-300"
                    }`}
                  >
                    {item.icon}
                  </div>
                  <span>{item.label}</span>
                </div>

                {item.badge ? (
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-gold-500/20 text-gold-300 border border-gold-500/30">
                    {item.badge}
                  </span>
                ) : (
                  <ChevronRight
                    className={`w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition ${
                      isActive ? "opacity-100 text-gold-400" : "text-slate-500"
                    }`}
                  />
                )}
              </button>
            );
          })}

          {/* Quick Saved Phrases Bookmark Link */}
          <button
            onClick={onOpenSavedPhrases}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-space-850 border border-transparent hover:border-gold-500/30 transition group"
          >
            <div className="flex items-center gap-3">
              <div className="text-gold-400 group-hover:scale-110 transition">
                <Bookmark className="w-5 h-5" />
              </div>
              <span>Saved Bookmarks</span>
            </div>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-space-800 text-slate-300 border border-space-700">
              Prisma
            </span>
          </button>
        </div>
      </div>

      {/* Bottom Profile, SOS and Action Controls */}
      <div className="p-3 border-t border-space-800 space-y-2">
        {/* Urgent Emergency SOS Button */}
        <button
          onClick={onTriggerEmergency}
          className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-ruby-600 via-ruby-500 to-ruby-700 hover:from-ruby-500 hover:to-ruby-600 text-white font-extrabold text-xs shadow-lg shadow-ruby-900/40 border border-ruby-400/50 flex items-center justify-center gap-2 transition active:scale-95 group"
        >
          <AlertTriangle className="w-4 h-4 text-white animate-bounce" />
          <span>INSTANT SOS EMERGENCY</span>
        </button>

        {/* User Profile Card */}
        <div
          onClick={onOpenProfile}
          className="flex items-center justify-between p-2.5 rounded-xl bg-space-850 hover:bg-space-800 border border-space-700/80 hover:border-gold-500/40 transition cursor-pointer group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-gold-500 to-ruby-500 p-0.5 shrink-0">
              <div className="w-full h-full bg-space-950 rounded-[7px] flex items-center justify-center font-bold text-xs text-gold-300">
                {dbUser.name[0]?.toUpperCase() || "S"}
              </div>
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-white truncate group-hover:text-gold-300 transition">
                {dbUser.name}
              </div>
              <div className="text-[10px] text-slate-400 flex items-center gap-1">
                <Database className="w-2.5 h-2.5 text-gold-400" />
                <span className="truncate">{dbUser.role}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onToggleSound();
              }}
              title={soundEnabled ? "Mute audio cues" : "Unmute audio cues"}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-700 transition"
            >
              {soundEnabled ? <Volume2 className="w-3.5 h-3.5 text-gold-400" /> : <VolumeX className="w-3.5 h-3.5" />}
            </button>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onOpenSettings();
              }}
              title="Open Settings"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-700 transition"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
