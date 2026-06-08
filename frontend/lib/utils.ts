import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Pricing } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PRICING_LABELS: Record<Pricing, string> = {
  free: "Free",
  open_source: "Open source",
  freemium: "Freemium",
  free_trial: "Free trial",
  paid: "Paid",
  enterprise_only: "Enterprise",
  unknown: "Unknown",
};

// Two-color system: pricing badges stay neutral (white/slate) so blue reads as the accent.
const NEUTRAL_BADGE = "bg-white/5 text-slate-300 border-white/12";
export const PRICING_STYLES: Record<Pricing, string> = {
  free: NEUTRAL_BADGE,
  open_source: NEUTRAL_BADGE,
  freemium: NEUTRAL_BADGE,
  free_trial: NEUTRAL_BADGE,
  paid: NEUTRAL_BADGE,
  enterprise_only: NEUTRAL_BADGE,
  unknown: NEUTRAL_BADGE,
};

/** Quality score → ring color, in blues (high) down to slate (low). */
export function scoreColor(score: number): string {
  if (score >= 60) return "#3b82f6"; // blue-500
  if (score >= 30) return "#60a5fa"; // blue-400
  return "#475569"; // slate-600
}

/** ISO alpha-2 → flag emoji (best-effort; null → globe). */
export function countryFlag(code: string | null): string {
  if (!code || code.length !== 2) return "🌐";
  const base = 0x1f1e6;
  return String.fromCodePoint(
    base + (code.toUpperCase().charCodeAt(0) - 65),
    base + (code.toUpperCase().charCodeAt(1) - 65)
  );
}
