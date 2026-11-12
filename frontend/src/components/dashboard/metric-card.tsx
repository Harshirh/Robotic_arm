import type { LucideIcon } from "lucide-react";

type MetricCardProps = { label: string; value: string; note: string; icon: LucideIcon; tone: "cyan" | "blue" | "green" | "neutral" };

export function MetricCard({ label, value, note, icon: Icon, tone }: MetricCardProps) {
  return <article className="metric-card"><div className="metric-top"><span className="metric-label">{label}</span><span className={`metric-icon metric-icon-${tone}`}><Icon size={17} strokeWidth={1.8} /></span></div><div className={`metric-value metric-value-${tone}`}>{value}</div><p className="metric-note">{note}</p></article>;
}
