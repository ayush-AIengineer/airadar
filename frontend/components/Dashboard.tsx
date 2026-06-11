"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Radar, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { AuroraBackground } from "@/components/AuroraBackground";
import { FilterSidebar, type FilterState } from "@/components/FilterSidebar";
import { RadarHero } from "@/components/RadarHero";
import { Scene3DBackground } from "@/components/Scene3DBackground";
import { StatCard } from "@/components/StatCard";
import { SubscribeForm } from "@/components/SubscribeForm";
import { ToolCard } from "@/components/ToolCard";
import type { Pricing, Tool } from "@/lib/types";

export function Dashboard({ tools }: { tools: Tool[] }) {
  const [filters, setFilters] = useState<FilterState>({
    query: "",
    categories: new Set(),
    pricings: new Set(),
    minQuality: 0,
  });

  const categoryCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const t of tools) for (const c of t.categories) counts.set(c, (counts.get(c) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [tools]);

  const pricingOptions = useMemo(
    () => [...new Set(tools.map((t) => t.pricing))].sort() as Pricing[],
    [tools]
  );

  const filtered = useMemo(() => {
    const q = filters.query.trim().toLowerCase();
    return tools
      .filter((t) => {
        if (t.quality < filters.minQuality) return false;
        if (filters.pricings.size && !filters.pricings.has(t.pricing)) return false;
        if (filters.categories.size && !t.categories.some((c) => filters.categories.has(c)))
          return false;
        if (
          q &&
          !`${t.name} ${t.oneLiner ?? ""} ${t.categories.join(" ")}`.toLowerCase().includes(q)
        )
          return false;
        return true;
      })
      .sort((a, b) => b.quality - a.quality);
  }, [tools, filters]);

  const avgQuality = tools.length
    ? Math.round(tools.reduce((s, t) => s + t.quality, 0) / tools.length)
    : 0;

  return (
    <main id="top" className="relative min-h-screen">
      <AuroraBackground />
      <Scene3DBackground />

      {/* ── Header ── */}
      <header className="sticky top-0 z-40 border-b border-white/5 bg-ink-950/60 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-[1920px] items-center justify-between px-6 py-3 lg:px-12">
          <a href="#top" className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-500 font-display text-sm font-bold text-white">
              A
            </span>
            <span className="font-display text-lg font-semibold tracking-tight">AIRadar</span>
          </a>
          <nav className="flex items-center gap-6 text-sm text-slate-400">
            <a href="#tools" className="transition hover:text-slate-100">
              Tools
            </a>
            <a href="#how" className="transition hover:text-slate-100">
              How it works
            </a>
          </nav>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative mx-auto w-full max-w-[1920px] px-6 pt-8 lg:px-12">
        <div className="relative overflow-hidden rounded-3xl border border-white/10">
          <div className="absolute inset-0">
            <RadarHero />
          </div>
          <div className="relative z-10 flex h-[460px] flex-col justify-center px-8 sm:h-[560px] sm:px-16">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7 }}
              className="max-w-2xl"
            >
              <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-slate-300 backdrop-blur">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-brand-500" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-500" />
                </span>
                Live pipeline · {tools.length} tools enriched
              </span>
              <h1 className="mt-5 text-4xl font-bold leading-[1.08] tracking-tight sm:text-6xl xl:text-7xl">
                The <span className="text-gradient">AI tool radar</span> that never sleeps
              </h1>
              <p className="mt-5 max-w-lg text-base text-slate-400 sm:text-lg">
                Every AI product launching across the web — discovered, enriched, deduplicated
                and ranked. Updated daily.
              </p>
              <div className="mt-6 flex items-center gap-3 text-sm text-slate-400">
                <Sparkles className="h-4 w-4 text-brand-400" />
                Move your cursor — the radar tracks you.
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="mx-auto mt-8 grid w-full max-w-[1920px] grid-cols-2 gap-4 px-6 sm:grid-cols-4 lg:px-12">
        <StatCard label="Tools tracked" value={tools.length} delay={0} />
        <StatCard label="Avg quality score" value={avgQuality} delay={0.1} />
        <StatCard label="Categories" value={categoryCounts.length} delay={0.2} />
        <StatCard label="Sources live" value={1} delay={0.3} />
      </section>

      {/* ── Catalog ── */}
      <section
        id="tools"
        className="mx-auto mt-12 grid w-full max-w-[1920px] grid-cols-1 gap-8 px-6 pb-20 lg:grid-cols-[300px_1fr] lg:px-12 scroll-mt-20"
      >
        <FilterSidebar
          categoryCounts={categoryCounts}
          pricingOptions={pricingOptions}
          state={filters}
          onChange={setFilters}
          resultCount={filtered.length}
        />

        <div>
          <div className="mb-5 flex items-center gap-2">
            <Radar className="h-5 w-5 text-brand-400" />
            <h2 className="text-xl font-semibold">Latest tools</h2>
            <span className="ml-auto text-sm text-slate-500">{filtered.length} results</span>
          </div>

          {filtered.length === 0 ? (
            <div className="glass grid place-items-center rounded-2xl py-20 text-slate-500">
              No tools match these filters.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 2xl:grid-cols-3">
              <AnimatePresence mode="popLayout">
                {filtered.map((tool, i) => (
                  <motion.div key={tool.id} layout exit={{ opacity: 0, scale: 0.95 }}>
                    <ToolCard tool={tool} index={i} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </section>

      {/* ── Email capture (audience engine) ── */}
      <section className="mx-auto w-full max-w-[1920px] px-6 pb-16 lg:px-12">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="glass relative overflow-hidden rounded-3xl px-6 py-12 text-center sm:px-12"
        >
          <div className="pointer-events-none absolute -top-1/2 left-1/2 h-[40vmax] w-[40vmax] -translate-x-1/2 rounded-full bg-brand-500/15 blur-[100px]" />
          <div className="relative">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/5 px-3 py-1 text-xs text-slate-300">
              <span className="h-2 w-2 rounded-full bg-brand-500" /> Daily digest
            </span>
            <h2 className="mt-4 text-2xl font-bold sm:text-3xl">Never miss a launch</h2>
            <p className="mx-auto mt-2 max-w-md text-slate-400">
              The freshest AI tools, ranked and deduplicated, delivered to your inbox. One
              email a day — skip the noise.
            </p>
            <div className="mt-6">
              <SubscribeForm />
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer id="how" className="relative scroll-mt-20 border-t border-white/5">
        <div className="mx-auto grid w-full max-w-[1920px] gap-10 px-6 py-12 lg:grid-cols-3 lg:px-12">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-500 font-display text-sm font-bold text-white">
                A
              </span>
              <span className="font-display text-lg font-semibold tracking-tight">AIRadar</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-slate-500">
              Autonomous intelligence on newly launched AI tools — discovered, enriched and
              ranked. Refreshed daily.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-300">How it works</h3>
            <ol className="mt-3 space-y-1.5 text-sm text-slate-500">
              <li>1 — Discover candidate launches across the web</li>
              <li>2 — Enrich each with structured, evidence-backed data</li>
              <li>3 — Deduplicate and score by quality</li>
              <li>4 — Deliver a ranked daily digest</li>
            </ol>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-300">Sources</h3>
            <p className="mt-3 max-w-xs text-sm text-slate-500">
              Currently aggregating Hacker News, with Product Hunt, GitHub and more on the way.
              Every card links to the original source.
            </p>
          </div>
        </div>

        <div className="border-t border-white/5 py-5 text-center text-xs text-slate-600">
          © 2026 AIRadar · Beta · Data refreshed daily · Built with Next.js, Three.js &amp; Framer Motion
        </div>
      </footer>
    </main>
  );
}
