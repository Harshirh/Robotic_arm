import { ClipboardList, History } from "lucide-react";

const columns = ["TIMESTAMP", "DETECTION RESULT", "CLASSIFICATION", "SORTING STATUS"];

export function ActivityPanel() {
  return <section className="panel activity-panel" id="activity-history"><div className="panel-heading"><div><div className="panel-eyebrow">04 / EVENT STREAM</div><h2>Activity history</h2></div><span className="activity-log-state"><History size={14} />NO EVENTS</span></div><div className="activity-table-wrap"><table className="activity-table"><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody><tr><td colSpan={columns.length}><div className="activity-empty"><div className="activity-empty-mark"><ClipboardList size={19} /></div><strong>No activity recorded</strong><span>Detection and sorting events will appear here when received from the backend.</span></div></td></tr></tbody></table></div><div className="activity-foot"><span><i /> LOG SOURCE</span><strong>BACKEND EVENT STREAM · NOT CONNECTED</strong></div></section>;
}
