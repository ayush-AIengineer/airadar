import { NextResponse } from "next/server";

/**
 * "Submit your AI tool" — Phase 2 revenue funnel. Captures tool submissions (for free
 * listing review and paid Featured placement). Serverless + provider-pluggable:
 *   - SUBMIT_WEBHOOK_URL → POSTs the submission anywhere (Slack/Sheet/Zapier/email)
 *   - else                → logs it (so dev works; wire a webhook to receive leads)
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_RE = /^https?:\/\/.+\..+/;

export async function POST(req: Request) {
  let data: { toolName?: unknown; url?: unknown; email?: unknown; note?: unknown };
  try {
    data = (await req.json()) as typeof data;
  } catch {
    return NextResponse.json({ ok: false, message: "Invalid request." }, { status: 400 });
  }

  const toolName = String(data.toolName ?? "").trim().slice(0, 120);
  const url = String(data.url ?? "").trim().slice(0, 400);
  const email = String(data.email ?? "").trim().toLowerCase().slice(0, 254);
  const note = String(data.note ?? "").trim().slice(0, 1000);

  if (!toolName) {
    return NextResponse.json({ ok: false, message: "Tool name is required." }, { status: 400 });
  }
  if (!URL_RE.test(url)) {
    return NextResponse.json(
      { ok: false, message: "Please enter a valid tool URL (https://…)." },
      { status: 400 }
    );
  }
  if (!EMAIL_RE.test(email)) {
    return NextResponse.json(
      { ok: false, message: "Please enter a valid contact email." },
      { status: 400 }
    );
  }

  const submission = { toolName, url, email, note, source: "airadar", ts: new Date().toISOString() };
  try {
    if (process.env.SUBMIT_WEBHOOK_URL) {
      await fetch(process.env.SUBMIT_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submission),
      });
    } else {
      console.log("[submit-tool] no webhook configured — submission:", submission);
    }
    return NextResponse.json({ ok: true, message: "Submitted! We'll review it shortly. 🚀" });
  } catch (err) {
    console.error("submit-tool failed", err);
    return NextResponse.json(
      { ok: false, message: "Something went wrong. Please try again." },
      { status: 500 }
    );
  }
}
