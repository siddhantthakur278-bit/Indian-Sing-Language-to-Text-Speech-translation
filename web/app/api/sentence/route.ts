import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { glosses, lang } = body;

    if (!glosses || !Array.isArray(glosses) || glosses.length === 0) {
      return NextResponse.json({ message: "Glosses list cannot be empty." }, { status: 400 });
    }

    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${backendUrl}/api/sentence`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ glosses, lang: lang || "hi" }),
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (backendError) {
      // Backend not running; execute intelligent Gemini fallback
      console.warn("Backend unavailable, using direct Gemini integration:", backendError);
    }

    // Emergency guardrails (never let LLM rewrite emergency phrases)
    const emergencyGlosses = new Set(["HELP", "PAIN", "POLICE", "HOSPITAL", "AMBULANCE", "FIRE"]);
    const isEmergency = glosses.some((g: string) => emergencyGlosses.has(g.toUpperCase()));

    let sentence = glosses.join(" ") + ".";
    let translated = sentence;
    const targetLang = lang || "hi";

    if (isEmergency) {
      sentence = "Emergency! Please help me immediately.";
      translated = targetLang === "hi" ? "कृपया तुरंत मेरी सहायता करें, यह एक आपात स्थिति है।" : sentence;
      return NextResponse.json({
        sentence,
        translated,
        lang: targetLang,
        emergency: true,
        audio_url: null,
      });
    }

    // Direct Gemini translation if API key is present
    const apiKey = process.env.LLM_API_KEY;
    if (apiKey) {
      try {
        const model = process.env.LLM_MODEL || "gemini-3.8-flash";
        const prompt = `You convert Indian Sign Language gloss sequences into one natural, polite English sentence, and then translate it into the target language code '${targetLang}'.
ISL word order is Subject-Object-Verb. Reorder and add small function words as needed. Do not add new facts.
Output strictly JSON with keys "sentence" (natural English) and "translated" (in '${targetLang}').
Glosses: ${glosses.join(" ")}`;

        const geminiRes = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              contents: [{ parts: [{ text: prompt }] }],
              generationConfig: {
                responseMimeType: "application/json",
              },
            }),
          }
        );

        if (geminiRes.ok) {
          const geminiData = await geminiRes.json();
          const rawText = geminiData.candidates?.[0]?.content?.parts?.[0]?.text;
          if (rawText) {
            const parsed = JSON.parse(rawText);
            if (parsed.sentence && parsed.translated) {
              return NextResponse.json({
                sentence: parsed.sentence,
                translated: parsed.translated,
                lang: targetLang,
                emergency: false,
                audio_url: null,
              });
            }
          }
        }
      } catch (geminiError) {
        console.warn("Direct Gemini call failed:", geminiError);
      }
    }

    return NextResponse.json({
      sentence,
      translated,
      lang: targetLang,
      emergency: false,
      audio_url: null,
      fallback: true,
    });
  } catch (error: any) {
    return NextResponse.json(
      { message: error?.message || "Internal server error" },
      { status: 500 }
    );
  }
}
