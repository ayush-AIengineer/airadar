import { Dashboard } from "@/components/Dashboard";
import { getTools } from "@/lib/data";

export default function Home() {
  const { tools } = getTools();
  return <Dashboard tools={tools} />;
}
