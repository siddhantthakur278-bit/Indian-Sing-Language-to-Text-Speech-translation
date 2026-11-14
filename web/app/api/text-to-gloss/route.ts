import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { text } = body;

    if (!text || typeof text !== "string") {
      return NextResponse.json({ message: "Text input is required." }, { status: 400 });
    }

    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${backendUrl}/api/text-to-gloss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (e) {
      // Backend not running, use edge fallback
    }

    // Client edge fallback dictionary
    const words = text.toUpperCase().replace(/[^A-Z\s]/g, "").split(/\s+/);
    const mockGlossMap: Record<string, string> = {
      "I": "ME", "ME": "ME", "HOSPITAL": "HOSPITAL", "DOCTOR": "DOCTOR",
      "GO": "GO", "GOING": "GO", "WATER": "WATER", "HELP": "HELP",
      "HELLO": "HELLO", "HI": "HELLO", "THANK": "THANK_YOU", "WHERE": "WHERE",
      "WHAT": "WHAT", "POLICE": "POLICE", "AMBULANCE": "AMBULANCE"
    };

    const glosses = words.filter(w => mockGlossMap[w]).map(w => mockGlossMap[w]);
    return NextResponse.json({
      original_text: text,
      glosses: glosses.length > 0 ? glosses : ["HELLO"]
    });
  } catch (err: any) {
    return NextResponse.json({ message: err?.message || "Internal error" }, { status: 500 });
  }
}
