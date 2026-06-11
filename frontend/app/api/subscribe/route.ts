import { NextResponse } from "next/server";

/**
 * Email capture — Phase 1 audience engine. Runs as a Vercel serverless function (free).
 *
 * Provider-pluggable so there's no backend to host:
 *   - BUTTONDOWN_API_KEY  → adds the subscriber to a Buttondown newsletter (free tier)
 *   - SUBSCRIBE_WEBHOOK_URL → POSTs the email to any webhook (Zapier/Make/Google Sheet)
 *   - neither set          → validates + logs (so dev works; wire a provider to go live)
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(req: Request) {
  let email = "";
  try {
    const body = (await req.json()) as { email?: unknown };
    email = String(body.email ?? "").trim().toLowerCase();
  } catch {
    return NextResponse.json({ ok: false, message: "Invalid request." }, { status: 400 });
  }

  if (!EMAIL_RE.test(email) || email.length > 254) {
    return NextResponse.json(
      { ok: false, message: "Please enter a valid email address." },
      { status: 400 }
    );
  }

  try {
    if (process.env.BUTTONDOWN_API_KEY) {
      const res = await fetch("https://api.buttondown.email/v1/subscribers", {
        method: "POST",
        headers: {
          Authorization: `Token ${process.env.BUTTONDOWN_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email_address: email }),
      });
      // 201 = created, 400 = already subscribed → both are fine for the user.
      if (!res.ok && res.status !== 400) {
        console.error("Buttondown error", res.status, await res.text());
        return NextResponse.json(
          { ok: false, message: "Couldn't subscribe right now — try again shortly." },
          { status: 502 }
        );
      }
    } else if (process.env.SUBSCRIBE_WEBHOOK_URL) {
      await fetch(process.env.SUBSCRIBE_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, source: "airadar", ts: new Date().toISOString() }),
      });
    } else {
      console.log("[subscribe] no provider configured — captured:", email);
    }

    return NextResponse.json({ ok: true, message: "You're on the list! 📡" });
  } catch (err) {
    console.error("subscribe failed", err);
    return NextResponse.json(
      { ok: false, message: "Something went wrong. Please try again." },
      { status: 500 }
    );
  }
}
