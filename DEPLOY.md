# Deploying AIRadar (free)

The dashboard ships as a **statically-generated Next.js site on Vercel**, reading a JSON
snapshot committed to the repo. There is no always-on backend to host or pay for — a
GitHub Action regenerates the snapshot daily and the commit triggers a Vercel redeploy.

**Total cost: $0** (Vercel Hobby + GitHub Actions free minutes).

```
GitHub repo ──(push / nightly Action commit)──▶ Vercel build ──▶ CDN (live site)
     ▲                                                                    
     └── .github/workflows/refresh-data.yml  (runs the pipeline, commits tools.json)
```

---

## One-time setup

### 1. Push the repo to GitHub
```bash
git add -A
git commit -m "AIRadar: pipeline, delivery, scheduler, and Next.js dashboard"
gh repo create airadar --private --source=. --push   # or create the repo in the UI and:
# git remote add origin https://github.com/<you>/airadar.git && git push -u origin master
```

### 2. Import the project into Vercel
1. Go to <https://vercel.com/new> and import the GitHub repo.
2. **Root Directory:** set to `frontend` ← important (the repo root is the Python app).
3. Framework preset: **Next.js** (auto-detected). Build/output settings: leave defaults.
4. **Environment variable:**
   - `NEXT_PUBLIC_SITE_URL` = your production URL (e.g. `https://airadar.vercel.app`)
   - (used for canonical/OpenGraph URLs; you can set it after the first deploy once you
     know the URL, then redeploy.)
5. Click **Deploy**.

That's it — the site is live at `https://<project>.vercel.app`.

---

## Keeping data fresh (already wired)

`.github/workflows/refresh-data.yml` runs **daily at 06:00 UTC**:
1. builds a fresh SQLite DB, runs the pipeline (discovery → scrape → enrich → curate),
2. exports `frontend/public/data/tools.json` through the hard quality filter,
3. commits it **only if it changed** → Vercel auto-redeploys.

Trigger it manually anytime from the repo's **Actions → Refresh tool data → Run workflow**.

> The pipeline runs in **offline mode** (no API keys) in CI, so it's free. To get
> higher-quality enrichment, add `AIRADAR_ANTHROPIC_API_KEY` as a GitHub Actions secret and
> the enrichment step upgrades automatically.

---

## Updating data manually (local)
```bash
uv run airadar pipeline-once --source hackernews --lookback-hours 96 --limit 50
uv run python scripts/export_tools_json.py
git add frontend/public/data/tools.json && git commit -m "chore(data): refresh" && git push
```

## Pre-publish checklist (Senior-PM gate)
- [ ] Eyeball `frontend/public/data/tools.json` — every entry is a real product, clean name + one-liner
- [ ] `cd frontend && npm run build` passes locally
- [ ] `NEXT_PUBLIC_SITE_URL` set in Vercel
- [ ] Shared-link preview renders (test the deployed `/opengraph-image`)
