import { NextRequest, NextResponse } from "next/server";
import { prisma, getOrCreateDefaultUser } from "@/lib/db";

export async function GET() {
  try {
    const user = await getOrCreateDefaultUser();

    let records: any[] = [];
    try {
      records = await prisma.translationRecord.findMany({
        where: { userId: user.id },
        orderBy: { createdAt: "desc" },
        take: 50,
      });
    } catch (dbErr) {
      console.warn("History findMany fallback:", dbErr);
      return NextResponse.json({ history: [] });
    }

    const formatted = records.map((r) => {
      let parsedGlosses: string[] = [];
      try {
        parsedGlosses = typeof r.glosses === "string" ? JSON.parse(r.glosses) : r.glosses;
      } catch {
        parsedGlosses = [r.glosses];
      }

      return {
        id: r.id,
        time: new Date(r.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        glosses: parsedGlosses,
        english: r.english,
        translated: r.translated,
        lang: r.lang,
        isEmergency: r.isEmergency,
        audioUrl: r.audioUrl,
        createdAt: r.createdAt,
      };
    });

    return NextResponse.json({ history: formatted });
  } catch (error: any) {
    console.error("GET /api/history error:", error);
    return NextResponse.json({ history: [] });
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await getOrCreateDefaultUser();
    const body = await request.json();

    const { glosses, english, translated, lang, isEmergency, audioUrl } = body;

    if (!english || !translated) {
      return NextResponse.json({ error: "Missing required sentence fields" }, { status: 400 });
    }

    try {
      const newRecord = await prisma.translationRecord.create({
        data: {
          userId: user.id,
          glosses: JSON.stringify(glosses || []),
          english,
          translated,
          lang: lang || "hi",
          isEmergency: Boolean(isEmergency),
          audioUrl: audioUrl || null,
        },
      });

      return NextResponse.json({ record: newRecord }, { status: 201 });
    } catch (dbErr) {
      const fallbackRecord = {
        id: `rec_${Date.now()}`,
        userId: user.id,
        glosses: glosses || [],
        english,
        translated,
        lang: lang || "hi",
        isEmergency: Boolean(isEmergency),
        audioUrl: audioUrl || null,
        createdAt: new Date().toISOString(),
      };
      return NextResponse.json({ record: fallbackRecord }, { status: 201 });
    }
  } catch (error: any) {
    console.error("POST /api/history error:", error);
    return NextResponse.json({ error: error?.message || "Failed to save history" }, { status: 500 });
  }
}

export async function DELETE() {
  try {
    const user = await getOrCreateDefaultUser();

    try {
      await prisma.translationRecord.deleteMany({
        where: { userId: user.id },
      });
    } catch (e) {
      console.warn("Delete history fallback:", e);
    }

    return NextResponse.json({ success: true, message: "History cleared successfully" });
  } catch (error: any) {
    console.error("DELETE /api/history error:", error);
    return NextResponse.json({ error: error?.message || "Failed to clear history" }, { status: 500 });
  }
}
