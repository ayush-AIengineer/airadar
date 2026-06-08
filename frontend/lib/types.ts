export type Pricing =
  | "free"
  | "open_source"
  | "freemium"
  | "free_trial"
  | "paid"
  | "enterprise_only"
  | "unknown";

export interface Tool {
  id: string;
  name: string;
  url: string;
  oneLiner: string | null;
  description: string;
  pricing: Pricing;
  country: string | null;
  quality: number;
  isOpenSource: boolean;
  githubUrl: string | null;
  categories: string[];
}

export interface ToolsPayload {
  generatedAt: string;
  count: number;
  tools: Tool[];
}
