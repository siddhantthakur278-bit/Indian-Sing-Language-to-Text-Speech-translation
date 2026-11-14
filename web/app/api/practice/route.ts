import { NextRequest, NextResponse } from "next/server";
import { prisma, getOrCreateDefaultUser } from "@/lib/db";

export async function GET() {
  try {
    const user = await getOrCreateDefaultUser();

    const sessions = await prisma.practiceSession.findMany({
      where: { userId: user.id },
      orderBy: { id: "desc" },
      take: 20,
    });

    const totalSessions = sessions.length;
    const avgAccuracy =
      totalSessions > 0
        ? Math.round(
            (sessions.reduce((acc, s) => acc + s.accuracy, 0) / totalSessions) * 10
          ) / 10
        : 0;

    return NextResponse.json({
      sessions,
      stats: {
        totalSessions,
        avgAccuracy,
      },
    });
  } catch (error: any) {
    console.error("GET /api/practice error:", error);
    return NextResponse.json(
      { error: error?.message || "Failed to fetch practice history" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await getOrCreateDefaultUser();
    const body = await request.json();

    const { signsRecognized, durationSeconds, accuracy } = body;

    const session = await prisma.practiceSession.create({
      data: {
        userId: user.id,
        signsRecognized: Number(signsRecognized) || 1,
        durationSeconds: Number(durationSeconds) || 30,
        accuracy: Number(accuracy) || 95.0,
      },
    });

    return NextResponse.json({ session }, { status: 201 });
  } catch (error: any) {
    console.error("POST /api/practice error:", error);
    return NextResponse.json(
      { error: error?.message || "Failed to record practice session" },
      { status: 500 }
    );
  }
}
