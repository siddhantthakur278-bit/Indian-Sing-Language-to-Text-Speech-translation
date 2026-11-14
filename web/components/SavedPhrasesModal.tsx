"use client";

import React, { useState, useEffect } from "react";
import { Bookmark, Plus, Trash2, Volume2, Sparkles, X, Check, ArrowRight } from "lucide-react";
import { speakText } from "@/lib/speech";

interface SavedPhraseItem {
  id: string;
  title: string;
  glosses: string[];
  english: string;
  translated: string;
  category: string;
  shortcut?: string | null;
}

interface SavedPhrasesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPhrase: (glosses: string[], english: string, translated: string) => void;
  targetLang: string;
}

export const SavedPhrasesModal: React.FC<SavedPhrasesModalProps> = ({
  isOpen,
  onClose,
  onSelectPhrase,
  targetLang,
}) => {
  const [phrases, setPhrases] = useState<SavedPhraseItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showAddForm, setShowAddForm] = useState<boolean>(false);

  // New phrase form state
  const [newTitle, setNewTitle] = useState("");
  const [newGlosses, setNewGlosses] = useState("");
  const [newEnglish, setNewEnglish] = useState("");
  const [newTranslated, setNewTranslated] = useState("");
  const [newCategory, setNewCategory] = useState("Daily");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchPhrases = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/saved-phrases");
      const data = await res.json();
      if (data.phrases) {
        setPhrases(data.phrases);
      }
    } catch (err) {
      console.error("Failed to fetch saved phrases:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchPhrases();
    }
  }, [isOpen]);

  const handleCreatePhrase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newEnglish.trim() || !newTranslated.trim()) return;

    setIsSubmitting(true);
    try {
      const parsedGlosses = newGlosses
        .split(/[\s,]+/)
        .map((g) => g.trim().toUpperCase())
        .filter(Boolean);

      const res = await fetch("/api/saved-phrases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle.trim(),
          glosses: parsedGlosses,
          english: newEnglish.trim(),
          translated: newTranslated.trim(),
          category: newCategory,
        }),
      });

      if (res.ok) {
        setNewTitle("");
        setNewGlosses("");
        setNewEnglish("");
        setNewTranslated("");
        setShowAddForm(false);
        fetchPhrases();
      }
    } catch (err) {
      console.error("Failed to add phrase:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/saved-phrases?id=${id}`, { method: "DELETE" });
      if (res.ok) {
        setPhrases((prev) => prev.filter((p) => p.id !== id));
      }
    } catch (err) {
      console.error("Failed to delete phrase:", err);
    }
  };

  const handlePlayAudio = (phrase: SavedPhraseItem, e: React.MouseEvent) => {
    e.stopPropagation();
    speakText(phrase.translated, targetLang, 1.0);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl bg-space-900 border border-gold-500/30 shadow-2xl overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-gold-500 via-ruby-500 to-white" />

        {/* Modal Header */}
        <div className="p-5 border-b border-space-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400 to-ruby-600 flex items-center justify-center text-space-950 font-bold shadow-md">
              <Bookmark className="w-5 h-5 text-space-950" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Saved Quick Phrases
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gold-500/20 text-gold-300 border border-gold-500/30">
                  Prisma DB
                </span>
              </h2>
              <p className="text-xs text-slate-400">Click any phrase to load and pronounce it immediately</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-3 py-1.5 rounded-xl text-xs font-bold text-space-950 bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 transition flex items-center gap-1.5 shadow-md"
            >
              <Plus className="w-4 h-4" />
              <span>{showAddForm ? "Cancel" : "Add Phrase"}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {/* Add Phrase Form */}
          {showAddForm && (
            <form onSubmit={handleCreatePhrase} className="p-4 rounded-xl bg-space-850 border border-gold-500/40 space-y-3 animate-fadeIn">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gold-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Add New Phrase to Database
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Title</label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Call Doctor"
                    className="w-full px-3 py-1.5 rounded-lg bg-space-900 border border-space-700 text-white text-xs focus:border-gold-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-space-900 border border-space-700 text-white text-xs focus:border-gold-500 focus:outline-none"
                  >
                    <option value="Emergency">🚨 Emergency</option>
                    <option value="Medical">🏥 Medical</option>
                    <option value="Daily">☀️ Daily</option>
                    <option value="Greetings">👋 Greetings</option>
                    <option value="Questions">❓ Questions</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  ISL Glosses (Space separated)
                </label>
                <input
                  type="text"
                  value={newGlosses}
                  onChange={(e) => setNewGlosses(e.target.value)}
                  placeholder="e.g. ME DOCTOR CALL"
                  className="w-full px-3 py-1.5 rounded-lg bg-space-900 border border-space-700 text-white text-xs focus:border-gold-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">English Sentence</label>
                  <input
                    type="text"
                    required
                    value={newEnglish}
                    onChange={(e) => setNewEnglish(e.target.value)}
                    placeholder="e.g. Please call a doctor."
                    className="w-full px-3 py-1.5 rounded-lg bg-space-900 border border-space-700 text-white text-xs focus:border-gold-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Target Language Translation</label>
                  <input
                    type="text"
                    required
                    value={newTranslated}
                    onChange={(e) => setNewTranslated(e.target.value)}
                    placeholder="e.g. कृपया डॉक्टर को बुलाएं।"
                    className="w-full px-3 py-1.5 rounded-lg bg-space-900 border border-space-700 text-white text-xs focus:border-gold-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold text-space-950 bg-gold-400 hover:bg-gold-300 transition"
                >
                  {isSubmitting ? "Saving..." : "Save to DB"}
                </button>
              </div>
            </form>
          )}

          {/* List of phrases */}
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2">
              <div className="w-7 h-7 rounded-full border-2 border-gold-500 border-t-transparent animate-spin" />
              <p className="text-xs text-slate-400">Loading saved phrases from database...</p>
            </div>
          ) : phrases.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              No saved phrases yet. Click &quot;Add Phrase&quot; above to create one!
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-2.5">
              {phrases.map((phrase) => (
                <div
                  key={phrase.id}
                  onClick={() => {
                    onSelectPhrase(phrase.glosses, phrase.english, phrase.translated);
                    onClose();
                  }}
                  className="p-3.5 rounded-xl bg-space-850 hover:bg-space-800 border border-space-700/60 hover:border-gold-500/40 transition cursor-pointer flex items-center justify-between group shadow-sm"
                >
                  <div className="flex-1 pr-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-sm text-white group-hover:text-gold-300 transition">
                        {phrase.title}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-space-950 border border-space-700 text-slate-300">
                        {phrase.category}
                      </span>
                      {phrase.glosses && phrase.glosses.length > 0 && (
                        <div className="flex gap-1">
                          {phrase.glosses.slice(0, 3).map((g, idx) => (
                            <span key={idx} className="text-[10px] px-1.5 py-0.2 rounded bg-gold-500/10 text-gold-400 border border-gold-500/20 font-mono">
                              {g}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-slate-300">{phrase.english}</div>
                    <div className="text-xs font-semibold text-gold-400 mt-0.5">{phrase.translated}</div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => handlePlayAudio(phrase, e)}
                      title="Play Pronunciation"
                      className="p-2 rounded-lg bg-space-950 text-slate-300 hover:text-gold-400 border border-space-700 hover:border-gold-500/50 transition"
                    >
                      <Volume2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(phrase.id);
                      }}
                      title="Delete Phrase"
                      className="p-2 rounded-lg bg-space-950 text-slate-400 hover:text-ruby-400 border border-space-700 hover:border-ruby-500/50 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <div className="p-2 text-slate-500 group-hover:text-gold-400 transition">
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
