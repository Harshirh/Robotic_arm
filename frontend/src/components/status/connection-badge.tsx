import { Circle } from "lucide-react";
import type { ConnectionState } from "@/types";

const labels: Record<ConnectionState, string> = { connected: "Connected", connecting: "Connecting", disconnected: "Not connected" };

export function ConnectionBadge({ state = "disconnected" }: { state?: ConnectionState }) {
  return <span className={`connection-badge connection-${state}`}><Circle size={7} fill="currentColor" strokeWidth={0} />{labels[state]}</span>;
}
