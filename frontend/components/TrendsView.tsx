"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Radar, TrendingUp } from "lucide-react";
import Link from "next/link";
import { AuroraBackground } from "@/components/AuroraBackground";
import { SubscribeForm } from "@/components/SubscribeForm";
import type { Insights } from "@/lib/insights";
import type { Pricing } from "@/lib/types";
import { PRICING_LABELS } from "@/lib/utils";

function Bar({ label, value, max, delay = 0 }: { label: string; value: number; max: number; delay?: number }) {
  const pct = max ? Math.round((value / max) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-200">{label}</span>
        <span className="font-mono text-slate-400">{value}</span>
      </div>
      <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-white/5">
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay, ease: "easeOut" }}
          className="h-full rounded-full bg-gradient-to-r from-brand-600 to-brand-300"
        />
      </div>
    </div>
  );
}

export function TrendsView({ insights }: { insights: Insights }) {
  const catMax = insights.categories[0]?.count ?? 1;
  const priceMax = insights.pricing[0]?.count ?? 1;

  return (
    <main className="relative min-h-screen">
      <AuroraBackground />

      <header className="sticky top-0 z-40 border-b border-white/5 bg-ink-950/60 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between px-6 py-3 lg:px-10">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-500 font-display text-sm font-bold text-white">
              A
            </span>
            <span className="font-display text-lg font-semibold tracking-tight">AIRadar</span>
          </Link>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition hover:text-slate-100"
          >
            <ArrowLeft className="h-4 w-4" /> Back to radar
          </Link>
        </div>
      </header>

      <div className="mx-auto w-full max-w-[1400px] px-6 py-12 lg:px-10">
        {/* Hero */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/5 px-3 py-1 text-xs text-slate-300">
            <TrendingUp className="h-3.5 w-3.5 text-brand-400" /> Weekly trends
          </span>
          <h1 className="mt-4 text-3xl font-bold sm:text-5xl">
            This week on the <span className="text-gradient">radar</span>
          </h1>
          <p className="mt-3 max-w-xl text-slate-400">
            A live read of what's launching in AI — categories heating up, how tools are
            priced, and the highest-signal launches. Refreshed daily.
          </p>
        </motion.div>

        {/* Summary stats */}
        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Tools tracked", value: insights.total },
            { label: "Avg quality", value: insights.avgQuality },
            { label: "Open-source", value: `${insights.openSourcePct}%` },
            { label: "Free / OSS", value: `${insights.freePct}%` },
          ].map((s) => (
            <div key={s.label} className="glass rounded-2xl p-5">
              <div className="font-mono text-3xl font-bold text-gradient">{s.value}</div>
              <div className="mt-1 text-sm text-slate-400">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Bars */}
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="glass rounded-2xl p-6">
            <h2 className="mb-5 flex items-center gap-2 text-lg font-semibold">
              <Radar className="h-5 w-5 text-brand-400" /> Hottest categories
            </h2>
            <div className="space-y-4">
              {insights.categories.slice(0, 8).map((c, i) => (
                <Bar key={c.key} label={c.key} value={c.count} max={catMax} delay={i * 0.05} />
              ))}
            </div>
          </div>

          <div className="glass rounded-2xl p-6">
            <h2 className="mb-5 text-lg font-semibold">Pricing mix</h2>
            <div className="space-y-4">
              {insights.pricing.map((p, i) => (
                <Bar
                  key={p.key}
                  label={PRICING_LABELS[p.key as Pricing] ?? p.key}
                  value={p.count}
                  max={priceMax}
                  delay={i * 0.05}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Top tools */}
        <div className="mt-6 glass rounded-2xl p-6">
          <h2 className="mb-4 text-lg font-semibold">Top launches by quality</h2>
          <div className="divide-y divide-white/5">
            {insights.topTools.map((t, i) => (
              <a
                key={t.id}
                href={t.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-4 py-3 transition hover:opacity-80"
              >
                <span className="font-mono text-sm text-slate-500">{String(i + 1).padStart(2, "0")}</span>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium text-slate-100">{t.name}</div>
                  {t.oneLiner && <div className="truncate text-sm text-slate-500">{t.oneLiner}</div>}
                </div>
                <span className="font-mono text-sm text-brand-300">{t.quality}</span>
              </a>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-8 glass rounded-3xl px-6 py-10 text-center">
          <h2 className="text-2xl font-bold">Get the weekly trends in your inbox</h2>
          <p className="mx-auto mt-2 max-w-md text-slate-400">
            One email, the signal only. The launches and shifts worth knowing.
          </p>
          <div className="mt-6">
            <SubscribeForm />
          </div>
        </div>
      </div>
    </main>
  );
}
