import { Dashboard } from "@/components/Dashboard";
import { getFeatured, getTools } from "@/lib/data";

export default function Home() {
  const { tools } = getTools();
  const featured = getFeatured();
  return <Dashboard tools={tools} featured={featured} />;
}
