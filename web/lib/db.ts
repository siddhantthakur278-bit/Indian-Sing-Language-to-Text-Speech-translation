import { PrismaClient } from "@prisma/client";

const globalForPrisma = global as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

/**
 * Ensures a default active user and initial saved bookmark phrases exist in the database.
 */
export async function getOrCreateDefaultUser() {
  let user = await prisma.user.findFirst();
  if (!user) {
    user = await prisma.user.create({
      data: {
        name: "Siddhant",
        email: "siddhant@isl-translator.org",
        role: "Signer",
        preferredLang: "hi",
        speechRate: 1.0,
        autoSpeak: true,
        signMode: "auto",
        theme: "galaxy-gold",
      },
    });

    await prisma.savedPhrase.createMany({
      data: [
        {
          userId: user.id,
          title: "Need Hospital Immediately",
          glosses: JSON.stringify(["ME", "HOSPITAL", "GO"]),
          english: "I need to go to the hospital.",
          translated: "मुझे अस्पताल जाना है।",
          category: "Emergency",
          shortcut: "H",
        },
        {
          userId: user.id,
          title: "Want Water",
          glosses: JSON.stringify(["ME", "WATER", "WANT"]),
          english: "I want water.",
          translated: "मुझे पानी चाहिए।",
          category: "Daily",
          shortcut: "W",
        },
        {
          userId: user.id,
          title: "Hello Friend",
          glosses: JSON.stringify(["HELLO", "FRIEND"]),
          english: "Hello, friend.",
          translated: "नमस्ते दोस्त।",
          category: "Greetings",
          shortcut: "G",
        },
        {
          userId: user.id,
          title: "Please Help Me",
          glosses: JSON.stringify(["PLEASE", "HELP", "ME"]),
          english: "Please help me.",
          translated: "कृपया मेरी सहायता करें।",
          category: "Emergency",
          shortcut: "P",
        },
      ],
    });
  }
  return user;
}
