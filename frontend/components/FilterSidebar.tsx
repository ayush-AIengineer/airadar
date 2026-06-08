"use client";

import { motion } from "framer-motion";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { cn, PRICING_LABELS } from "@/lib/utils";
import type { Pricing } from "@/lib/types";

export interface FilterState {
  query: string;
  categories: Set<string>;
  pricings: Set<Pricing>;
  minQuality: number;
}

interface FilterSidebarProps {
  categoryCounts: [string, number][];
  pricingOptions: Pricing[];
  state: FilterState;
  onChange: (next: FilterState) => void;
  resultCount: number;
}

export function FilterSidebar({
  categoryCounts,
  pricingOptions,
  state,
  onChange,
  resultCount,
}: FilterSidebarProps) {
  const toggle = <T,>(set: Set<T>, value: T): Set<T> => {
    const next = new Set(set);
    next.has(value) ? next.delete(value) : next.add(value);
    return next;
  };

  const active =
    state.query !== "" ||
    state.categories.size > 0 ||
    state.pricings.size > 0 ||
    state.minQuality > 0;

  return (
    <motion.aside
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-4 lg:sticky lg:top-6 lg:self-start"
    >
      {/* Search */}
      <div className="glass rounded-2xl p-1.5">
        <div className="flex items-center gap-2 px-3 py-2">
          <Search className="h-4 w-4 shrink-0 text-slate-500" />
          <input
            value={state.query}
            onChange={(e) => onChange({ ...state, query: e.target.value })}
            placeholder="Search tools…"
            className="w-full bg-transparent text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none"
          />
          {state.query && (
            <button onClick={() => onChange({ ...state, query: "" })} aria-label="Clear search">
              <X className="h-4 w-4 text-slate-500 hover:text-slate-300" />
            </button>
          )}
        </div>
      </div>

      <div className="glass rounded-2xl p-4">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <SlidersHorizontal className="h-4 w-4" /> Filters
          </div>
          {active && (
            <button
              onClick={() =>
                onChange({ query: "", categories: new Set(), pricings: new Set(), minQuality: 0 })
              }
              className="text-xs text-brand-400 hover:underline"
            >
              Reset
            </button>
          )}
        </div>

        {/* Category */}
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Category
        </h4>
        <div className="mb-5 flex flex-wrap gap-1.5">
          {categoryCounts.map(([cat, count]) => {
            const on = state.categories.has(cat);
            return (
              <button
                key={cat}
                onClick={() => onChange({ ...state, categories: toggle(state.categories, cat) })}
                className={cn(
                  "rounded-full border px-2.5 py-1 text-xs transition",
                  on
                    ? "border-brand-500 bg-brand-500/20 font-medium text-brand-200"
                    : "border-white/10 text-slate-400 hover:text-slate-200"
                )}
              >
                {cat} <span className="opacity-50">{count}</span>
              </button>
            );
          })}
        </div>

        {/* Pricing */}
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Pricing
        </h4>
        <div className="mb-5 space-y-1.5">
          {pricingOptions.map((p) => (
            <label
              key={p}
              className="flex cursor-pointer items-center gap-2 text-sm text-slate-400 hover:text-slate-200"
            >
              <input
                type="checkbox"
                checked={state.pricings.has(p)}
                onChange={() => onChange({ ...state, pricings: toggle(state.pricings, p) })}
                className="h-3.5 w-3.5 rounded border-white/20 bg-transparent accent-brand-500"
              />
              {PRICING_LABELS[p]}
            </label>
          ))}
        </div>

        {/* Min quality */}
        <h4 className="mb-2 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
          <span>Min quality</span>
          <span className="font-mono text-brand-400">{state.minQuality}</span>
        </h4>
        <input
          type="range"
          min={0}
          max={100}
          value={state.minQuality}
          onChange={(e) => onChange({ ...state, minQuality: Number(e.target.value) })}
          className="w-full accent-brand-500"
        />
      </div>

      <div className="px-1 text-center text-xs text-slate-500">
        {resultCount} {resultCount === 1 ? "tool" : "tools"} match
      </div>
    </motion.aside>
  );
}
