import { PrismaClient } from "@prisma/client";
import fs from "fs";
import path from "path";

const globalForPrisma = global as unknown as { prisma: PrismaClient };

function getDatabaseUrl(): string {
  if (process.env.VERCEL) {
    const tmpDbPath = "/tmp/dev.db";
    if (!fs.existsSync(tmpDbPath)) {
      const candidatePaths = [
        path.join(process.cwd(), "prisma", "dev.db"),
        path.join(process.cwd(), "dev.db"),
      ];
      for (const p of candidatePaths) {
        if (fs.existsSync(p)) {
          try {
            fs.copyFileSync(p, tmpDbPath);
          } catch (e) {
            console.warn("Failed to copy sqlite db to /tmp:", e);
          }
          break;
        }
      }
    }
    return `file:${tmpDbPath}`;
  }
  return process.env.DATABASE_URL || "file:./dev.db";
}

const dbUrl = getDatabaseUrl();

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    datasources: {
      db: {
        url: dbUrl,
      },
    },
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

// Default in-memory fallbacks if SQLite filesystem is constrained in ephemeral lambdas
export const DEFAULT_USER = {
  id: "user_default_siddhant",
  name: "Siddhant",
  email: "siddhant@isl-translator.org",
  role: "Signer",
  preferredLang: "hi",
  speechRate: 1.0,
  autoSpeak: true,
  signMode: "auto",
  theme: "galaxy-gold",
};

export const DEFAULT_SAVED_PHRASES = [
  {
    id: "sp_1",
    userId: "user_default_siddhant",
    title: "Need Hospital Immediately",
    glosses: ["ME", "HOSPITAL", "GO"],
    english: "I need to go to the hospital.",
    translated: "मुझे तुरंत अस्पताल जाना है।",
    category: "Emergency",
    shortcut: "H",
  },
  {
    id: "sp_2",
    userId: "user_default_siddhant",
    title: "Want Drinking Water",
    glosses: ["ME", "WATER", "WANT"],
    english: "I want water to drink.",
    translated: "मुझे पीने का पानी चाहिए।",
    category: "Daily",
    shortcut: "W",
  },
  {
    id: "sp_3",
    userId: "user_default_siddhant",
    title: "Namaste Friend",
    glosses: ["HELLO", "FRIEND"],
    english: "Hello, friend.",
    translated: "नमस्ते दोस्त।",
    category: "Greetings",
    shortcut: "G",
  },
  {
    id: "sp_4",
    userId: "user_default_siddhant",
    title: "Please Help Me",
    glosses: ["PLEASE", "HELP", "ME"],
    english: "Please help me.",
    translated: "कृपया मेरी सहायता करें।",
    category: "Emergency",
    shortcut: "P",
  },
];

/**
 * Ensures a default active user and initial saved bookmark phrases exist in the database,
 * with graceful in-memory fallback for read-only serverless lambdas.
 */
export async function getOrCreateDefaultUser() {
  try {
    let user = await prisma.user.findFirst();
    if (!user) {
      user = await prisma.user.create({
        data: DEFAULT_USER,
      });

      await prisma.savedPhrase.createMany({
        data: DEFAULT_SAVED_PHRASES.map((p) => ({
          ...p,
          glosses: JSON.stringify(p.glosses),
        })),
      });
    }
    return user;
  } catch (err) {
    console.warn("Prisma SQLite DB query fallback active:", err);
    return DEFAULT_USER as any;
  }
}
