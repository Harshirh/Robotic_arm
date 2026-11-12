"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Clock3, Cpu, Wifi } from "lucide-react";
import { useRealtime } from "@/components/realtime/realtime-provider";

function formatDate(value: Date) {
  return new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "2-digit", year: "numeric" }).format(value);
}

function formatTime(value: Date) {
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(value);
}

export function Topbar() {
  const [now, setNow] = useState<Date | null>(null);
  const { backendConnected, esp32Connected } = useRealtime();
  useEffect(() => {
    const update = () => setNow(new Date());
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const esp32Label = esp32Connected === null ? "Unknown" : esp32Connected ? "Connected" : "Disconnected";
  return <header className="topbar"><div className="header-project"><span className="header-project-label">PROJECT</span><strong>Recycling Robotic Arm</strong></div><div className="topbar-right"><div className="header-clock"><span><CalendarDays size={14} />{now ? formatDate(now) : "Loading date"}</span><span><Clock3 size={14} />{now ? formatTime(now) : "--:--:--"}</span></div><div className="header-statuses"><span className={`status-chip ${backendConnected ? "status-connected" : "status-unavailable"}`}><Wifi size={14} /><span className="status-chip-copy"><small>BACKEND</small><strong>{backendConnected ? "Connected" : "Disconnected"}</strong></span><i /></span><span className={`status-chip ${esp32Connected ? "status-connected" : "status-unavailable"}`}><Cpu size={14} /><span className="status-chip-copy"><small>ESP32</small><strong>{esp32Label}</strong></span><i /></span></div></div></header>;
}
