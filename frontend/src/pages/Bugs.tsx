import { useEffect, useState } from "react";
import api from "../services/api";

interface Bug {
  id: number;
  bug_id: string;
  summary: string;
  severity: string;
  status: string;
  root_cause_category: string | null;
  origin_stage: string | null;
}

export default function Bugs() {
  const [bugs, setBugs] = useState<Bug[]>([]);

  useEffect(() => {
    api.get("/bugs").then((r) => setBugs(r.data));
  }, []);

  return (
    <div>
      <h2>Bugs</h2>
      <table
        style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}
      >
        <thead>
          <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
            <th style={{ padding: "0.75rem" }}>ID</th>
            <th style={{ padding: "0.75rem" }}>Summary</th>
            <th style={{ padding: "0.75rem" }}>Severity</th>
            <th style={{ padding: "0.75rem" }}>Status</th>
            <th style={{ padding: "0.75rem" }}>Root Cause</th>
            <th style={{ padding: "0.75rem" }}>Origin</th>
          </tr>
        </thead>
        <tbody>
          {bugs.map((b) => (
            <tr key={b.id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ padding: "0.75rem" }}>{b.bug_id}</td>
              <td style={{ padding: "0.75rem" }}>{b.summary}</td>
              <td style={{ padding: "0.75rem" }}>
                <SeverityBadge severity={b.severity} />
              </td>
              <td style={{ padding: "0.75rem" }}>{b.status}</td>
              <td style={{ padding: "0.75rem" }}>
                {b.root_cause_category || "—"}
              </td>
              <td style={{ padding: "0.75rem" }}>{b.origin_stage || "—"}</td>
            </tr>
          ))}
          {bugs.length === 0 && (
            <tr>
              <td
                colSpan={6}
                style={{ padding: "2rem", textAlign: "center", color: "#999" }}
              >
                No bugs yet. Import bugs via the API.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "#e74c3c",
    high: "#e67e22",
    production: "#c0392b",
    security: "#8e44ad",
    data_loss: "#c0392b",
    medium: "#f39c12",
    general: "#3498db",
    cosmetic: "#95a5a6",
    informational: "#bdc3c7",
    performance: "#2980b9",
  };
  return (
    <span
      style={{
        padding: "0.25rem 0.5rem",
        borderRadius: "4px",
        background: colors[severity] || "#95a5a6",
        color: "#fff",
        fontSize: "0.8rem",
      }}
    >
      {severity}
    </span>
  );
}
