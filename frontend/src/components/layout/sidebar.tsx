import { Activity, Camera, ChartNoAxesCombined, History, Recycle, Settings2, SlidersHorizontal, Tags } from "lucide-react";

const navigation = [
  { label: "Dashboard", href: "#dashboard", icon: ChartNoAxesCombined, active: true },
  { label: "Live Monitoring", href: "#live-monitoring", icon: Camera },
  { label: "Bottle Detection", href: "#bottle-detection", icon: Tags },
  { label: "Robot Control", href: "#robot-control", icon: SlidersHorizontal },
  { label: "Activity History", href: "#activity-history", icon: History },
  { label: "Settings", href: "#settings", icon: Settings2 },
];

export function Sidebar() {
  return <aside className="sidebar"><div className="brand-lockup"><div className="brand-mark"><Recycle size={19} strokeWidth={2} /></div><div><p className="brand-name">RECYCLE<span>BOT</span></p><p className="brand-caption">ROBOTIC SORTING SYSTEM</p></div></div><div className="nav-section-label">WORKSPACE</div><nav aria-label="Main navigation" className="nav-list">{navigation.map(({ label, href, icon: Icon, active }) => <a key={label} className={`nav-item${active ? " nav-item-active" : ""}`} href={href} aria-current={active ? "page" : undefined}><Icon size={16} strokeWidth={1.8} /><span>{label}</span>{active && <span className="nav-active-dot" />}</a>)}</nav><div className="sidebar-bottom"><div className="project-card"><div className="project-icon"><Activity size={15} /></div><div className="project-copy"><span>ACTIVE PROJECT</span><strong>Recycling Robotic Arm</strong></div></div><div className="sidebar-foot"><span className="foot-dot" />DEVICE DATA UNAVAILABLE</div></div></aside>;
}
