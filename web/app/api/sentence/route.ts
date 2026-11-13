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
      // Backend not running; execute client-side fallback
      console.warn("Backend unavailable, using edge fallback:", backendError);
    }

    // Client-side emergency check fallback
    const emergencyGlosses = new Set(["HELP", "PAIN", "POLICE", "HOSPITAL", "AMBULANCE", "FIRE"]);
    const isEmergency = glosses.some((g: string) => emergencyGlosses.has(g.toUpperCase()));

    let fallbackSentence = glosses.join(" ") + ".";
    if (isEmergency) {
      fallbackSentence = "Emergency! Please help me immediately.";
    }

    return NextResponse.json({
      sentence: fallbackSentence,
      translated: fallbackSentence,
      lang: lang || "hi",
      emergency: isEmergency,
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
