"use client";

import { motion } from "framer-motion";
import { ArrowUpRight, Github } from "lucide-react";
import { Tilt3D } from "@/components/Tilt3D";
import type { Tool } from "@/lib/types";
import { cn, countryFlag, PRICING_LABELS, PRICING_STYLES, scoreColor } from "@/lib/utils";

export function ToolCard({
  tool,
  index,
  featured = false,
}: {
  tool: Tool;
  index: number;
  featured?: boolean;
}) {
  const ring = scoreColor(tool.quality);

  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: Math.min(index * 0.05, 0.4) }}
    >
      <Tilt3D className="h-full">
        <a
          href={tool.url}
          target="_blank"
          rel="noreferrer"
          style={{ transformStyle: "preserve-3d" }}
          className={cn(
            "glass glass-hover relative block h-full rounded-2xl p-5",
            featured && "border-brand-400/40 ring-1 ring-brand-500/30"
          )}
        >
          {featured && (
            <span
              className="relative mb-2 inline-flex items-center gap-1 rounded-full border border-brand-400/40 bg-brand-500/15 px-2 py-0.5 text-[11px] font-medium text-brand-200"
              style={{ transform: "translateZ(44px)" }}
            >
              ✦ Featured
            </span>
          )}
          <div
            className="relative flex items-start justify-between gap-3"
            style={{ transform: "translateZ(40px)" }}
          >
            <h3 className="font-semibold leading-snug text-slate-100 group-hover:text-white">
              {tool.name}
            </h3>
            <ScoreRing score={tool.quality} color={ring} />
          </div>

          {tool.oneLiner && (
            <p
              className="relative mt-2 line-clamp-2 text-sm text-slate-400"
              style={{ transform: "translateZ(28px)" }}
            >
              {tool.oneLiner}
            </p>
          )}

          <div
            className="relative mt-3 flex flex-wrap gap-1.5"
            style={{ transform: "translateZ(22px)" }}
          >
            {tool.categories.slice(0, 4).map((c) => (
              <span
                key={c}
                className="rounded-full border border-brand-400/30 bg-brand-400/10 px-2 py-0.5 text-xs text-brand-200"
              >
                {c}
              </span>
            ))}
          </div>

          <div
            className="relative mt-4 flex items-center justify-between"
            style={{ transform: "translateZ(16px)" }}
          >
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-xs font-medium",
                  PRICING_STYLES[tool.pricing]
                )}
              >
                {PRICING_LABELS[tool.pricing]}
              </span>
              <span className="text-sm" title={tool.country ?? "Unknown"}>
                {countryFlag(tool.country)}
              </span>
              {tool.githubUrl && <Github className="h-3.5 w-3.5 text-slate-500" />}
            </div>
            <ArrowUpRight className="h-4 w-4 text-slate-500 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand-400" />
          </div>
        </a>
      </Tilt3D>
    </motion.div>
  );
}

function ScoreRing({ score, color }: { score: number; color: string }) {
  const r = 14;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  return (
    <div className="relative shrink-0" title={`Quality score ${score}`}>
      <svg width="38" height="38" className="-rotate-90">
        <circle cx="19" cy="19" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="3" fill="none" />
        <circle
          cx="19"
          cy="19"
          r={r}
          stroke={color}
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
        />
      </svg>
      <span className="absolute inset-0 grid place-items-center font-mono text-xs text-slate-200">
        {score}
      </span>
    </div>
  );
}
