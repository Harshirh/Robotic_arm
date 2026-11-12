"use client";

import { Activity, Bot, Camera, CircleDot, Cpu, Gauge, Server, Settings2 } from "lucide-react";
import { ArmStatusPanel } from "@/components/controls/arm-status-panel";
import { CameraPanel } from "@/components/camera/camera-panel";
import { ActivityPanel } from "@/components/dashboard/activity-panel";
import { ClassificationPanel } from "@/components/dashboard/classification-panel";
import { MetricCard } from "@/components/dashboard/metric-card";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useRealtime } from "@/components/realtime/realtime-provider";

export default function DashboardPage() {
  const { backendConnected, cameraActive, detection, esp32Connected } = useRealtime();
  const detectionLabel = detection?.detected === true ? "Bottle detected" : detection?.detected === false ? "No bottle" : detection?.state === "unavailable" ? "Unavailable" : "Waiting";
  return <div className="app-shell" id="dashboard"><Sidebar /><div className="main-column"><Topbar /><main className="dashboard-main"><section className="welcome-row"><div><div className="page-kicker"><span className="kicker-line" />OPERATIONS CONSOLE <span className="kicker-dot">/</span> OVERVIEW</div><h1>System dashboard<span className="title-period">.</span></h1><p className="welcome-copy">Live operations overview for your recycling automation workspace.</p></div><div className="overview-stamp"><span className="stamp-dot" />LIVE DEVICE STATUS <span>{detection?.detected ? "FILL STATE UNCERTAIN" : "FILL STATE UNASSESSED"}</span></div></section>
    <section className="metrics-grid" aria-label="System overview"><MetricCard label="ESP32" value={esp32Connected ? "Connected" : backendConnected ? "Disconnected" : "Unavailable"} note={esp32Connected ? "Serial device is connected" : "No ESP32 serial connection"} icon={Cpu} tone="blue" /><MetricCard label="CAMERA" value={cameraActive === null ? "Unavailable" : cameraActive ? "Active" : "Inactive"} note={cameraActive ? "Webcam stream is running" : "Start the webcam to begin"} icon={Camera} tone="cyan" /><MetricCard label="BOTTLE DETECTION" value={detectionLabel} note={detection?.message ?? "Waiting for backend telemetry"} icon={CircleDot} tone="green" /><MetricCard label="ROBOTIC ARM" value="Not implemented" note="Motion commands are disabled" icon={Bot} tone="neutral" /></section>
    <div className="section-title-row"><div><span className="section-index">01</span><h2>Live operations</h2></div><span className="section-context"><Activity size={14} /> WEBSOCKET TELEMETRY</span></div>
    <section className="operations-grid"><CameraPanel /><div className="operations-side"><ClassificationPanel /><ArmStatusPanel /></div></section>
    <ActivityPanel />
    <section className="settings-strip" id="settings"><div className="settings-icon"><Settings2 size={17} /></div><div><span>INTEGRATION SETTINGS</span><strong>Backend connection</strong><p>Configure NEXT_PUBLIC_API_URL and NEXT_PUBLIC_WS_URL in your local environment when the FastAPI service is ready.</p></div><div className="settings-end"><Server size={15} /><span>NOT CONFIGURED</span></div></section>
    <footer className="page-footer"><span>RECYCLING ROBOTIC ARM <i /> CONTROL INTERFACE</span><span><Gauge size={12} /> UI ONLY <b>V 0.2.0</b></span></footer>
  </main></div></div>;
}
