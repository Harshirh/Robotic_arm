"use client";

import { CircleHelp, Droplets, FlaskConical, Package, ScanSearch } from "lucide-react";
import { useRealtime } from "@/components/realtime/realtime-provider";

export function ClassificationPanel() {
  const { detection } = useRealtime();
  const detected = detection?.detected === true;
  const bottleState = detection?.state === "unavailable" ? "Unavailable" : detected ? "Detected" : detection?.detected === false ? "Not detected" : "Waiting";
  const signals = [
    { label: "Bottle detected", icon: Package, state: bottleState, tone: detected ? "value-detected" : "" },
    { label: "Empty", icon: FlaskConical, state: "Not assessed", tone: "" },
    { label: "Not empty", icon: Droplets, state: "Not assessed", tone: "" },
    { label: "Uncertain", icon: CircleHelp, state: detected ? "Fill state" : "—", tone: detected ? "value-waiting" : "" },
  ];
  const confidence = detection?.confidence;
  const statusLabel = detection?.state === "unavailable" ? "DETECTOR UNAVAILABLE" : detected ? "BOTTLE DETECTED" : detection?.detected === false ? "NO BOTTLE DETECTED" : "AWAITING INPUT";

  return <section className="panel classification-panel" id="bottle-detection"><div className="panel-heading"><div><div className="panel-eyebrow">02 / MACHINE VISION</div><h2>Bottle detection &amp; classification</h2></div><span className={`panel-state ${detected ? "state-online" : "state-pending"}`}><i />{statusLabel}</span></div><div className="classification-summary"><div className="classification-symbol"><ScanSearch size={20} /></div><div><span>LIVE DETECTION</span><strong>{detection?.message ?? "Waiting for camera frames"}</strong></div><div className="confidence-ring"><span>{confidence == null ? "—" : `${Math.round(confidence * 100)}%`}</span><small>BOX SCORE</small></div></div><div className="classification-list">{signals.map(({ label, icon: Icon, state, tone }) => <div className="classification-row" key={label}><span className="classification-name"><Icon size={15} />{label}</span><span className={`classification-value ${tone}`}>{state}</span></div>)}</div><div className="classification-footer"><span className="data-placeholder-dot" />PRESENCE AND FILL-STATE ARE SEPARATE <span>Transparency is not used to infer empty</span></div></section>;
}
