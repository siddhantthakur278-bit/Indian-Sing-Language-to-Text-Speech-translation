/**
 * Client-Side Text-to-Speech (TTS) Engine using Web Speech API (speechSynthesis)
 * Provides zero-cost, immediate voice playback for Indian Languages.
 */

export const LANG_CODE_TO_LOCALE: Record<string, string> = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
  ta: "ta-IN",
  bn: "bn-IN",
  te: "te-IN",
  gu: "gu-IN",
  kn: "kn-IN",
  ml: "ml-IN",
  pa: "pa-IN",
};

export function speakText(
  text: string,
  langCode: string = "hi",
  rate: number = 1.0,
  onEnd?: () => void,
  onError?: (err: string) => void
): boolean {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    onError?.("Web Speech API is not supported on this browser.");
    return false;
  }

  const locale = LANG_CODE_TO_LOCALE[langCode.toLowerCase()] || "en-IN";
  window.speechSynthesis.cancel(); // Stop prior speech

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = locale;
  utterance.rate = rate;

  const voices = window.speechSynthesis.getVoices();
  const matchedVoice = voices.find((v) => v.lang === locale || v.lang.startsWith(langCode));

  if (matchedVoice) {
    utterance.voice = matchedVoice;
  }

  utterance.onend = () => {
    onEnd?.();
  };

  utterance.onerror = (e) => {
    onError?.(e.error || "Speech synthesis failed");
  };

  window.speechSynthesis.speak(utterance);
  return true;
}

export function stopSpeaking(): void {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
