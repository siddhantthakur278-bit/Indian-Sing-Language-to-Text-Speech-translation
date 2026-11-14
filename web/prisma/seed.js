const { PrismaClient } = require("@prisma/client");

const prisma = new PrismaClient();

async function main() {
  console.log("Seeding database with default user and curated ISL phrases...");

  // 1. Create or update default user
  const user = await prisma.user.upsert({
    where: { email: "siddhant@isl-translator.org" },
    update: {},
    create: {
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

  console.log(`Default user verified: ${user.name} (${user.id})`);

  // 2. Curated Starter Phrases
  const starterPhrases = [
    {
      title: "Need Hospital Immediately",
      glosses: JSON.stringify(["ME", "HOSPITAL", "GO"]),
      english: "I need to go to the hospital.",
      translated: "मुझे तुरंत अस्पताल जाना है।",
      category: "Emergency",
      shortcut: "H",
    },
    {
      title: "Want Drinking Water",
      glosses: JSON.stringify(["ME", "WATER", "WANT"]),
      english: "I want water to drink.",
      translated: "मुझे पीने का पानी चाहिए।",
      category: "Daily",
      shortcut: "W",
    },
    {
      title: "Namaste Friend",
      glosses: JSON.stringify(["HELLO", "FRIEND"]),
      english: "Hello, friend.",
      translated: "नमस्ते दोस्त।",
      category: "Greetings",
      shortcut: "G",
    },
    {
      title: "Please Help Me",
      glosses: JSON.stringify(["PLEASE", "HELP", "ME"]),
      english: "Please help me.",
      translated: "कृपया मेरी सहायता करें।",
      category: "Emergency",
      shortcut: "P",
    },
    {
      title: "Need Pain Medicine",
      glosses: JSON.stringify(["ME", "PAIN", "MEDICINE", "NEED"]),
      english: "I need medicine for pain.",
      translated: "मुझे दर्द की दवा चाहिए।",
      category: "Medical",
      shortcut: "M",
    },
    {
      title: "Where is Railway Station",
      glosses: JSON.stringify(["STATION", "WHERE"]),
      english: "Where is the railway station?",
      translated: "रेलवे स्टेशन कहाँ है?",
      category: "Travel",
      shortcut: "T",
    },
    {
      title: "What is Your Name",
      glosses: JSON.stringify(["YOU", "NAME", "WHAT"]),
      english: "What is your name?",
      translated: "आपका नाम क्या है?",
      category: "Greetings",
      shortcut: "N",
    },
    {
      title: "I am Hungry",
      glosses: JSON.stringify(["ME", "FOOD", "WANT"]),
      english: "I am hungry and need food.",
      translated: "मुझे भूख लगी है, खाना चाहिए।",
      category: "Daily",
      shortcut: "F",
    },
  ];

  for (const phrase of starterPhrases) {
    const existing = await prisma.savedPhrase.findFirst({
      where: {
        userId: user.id,
        title: phrase.title,
      },
    });

    if (!existing) {
      await prisma.savedPhrase.create({
        data: {
          ...phrase,
          userId: user.id,
        },
      });
    }
  }

  // 3. Initial Practice Session Record
  const existingSession = await prisma.practiceSession.findFirst({
    where: { userId: user.id },
  });

  if (!existingSession) {
    await prisma.practiceSession.create({
      data: {
        userId: user.id,
        signsRecognized: 12,
        durationSeconds: 180,
        accuracy: 94.5,
      },
    });
  }

  console.log("Database seeded successfully!");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
