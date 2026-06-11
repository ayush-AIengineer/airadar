import featuredPayload from "@/public/data/featured.json";
import payload from "@/public/data/tools.json";
import type { Tool, ToolsPayload } from "./types";

/**
 * Loads the exported tool catalog. Today this reads a static JSON snapshot produced by
 * `scripts/export_tools_json.py`; it will swap to `GET /api/v1/tools` once the FastAPI
 * backend (Architecture §10) is built — same shape, so callers don't change.
 */
export function getTools(): ToolsPayload {
  return payload as unknown as ToolsPayload;
}

/**
 * Owner-curated sponsored/featured tools (paid placements). Lives in its own file so the
 * nightly auto-refresh (which only rewrites tools.json) never wipes paid slots. To add a
 * sponsor, append a Tool object to `public/data/featured.json` and commit.
 */
export function getFeatured(): Tool[] {
  return (featuredPayload as unknown as { featured: Tool[] }).featured ?? [];
}
