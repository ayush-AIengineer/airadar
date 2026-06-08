import type { Metadata } from "next";
import { Inter, Sora, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Body: Inter — the gold-standard professional UI typeface.
const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
// Headings: Sora — a clean, confident geometric display face.
const display = Sora({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

// Set NEXT_PUBLIC_SITE_URL in Vercel to the production domain so OG/canonical URLs resolve.
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const TITLE = "AIRadar — Daily intelligence on new AI tools";
const DESCRIPTION =
  "Every AI product launching across the web — discovered, enriched, deduplicated and ranked. Updated daily.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: "%s · AIRadar" },
  description: DESCRIPTION,
  applicationName: "AIRadar",
  keywords: [
    "AI tools",
    "new AI tools",
    "AI product launches",
    "AI directory",
    "AI tool discovery",
    "generative AI",
  ],
  authors: [{ name: "AIRadar" }],
  openGraph: {
    type: "website",
    siteName: "AIRadar",
    url: SITE_URL,
    title: TITLE,
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable} ${mono.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
