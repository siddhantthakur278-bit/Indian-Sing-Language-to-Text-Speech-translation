import { NextRequest, NextResponse } from "next/server";
import { prisma, getOrCreateDefaultUser } from "@/lib/db";

export async function GET() {
  try {
    const user = await getOrCreateDefaultUser();

    // Fetch user statistics
    const [translationCount, savedPhraseCount, sessionCount] = await Promise.all([
      prisma.translationRecord.count({ where: { userId: user.id } }),
      prisma.savedPhrase.count({ where: { userId: user.id } }),
      prisma.practiceSession.count({ where: { userId: user.id } }),
    ]);

    return NextResponse.json({
      user,
      stats: {
        totalTranslations: translationCount,
        savedPhrases: savedPhraseCount,
        practiceSessions: sessionCount,
      },
    });
  } catch (error: any) {
    console.error("GET /api/user error:", error);
    return NextResponse.json({ error: error?.message || "Failed to load user" }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const user = await getOrCreateDefaultUser();
    const body = await request.json();

    const allowedFields = [
      "name",
      "role",
      "preferredLang",
      "speechRate",
      "autoSpeak",
      "signMode",
      "theme",
      "avatarUrl",
    ];

    const updateData: Record<string, any> = {};
    for (const key of allowedFields) {
      if (body[key] !== undefined) {
        updateData[key] = body[key];
      }
    }

    const updatedUser = await prisma.user.update({
      where: { id: user.id },
      data: updateData,
    });

    return NextResponse.json({ user: updatedUser });
  } catch (error: any) {
    console.error("PATCH /api/user error:", error);
    return NextResponse.json({ error: error?.message || "Failed to update user" }, { status: 500 });
  }
}
