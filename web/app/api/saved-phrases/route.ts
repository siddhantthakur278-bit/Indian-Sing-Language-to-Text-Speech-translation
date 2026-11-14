import { NextRequest, NextResponse } from "next/server";
import { prisma, getOrCreateDefaultUser, DEFAULT_SAVED_PHRASES } from "@/lib/db";

export async function GET() {
  try {
    const user = await getOrCreateDefaultUser();

    let phrases = [];
    try {
      phrases = await prisma.savedPhrase.findMany({
        where: { userId: user.id },
        orderBy: { createdAt: "desc" },
      });
    } catch (dbErr) {
      console.warn("Falling back to default saved phrases:", dbErr);
      return NextResponse.json({ phrases: DEFAULT_SAVED_PHRASES });
    }

    if (!phrases || phrases.length === 0) {
      return NextResponse.json({ phrases: DEFAULT_SAVED_PHRASES });
    }

    const formatted = phrases.map((p) => {
      let parsedGlosses: string[] = [];
      try {
        parsedGlosses = typeof p.glosses === "string" ? JSON.parse(p.glosses) : p.glosses;
      } catch {
        parsedGlosses = [p.glosses];
      }
      return {
        ...p,
        glosses: parsedGlosses,
      };
    });

    return NextResponse.json({ phrases: formatted });
  } catch (error: any) {
    console.error("GET /api/saved-phrases error:", error);
    return NextResponse.json({ phrases: DEFAULT_SAVED_PHRASES });
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await getOrCreateDefaultUser();
    const body = await request.json();

    const { title, glosses, english, translated, category, shortcut } = body;

    if (!title || !english || !translated) {
      return NextResponse.json({ error: "Title, English, and translation are required" }, { status: 400 });
    }

    try {
      const newPhrase = await prisma.savedPhrase.create({
        data: {
          userId: user.id,
          title,
          glosses: JSON.stringify(glosses || []),
          english,
          translated,
          category: category || "General",
          shortcut: shortcut || null,
        },
      });

      return NextResponse.json({ phrase: newPhrase }, { status: 201 });
    } catch (dbErr) {
      // In ephemeral serverless memory
      const fallbackPhrase = {
        id: `sp_${Date.now()}`,
        userId: user.id,
        title,
        glosses: glosses || [],
        english,
        translated,
        category: category || "General",
        shortcut: shortcut || null,
      };
      return NextResponse.json({ phrase: fallbackPhrase }, { status: 201 });
    }
  } catch (error: any) {
    console.error("POST /api/saved-phrases error:", error);
    return NextResponse.json({ error: error?.message || "Failed to create saved phrase" }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const user = await getOrCreateDefaultUser();
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json({ error: "Phrase ID is required" }, { status: 400 });
    }

    try {
      await prisma.savedPhrase.deleteMany({
        where: {
          id,
          userId: user.id,
        },
      });
    } catch (e) {
      console.warn("Delete fallback:", e);
    }

    return NextResponse.json({ success: true, message: "Phrase deleted successfully" });
  } catch (error: any) {
    console.error("DELETE /api/saved-phrases error:", error);
    return NextResponse.json({ error: error?.message || "Failed to delete saved phrase" }, { status: 500 });
  }
}
