"use client";

import { motion } from "framer-motion";
import { Check, Loader2, Rocket } from "lucide-react";
import { useState } from "react";

type Status = "idle" | "loading" | "done" | "error";

export function SubmitToolForm() {
  const [form, setForm] = useState({ toolName: "", url: "", email: "", note: "" });
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  function set(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setForm({ ...form, [field]: e.target.value });
      if (status === "error") setStatus("idle");
    };
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (status === "loading") return;
    setStatus("loading");
    try {
      const res = await fetch("/api/submit-tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
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
        className="flex items-center justify-center gap-2 rounded-2xl border border-brand-400/40 bg-brand-500/15 px-5 py-6 text-sm font-medium text-brand-200"
      >
        <Check className="h-4 w-4" /> {message}
      </motion.div>
    );
  }

  const field =
    "w-full rounded-xl border border-white/12 bg-white/5 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand-400/50 focus:outline-none focus:ring-2 focus:ring-brand-500/30";

  return (
    <form onSubmit={onSubmit} className="mx-auto grid w-full max-w-lg gap-3 text-left">
      <div className="grid gap-3 sm:grid-cols-2">
        <input className={field} placeholder="Tool name" value={form.toolName} onChange={set("toolName")} required />
        <input className={field} type="url" placeholder="https://yourtool.com" value={form.url} onChange={set("url")} required />
      </div>
      <input className={field} type="email" placeholder="Your email" value={form.email} onChange={set("email")} required />
      <textarea className={field} rows={2} placeholder="Anything we should know? (optional)" value={form.note} onChange={set("note")} />
      <button
        type="submit"
        disabled={status === "loading"}
        className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-400 disabled:opacity-70"
      >
        {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
        Submit your tool
      </button>
      {status === "error" && <p className="text-xs text-rose-300">{message}</p>}
    </form>
  );
}
