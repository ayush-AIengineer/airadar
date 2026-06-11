import { getTools } from "@/lib/data";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://airadar-sooty.vercel.app";

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/** Public RSS feed — lets people follow new AI tools without giving an email (distribution). */
export function GET() {
  const { tools } = getTools();
  const items = tools
    .map(
      (t) => `    <item>
      <title>${esc(t.name)}</title>
      <link>${esc(t.url)}</link>
      <description>${esc(t.oneLiner ?? t.description ?? "")}</description>
      <category>${esc(t.categories.join(", "))}</category>
      <guid isPermaLink="false">${esc(t.id)}</guid>
    </item>`
    )
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AIRadar — Newly launched AI tools</title>
    <link>${SITE}</link>
    <description>Newly launched AI tools, enriched and ranked daily.</description>
    <language>en</language>
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
