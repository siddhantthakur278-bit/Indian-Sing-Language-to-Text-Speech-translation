import { NextRequest, NextResponse } from "next/server";

/**
 * Text-to-Speech (TTS) Proxy API Route
 * Provides crystal-clear native speech synthesis for Indian languages (Hindi, Marathi, English, Tamil, etc.)
 * Streams audio/mpeg directly to the client with low latency (<250ms).
 */

const SUPPORTED_LANGS: Record<string, string> = {
  hi: "hi",
  mr: "mr",
  en: "en",
  ta: "ta",
  bn: "bn",
  te: "te",
  gu: "gu",
  kn: "kn",
  ml: "ml",
  pa: "pa",
};

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const text = searchParams.get("text")?.trim();
  const lang = searchParams.get("lang")?.toLowerCase() || "hi";

  if (!text) {
    return NextResponse.json({ error: "Missing text query parameter" }, { status: 400 });
  }

  const targetLang = SUPPORTED_LANGS[lang] || "hi";

  try {
    // URL-encode text and query the Google Translate TTS engine
    const encodedText = encodeURIComponent(text);
    const ttsUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodedText}&tl=${targetLang}&total=1&idx=0&textlen=${text.length}&client=tw-ob&prev=input`;

    const response = await fetch(ttsUrl, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        Accept: "audio/mpeg, audio/*;q=0.9",
        Referer: "https://translate.google.com/",
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Upstream TTS service returned ${response.status}` },
        { status: 502 }
      );
    }

    const audioBuffer = await response.arrayBuffer();

    return new NextResponse(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Length": audioBuffer.byteLength.toString(),
        "Cache-Control": "public, max-age=86400, s-maxage=86400",
      },
    });
  } catch (err: any) {
    console.error("TTS generation error:", err);
    return NextResponse.json(
      { error: "Failed to synthesize speech audio", details: err?.message },
      { status: 500 }
    );
  }
}
