import type { Metadata } from "next";
import { TrendsView } from "@/components/TrendsView";
import { getTools } from "@/lib/data";
import { computeInsights } from "@/lib/insights";

export const metadata: Metadata = {
  title: "Trends",
  description: "What's launching in AI this week — categories, pricing, and the top tools.",
};

export default function TrendsPage() {
  const { tools } = getTools();
  return <TrendsView insights={computeInsights(tools)} />;
}
