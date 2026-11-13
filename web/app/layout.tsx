import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ISL Translator - Indian Sign Language to Text & Speech",
  description: "Real-time AI assistive communication bridge translating Indian Sign Language (ISL) gestures into text and speech in multiple Indian languages.",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-navy-dark text-slate-100 antialiased selection:bg-teal selection:text-navy-dark">
        {children}
      </body>
    </html>
  );
}
