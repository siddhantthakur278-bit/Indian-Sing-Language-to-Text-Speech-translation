"use client";

import React, { useState, useEffect } from "react";
import { User, Activity, Bookmark, Award, Globe, Volume2, ShieldCheck, Sparkles, X, Check } from "lucide-react";

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUserUpdated?: () => void;
}

export const UserProfileModal: React.FC<UserProfileModalProps> = ({ isOpen, onClose, onUserUpdated }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [userData, setUserData] = useState<any>(null);
  const [stats, setStats] = useState<{ totalTranslations: number; savedPhrases: number; practiceSessions: number }>({
    totalTranslations: 0,
    savedPhrases: 0,
    practiceSessions: 0,
  });

  const [name, setName] = useState<string>("Siddhant");
  const [role, setRole] = useState<string>("Signer");
  const [theme, setTheme] = useState<string>("galaxy-gold");
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    fetch("/api/user")
      .then((res) => res.json())
      .then((data) => {
        if (data.user) {
          setUserData(data.user);
          setName(data.user.name || "Siddhant");
          setRole(data.user.role || "Signer");
          setTheme(data.user.theme || "galaxy-gold");
        }
        if (data.stats) {
          setStats(data.stats);
        }
      })
      .catch((err) => console.error("Error fetching user profile:", err))
      .finally(() => setLoading(false));
  }, [isOpen]);

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const res = await fetch("/api/user", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, role, theme }),
      });
      if (res.ok) {
        setSaveSuccess(true);
        if (onUserUpdated) onUserUpdated();
        setTimeout(() => setSaveSuccess(false), 2500);
      }
    } catch (err) {
      console.error("Failed to update profile:", err);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg rounded-2xl bg-space-900 border border-gold-500/30 shadow-2xl p-6 overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-gold-500 via-ruby-500 to-white" />

        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-space-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400 to-ruby-600 flex items-center justify-center text-white font-bold shadow-md">
              <User className="w-5 h-5 text-space-950" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                User Profile & Database
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gold-500/20 text-gold-300 border border-gold-500/30">
                  Prisma DB
                </span>
              </h2>
              <p className="text-xs text-slate-400">Manage your credentials, offline preferences and saved records</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-gold-500 border-t-transparent animate-spin" />
            <p className="text-xs text-slate-400">Connecting to Prisma SQLite database...</p>
          </div>
        ) : (
          <div className="mt-5 space-y-5">
            {/* Database Real-Time Metric Counters */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-space-850 border border-gold-500/20 text-center">
                <div className="flex justify-center mb-1 text-gold-400">
                  <Activity className="w-4 h-4" />
                </div>
                <div className="text-xl font-extrabold text-white">{stats.totalTranslations}</div>
                <div className="text-[11px] font-medium text-slate-400">Translations</div>
              </div>

              <div className="p-3 rounded-xl bg-space-850 border border-ruby-500/20 text-center">
                <div className="flex justify-center mb-1 text-ruby-400">
                  <Bookmark className="w-4 h-4" />
                </div>
                <div className="text-xl font-extrabold text-white">{stats.savedPhrases}</div>
                <div className="text-[11px] font-medium text-slate-400">Saved Bookmarks</div>
              </div>

              <div className="p-3 rounded-xl bg-space-850 border border-white/20 text-center">
                <div className="flex justify-center mb-1 text-slate-200">
                  <Award className="w-4 h-4" />
                </div>
                <div className="text-xl font-extrabold text-white">{stats.practiceSessions}</div>
                <div className="text-[11px] font-medium text-slate-400">Practice Drills</div>
              </div>
            </div>

            {/* Profile Edit Fields */}
            <div className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Signer / User Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-space-850 border border-space-700 text-white text-sm focus:border-gold-500 focus:outline-none transition"
                  placeholder="Enter your name"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">User Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-space-850 border border-space-700 text-white text-sm focus:border-gold-500 focus:outline-none transition"
                  >
                    <option value="Signer">Signer (Deaf / Hard of Hearing)</option>
                    <option value="Interpreter">Interpreter / Facilitator</option>
                    <option value="Learner">ISL Student / Learner</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Visual Theme</label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-space-850 border border-space-700 text-white text-sm focus:border-gold-500 focus:outline-none transition"
                  >
                    <option value="galaxy-gold">Stardust Gold & Ruby</option>
                    <option value="high-contrast">High Contrast Monochrome</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Data Privacy Status */}
            <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 flex items-start gap-2.5">
              <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div className="text-xs text-emerald-200">
                <span className="font-bold">On-Device Privacy Preserved:</span> All MediaPipe landmark extractions run client-side. Only translated text is stored securely in your local Prisma database.
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-space-800">
              {saveSuccess && (
                <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1 animate-fadeIn">
                  <Check className="w-4 h-4" /> Saved to Prisma Database!
                </span>
              )}
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-space-800 hover:bg-space-700 transition"
              >
                Close
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-5 py-2 rounded-xl text-xs font-bold text-space-950 bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 transition shadow-lg flex items-center gap-1.5"
              >
                {saving ? (
                  <>
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-space-950 border-t-transparent animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
