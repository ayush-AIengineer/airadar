# AIRadar — MVP Implementation Plan (business-first)

> PM principle: **audience before paywall.** Every revenue path (sponsorships, Pro, API,
> intel) needs an engaged list first. So we build the audience engine now, monetize next,
> and deepen the moat last. Each phase ships something usable and is independently valuable.

## North-star wedge
Not "another AI directory" — a **monitoring + signal** product. Pick a niche later; the
machinery below is niche-agnostic.

---

## Phase 1 — Audience Engine  ⬅️ building now
**Goal:** turn visitors into a list you own.
- ✅ Email capture (free daily/weekly digest) — the delivery engine already exists
- Conversion-placed CTA (after users see value)
- Provider-pluggable storage (Buttondown / webhook) — zero backend to host, free
- **Success metric:** subscribers/week; visitor→subscriber conversion ≥ 3–5%

## Phase 2 — First Revenue
**Goal:** money in, fastest path first.
1. **Sponsored / Featured listings** — tool makers pay for a boosted slot (fastest $: just DM 10 makers). Add a "Featured" flag + a "Submit your tool" form.
2. **Pro tier ($19–29/mo)** via Stripe — custom alerts, category/country filters, no-noise feed.
- **Success metric:** first paying customer; MRR > $0; ≥ 1 sponsor.

## Phase 3 — Moat & Scale
**Goal:** defensibility + higher ACV.
- **Weekly trend report** (LLM synthesis) — the editorial moat; gate behind Pro/email.
- **Niche verticalization** — clone the radar for a specific industry/persona.
- **Data API** (DaaS) — sell the clean, deduped dataset.
- **Success metric:** retention cohort; B2B/API revenue.

---

## Sequencing rule
Ship Phase 1 → grow the list to a few hundred → *then* turn on Phase 2. Don't build the
paywall before there's an audience to sell to.
