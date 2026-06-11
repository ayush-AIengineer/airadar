import type { Tool } from "./types";

export interface CountStat {
  key: string;
  count: number;
}

export interface Insights {
  total: number;
  avgQuality: number;
  openSourcePct: number;
  freePct: number;
  categories: CountStat[];
  pricing: CountStat[];
  topTools: Tool[];
}

/**
 * Derives the weekly "synthesis" view from the current tool snapshot — the editorial moat
 * (Architecture §1). Pure and deterministic; no LLM needed for the v1 data-driven report.
 */
export function computeInsights(tools: Tool[]): Insights {
  const total = tools.length;
  const avgQuality = total
    ? Math.round(tools.reduce((s, t) => s + t.quality, 0) / total)
    : 0;
  const oss = tools.filter((t) => t.isOpenSource).length;
  const free = tools.filter((t) => t.pricing === "free" || t.pricing === "open_source").length;

  const catCounts = new Map<string, number>();
  for (const t of tools) {
    for (const c of t.categories) catCounts.set(c, (catCounts.get(c) ?? 0) + 1);
  }
  const categories = [...catCounts.entries()]
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count);

  const priceCounts = new Map<string, number>();
  for (const t of tools) priceCounts.set(t.pricing, (priceCounts.get(t.pricing) ?? 0) + 1);
  const pricing = [...priceCounts.entries()]
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count);

  const topTools = [...tools].sort((a, b) => b.quality - a.quality).slice(0, 5);

  return {
    total,
    avgQuality,
    openSourcePct: total ? Math.round((oss / total) * 100) : 0,
    freePct: total ? Math.round((free / total) * 100) : 0,
    categories,
    pricing,
    topTools,
  };
}
