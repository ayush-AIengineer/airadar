"use client";

import { motion } from "framer-motion";
import { Check, Loader2, Send } from "lucide-react";
import { useState } from "react";

type Status = "idle" | "loading" | "done" | "error";

export function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (status === "loading") return;
    setStatus("loading");
    try {
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = (await res.json()) as { ok: boolean; message: string };
      if (res.ok && data.ok) {
        setStatus("done");
        setMessage(data.message);
      } else {
        setStatus("error");
        setMessage(data.message ?? "Please try again.");
      }
    } catch {
      setStatus("error");
      setMessage("Network error — please try again.");
    }
  }

  if (status === "done") {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center justify-center gap-2 rounded-full border border-brand-400/40 bg-brand-500/15 px-5 py-3 text-sm font-medium text-brand-200"
      >
        <Check className="h-4 w-4" /> {message}
      </motion.div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto w-full max-w-md">
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (status === "error") setStatus("idle");
          }}
          placeholder="you@company.com"
          className="w-full rounded-full border border-white/12 bg-white/5 px-5 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand-400/50 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full bg-brand-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-400 disabled:opacity-70"
        >
          {status === "loading" ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          Subscribe
        </button>
      </div>
      {status === "error" && <p className="mt-2 text-xs text-rose-300">{message}</p>}
      <p className="mt-2 text-xs text-slate-500">Free · daily digest · unsubscribe anytime.</p>
    </form>
  );
}
