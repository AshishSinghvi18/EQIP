import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import api from "../services/api";

interface TrendPoint {
  period: string;
  bugs: number;
  positive_events: number;
  negative_events: number;
}

interface ModuleRisk {
  module: string;
  risk_score: number;
  risk_level: string;
  total_stories: number;
  total_bugs: number;
  bug_density: number;
  critical_high_bugs: number;
  production_bugs: number;
  unresolved_bugs: number;
  trend_direction: number;
  trend_label: string;
}

interface BadgeAward {
  badge_name: string;
  badge_id: number;
  evidence: Record<string, unknown>;
}

const RISK_COLORS: Record<string, string> = {
  critical: "#dc2626",
  high: "#f59e0b",
  medium: "#3b82f6",
  low: "#16a34a",
};

export default function Trends() {
  const [projectId, setProjectId] = useState(1);
  const [timeline, setTimeline] = useState<TrendPoint[]>([]);
  const [moduleRisks, setModuleRisks] = useState<ModuleRisk[]>([]);
  const [badgeUserId, setBadgeUserId] = useState(1);
  const [badgePeriod, setBadgePeriod] = useState("2026-07");
  const [badgeResult, setBadgeResult] = useState<BadgeAward[]>([]);

  useEffect(() => {
    api
      .get("/trends/quality-over-time", { params: { project_id: projectId, months: 6 } })
      .then((r) => setTimeline(r.data.timeline))
      .catch(() => setTimeline([]));
  }, [projectId]);

  useEffect(() => {
    api
      .get("/trends/module-risk", { params: { project_id: projectId } })
      .then((r) => setModuleRisks(r.data.modules))
      .catch(() => setModuleRisks([]));
  }, [projectId]);

  const evaluateBadges = () => {
    api
      .post(`/trends/badges/evaluate/${badgeUserId}?period=${badgePeriod}`)
      .then((r) => setBadgeResult(r.data.badges_awarded))
      .catch(() => setBadgeResult([]));
  };

  return (
    <div>
      <h2>📈 Trend Analytics & Module Risk</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Quality trends over time, module risk assessment, and automated badge evaluation (Phase 3).
      </p>

      {/* Project Selector */}
      <div style={{ marginBottom: "1.5rem", display: "flex", gap: "1rem", alignItems: "center" }}>
        <label style={{ fontWeight: 500 }}>Project ID:</label>
        <input
          type="number"
          value={projectId}
          onChange={(e) => setProjectId(Number(e.target.value))}
          style={{
            width: "80px",
            padding: "0.25rem 0.5rem",
            border: "1px solid #d1d5db",
            borderRadius: "4px",
          }}
          min={1}
        />
      </div>

      {/* Quality Trend Chart */}
      <div style={{ marginBottom: "3rem" }}>
        <h3>Quality Over Time</h3>
        {timeline.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="bugs"
                stroke="#dc2626"
                name="Bugs"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="positive_events"
                stroke="#16a34a"
                name="Positive Events"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="negative_events"
                stroke="#f59e0b"
                name="Negative Events"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p style={{ color: "#999" }}>No trend data available for this project.</p>
        )}
      </div>

      {/* Module Risk View */}
      <div style={{ marginBottom: "3rem" }}>
        <h3>Module Risk Assessment</h3>
        {moduleRisks.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={moduleRisks}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="module" />
                <YAxis domain={[0, 100]} label={{ value: "Risk Score", angle: -90, position: "insideLeft" }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload as ModuleRisk;
                      return (
                        <div
                          style={{
                            background: "#fff",
                            border: "1px solid #ddd",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            fontSize: "0.8rem",
                          }}
                        >
                          <strong>{data.module}</strong> — {data.risk_level.toUpperCase()}
                          <div>Risk Score: {data.risk_score}</div>
                          <div>Bugs: {data.total_bugs} ({data.bug_density}/story)</div>
                          <div>Critical/High: {data.critical_high_bugs}</div>
                          <div>Unresolved: {data.unresolved_bugs}</div>
                          <div>Trend: {data.trend_label} ({data.trend_direction > 0 ? "+" : ""}{data.trend_direction}%)</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="risk_score" name="Risk Score">
                  {moduleRisks.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={RISK_COLORS[entry.risk_level] || "#999"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Module Risk Table */}
            <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
              <thead>
                <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
                  <th style={{ padding: "0.6rem" }}>Module</th>
                  <th style={{ padding: "0.6rem" }}>Risk</th>
                  <th style={{ padding: "0.6rem" }}>Bugs</th>
                  <th style={{ padding: "0.6rem" }}>Density</th>
                  <th style={{ padding: "0.6rem" }}>Critical/High</th>
                  <th style={{ padding: "0.6rem" }}>Unresolved</th>
                  <th style={{ padding: "0.6rem" }}>Trend</th>
                </tr>
              </thead>
              <tbody>
                {moduleRisks.map((mod) => (
                  <tr key={mod.module} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "0.6rem", fontWeight: 500 }}>{mod.module}</td>
                    <td style={{ padding: "0.6rem" }}>
                      <span
                        style={{
                          padding: "0.2rem 0.6rem",
                          borderRadius: "12px",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          color: "#fff",
                          background: RISK_COLORS[mod.risk_level],
                        }}
                      >
                        {mod.risk_score} — {mod.risk_level}
                      </span>
                    </td>
                    <td style={{ padding: "0.6rem" }}>{mod.total_bugs}</td>
                    <td style={{ padding: "0.6rem" }}>{mod.bug_density}</td>
                    <td style={{ padding: "0.6rem" }}>{mod.critical_high_bugs}</td>
                    <td style={{ padding: "0.6rem" }}>{mod.unresolved_bugs}</td>
                    <td style={{ padding: "0.6rem" }}>
                      <span
                        style={{
                          color:
                            mod.trend_label === "improving"
                              ? "#16a34a"
                              : mod.trend_label === "worsening"
                              ? "#dc2626"
                              : "#666",
                        }}
                      >
                        {mod.trend_label === "improving" && "↓ "}
                        {mod.trend_label === "worsening" && "↑ "}
                        {mod.trend_label} ({mod.trend_direction > 0 ? "+" : ""}
                        {mod.trend_direction}%)
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p style={{ color: "#999" }}>No module risk data available.</p>
        )}
      </div>

      {/* Auto Badge Evaluation */}
      <div style={{ marginBottom: "3rem" }}>
        <h3>🎖 Auto Badge Evaluation</h3>
        <p style={{ color: "#666", fontSize: "0.85rem" }}>
          Automatically evaluate and award badges based on quality facts (FR-14).
        </p>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginBottom: "1rem" }}>
          <label>User ID:</label>
          <input
            type="number"
            value={badgeUserId}
            onChange={(e) => setBadgeUserId(Number(e.target.value))}
            style={{
              width: "80px",
              padding: "0.25rem 0.5rem",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
            }}
            min={1}
          />
          <label>Period:</label>
          <input
            type="text"
            value={badgePeriod}
            onChange={(e) => setBadgePeriod(e.target.value)}
            style={{
              width: "100px",
              padding: "0.25rem 0.5rem",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
            }}
            placeholder="2026-07"
          />
          <button
            onClick={evaluateBadges}
            style={{
              padding: "0.4rem 1rem",
              background: "#7c3aed",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            Evaluate Badges
          </button>
        </div>

        {badgeResult.length > 0 ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
            {badgeResult.map((badge, i) => (
              <div
                key={i}
                style={{
                  padding: "0.75rem 1rem",
                  background: "#fef3c7",
                  border: "1px solid #f59e0b",
                  borderRadius: "12px",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                  🏅 {badge.badge_name}
                </div>
                <div style={{ fontSize: "0.75rem", color: "#555", marginTop: "0.25rem" }}>
                  {Object.entries(badge.evidence)
                    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
                    .join(", ")}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: "#999", fontSize: "0.85rem" }}>
            Click "Evaluate Badges" to check if user qualifies for any badges this period.
          </p>
        )}
      </div>
    </div>
  );
}
