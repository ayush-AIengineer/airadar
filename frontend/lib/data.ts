import payload from "@/public/data/tools.json";
import type { ToolsPayload } from "./types";

/**
 * Loads the exported tool catalog. Today this reads a static JSON snapshot produced by
 * `scripts/export_tools_json.py`; it will swap to `GET /api/v1/tools` once the FastAPI
 * backend (Architecture §10) is built — same shape, so callers don't change.
 */
export function getTools(): ToolsPayload {
  return payload as unknown as ToolsPayload;
}
