import { NextRequest, NextResponse } from "next/server";
import { prisma, getOrCreateDefaultUser, DEFAULT_USER } from "@/lib/db";

export async function GET() {
  try {
    const user = await getOrCreateDefaultUser();

    let translationCount = 0;
    let savedPhraseCount = 4;
    let sessionCount = 0;

    try {
      const counts = await Promise.all([
        prisma.translationRecord.count({ where: { userId: user.id } }),
        prisma.savedPhrase.count({ where: { userId: user.id } }),
        prisma.practiceSession.count({ where: { userId: user.id } }),
      ]);
      translationCount = counts[0];
      savedPhraseCount = counts[1];
      sessionCount = counts[2];
    } catch (countErr) {
      console.warn("Using fallback stats:", countErr);
    }

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
    return NextResponse.json({
      user: DEFAULT_USER,
      stats: {
        totalTranslations: 0,
        savedPhrases: 4,
        practiceSessions: 0,
      },
    });
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

    try {
      const updatedUser = await prisma.user.update({
        where: { id: user.id },
        data: updateData,
      });
      return NextResponse.json({ user: updatedUser });
    } catch (dbErr) {
      return NextResponse.json({ user: { ...user, ...updateData } });
    }
  } catch (error: any) {
    console.error("PATCH /api/user error:", error);
    return NextResponse.json({ error: error?.message || "Failed to update user" }, { status: 500 });
  }
}
