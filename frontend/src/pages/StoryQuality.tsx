import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";
import api from "../services/api";

interface QualitySummary {
  total_onboarded: number;
  insufficient_data: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

interface ClassBreakdown {
  quality_class: string;
  count: number;
  percentage: number;
}

interface ReasoningBreakdown {
  reasoning_class: string;
  count: number;
  percentage: number;
}

interface StoryByClass {
  id: number;
  story_id: string;
  title: string;
  module: string;
  quality_class: string;
  story_rollup: number;
  escalation_count: number;
}

interface RoleScore {
  id: number;
  story_id: number;
  role: string;
  actor_id: number;
  score: number;
  breakdown: Array<{ deduction?: number; reasoning_class?: string; bug_id?: number; type?: string }>;
  computed_at: string;
}

interface ClassTrend {
  sprint_name: string;
  high_pct: number;
  medium_pct: number;
  low_pct: number;
  total: number;
}

const CLASS_COLORS: Record<string, string> = {
  high: "#2ecc71",
  medium: "#f39c12",
  low: "#e74c3c",
  insufficient_data: "#95a5a6",
};

const REASONING_COLORS = ["#e74c3c", "#f39c12", "#3498db", "#9b59b6", "#e67e22"];

const REASONING_LABELS: Record<string, string> = {
  silly_miss: "Silly Miss",
  critical_miss: "Critical Miss",
  info_not_in_story: "Info Not in Story",
  missing_unit_test: "Missing Unit Test",
  wrong_test_cases: "Wrong Test Cases",
};

function Card({ title, value, color }: { title: string; value: string | number; color?: string }) {
  return (
    <div
      style={{
        padding: "1.25rem",
        borderRadius: "12px",
        background: "var(--code-bg)",
        border: "1px solid var(--border)",
        textAlign: "left",
      }}
    >
      <div style={{ fontSize: "0.85rem", color: "var(--text)", marginBottom: "0.5rem" }}>{title}</div>
      <div style={{ fontSize: "1.75rem", fontWeight: 600, color: color || "var(--text-h)" }}>{value}</div>
    </div>
  );
}

export default function StoryQuality() {
  const [summary, setSummary] = useState<QualitySummary | null>(null);
  const [classBreakdown, setClassBreakdown] = useState<ClassBreakdown[]>([]);
  const [reasoningBreakdown, setReasoningBreakdown] = useState<ReasoningBreakdown[]>([]);
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [storiesByClass, setStoriesByClass] = useState<StoryByClass[]>([]);
  const [selectedStoryId, setSelectedStoryId] = useState<number | null>(null);
  const [roleScores, setRoleScores] = useState<RoleScore[]>([]);
  const [classTrend, setClassTrend] = useState<ClassTrend[]>([]);
  const [projectId, setProjectId] = useState<string>("");

  useEffect(() => {
    const params: Record<string, string> = {};
    if (projectId) params.project_id = projectId;

    api.get("/story-quality/summary", { params }).then((r) => setSummary(r.data));
    api.get("/story-quality/class-breakdown", { params }).then((r) => setClassBreakdown(r.data));
    api.get("/story-quality/reasoning-breakdown", { params }).then((r) => setReasoningBreakdown(r.data));
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      api.get("/story-quality/class-trend", { params: { project_id: projectId } }).then((r) => setClassTrend(r.data));
    }
  }, [projectId]);

  useEffect(() => {
    if (selectedClass) {
      const params: Record<string, string> = { quality_class: selectedClass };
      if (projectId) params.project_id = projectId;
      api.get("/story-quality/stories-by-class", { params }).then((r) => setStoriesByClass(r.data));
    }
  }, [selectedClass, projectId]);

  useEffect(() => {
    if (selectedStoryId) {
      api.get(`/story-quality/story/${selectedStoryId}/role-scores`).then((r) => setRoleScores(r.data));
    }
  }, [selectedStoryId]);

  return (
    <div style={{ textAlign: "left" }}>
      <h2>Story Quality Dashboard</h2>
      <p style={{ color: "var(--text)", marginBottom: "1.5rem" }}>
        Per-role story scores, quality classification, and bug-reasoning insights (v1.1)
      </p>

      {/* Project filter */}
      <div style={{ marginBottom: "1.5rem" }}>
        <label style={{ marginRight: "0.5rem" }}>Project ID:</label>
        <input
          type="number"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          placeholder="All projects"
          style={{
            padding: "0.4rem 0.75rem",
            borderRadius: "6px",
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--text-h)",
          }}
        />
      </div>

      {/* Summary Cards */}
      {summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <Card title="Total Onboarded" value={summary.total_onboarded} />
          <Card title="Insufficient Data" value={summary.insufficient_data} color="#95a5a6" />
          <Card title="High Quality" value={summary.high_count} color="#2ecc71" />
          <Card title="Medium Quality" value={summary.medium_count} color="#f39c12" />
          <Card title="Low Quality" value={summary.low_count} color="#e74c3c" />
        </div>
      )}

      {/* Two-column layout: Class Breakdown + Reasoning Breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>
        {/* Quality Class Breakdown (donut) */}
        <div>
          <h3>Quality Class Breakdown</h3>
          <p style={{ color: "var(--text)", fontSize: "0.85rem" }}>Click a class to drill down to stories</p>
          {classBreakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={classBreakdown}
                  dataKey="count"
                  nameKey="quality_class"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={100}
                  label={({ name, payload }) => `${name} (${payload.percentage}%)`}
                  onClick={(data) => setSelectedClass(data.quality_class)}
                  style={{ cursor: "pointer" }}
                >
                  {classBreakdown.map((entry, idx) => (
                    <Cell key={idx} fill={CLASS_COLORS[entry.quality_class] || "#bdc3c7"} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: "var(--text)" }}>No classified stories yet.</p>
          )}
        </div>

        {/* Bug-Reasoning Breakdown ("Where We Fall") */}
        <div>
          <h3>Where We Fall — Bug Reasoning</h3>
          <p style={{ color: "var(--text)", fontSize: "0.85rem" }}>Primary improvement signal (§7.4)</p>
          {reasoningBreakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={reasoningBreakdown} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" unit="%" />
                <YAxis
                  dataKey="reasoning_class"
                  type="category"
                  width={130}
                  tickFormatter={(v) => REASONING_LABELS[v] || v}
                />
                <Tooltip formatter={(value: number) => `${value}%`} />
                <Bar dataKey="percentage" fill="#3498db">
                  {reasoningBreakdown.map((_, idx) => (
                    <Cell key={idx} fill={REASONING_COLORS[idx % REASONING_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: "var(--text)" }}>No approved reasoning classifications yet.</p>
          )}
        </div>
      </div>

      {/* Class Trend (sprint over time) */}
      {classTrend.length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <h3>Quality Trend by Sprint</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={classTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="sprint_name" />
              <YAxis unit="%" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="high_pct" stroke="#2ecc71" name="High %" strokeWidth={2} />
              <Line type="monotone" dataKey="medium_pct" stroke="#f39c12" name="Medium %" strokeWidth={2} />
              <Line type="monotone" dataKey="low_pct" stroke="#e74c3c" name="Low %" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Drill-down: Stories by class */}
      {selectedClass && (
        <div style={{ marginBottom: "2rem" }}>
          <h3>
            Stories classified as{" "}
            <span style={{ color: CLASS_COLORS[selectedClass], textTransform: "uppercase" }}>{selectedClass}</span>
            <button
              onClick={() => {
                setSelectedClass(null);
                setStoriesByClass([]);
                setSelectedStoryId(null);
                setRoleScores([]);
              }}
              style={{ marginLeft: "1rem", fontSize: "0.85rem" }}
            >
              ✕ Clear
            </button>
          </h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid var(--border)" }}>
                <th style={thStyle}>Story ID</th>
                <th style={thStyle}>Title</th>
                <th style={thStyle}>Module</th>
                <th style={thStyle}>Rollup</th>
                <th style={thStyle}>Escalations</th>
                <th style={thStyle}>Action</th>
              </tr>
            </thead>
            <tbody>
              {storiesByClass.map((s) => (
                <tr key={s.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={tdStyle}>{s.story_id}</td>
                  <td style={tdStyle}>{s.title}</td>
                  <td style={tdStyle}>{s.module || "—"}</td>
                  <td style={tdStyle}>{s.story_rollup?.toFixed(1) ?? "—"}</td>
                  <td style={tdStyle}>{s.escalation_count}</td>
                  <td style={tdStyle}>
                    <button onClick={() => setSelectedStoryId(s.id)}>View Scores</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Per-role scores for selected story */}
      {selectedStoryId && roleScores.length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <h3>
            Per-Role Scores — Story #{selectedStoryId}
            <button onClick={() => { setSelectedStoryId(null); setRoleScores([]); }} style={{ marginLeft: "1rem", fontSize: "0.85rem" }}>
              ✕ Close
            </button>
          </h3>
          <p style={{ color: "var(--text)", fontSize: "0.85rem", marginBottom: "1rem" }}>
            Each role starts at 10.0 — deductions are independent (no shared pool)
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }}>
            {roleScores.map((rs) => (
              <div
                key={rs.id}
                style={{
                  padding: "1rem",
                  borderRadius: "10px",
                  border: "1px solid var(--border)",
                  background: "var(--code-bg)",
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: "0.5rem", textTransform: "capitalize" }}>
                  {rs.role.replace("_", " ")}
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 700, color: rs.score >= 8 ? "#2ecc71" : rs.score >= 5 ? "#f39c12" : "#e74c3c" }}>
                  {rs.score.toFixed(1)}
                  <span style={{ fontSize: "1rem", fontWeight: 400 }}>/10</span>
                </div>
                {rs.breakdown && rs.breakdown.length > 0 && (
                  <ul style={{ margin: "0.75rem 0 0", padding: "0 0 0 1.25rem", fontSize: "0.82rem" }}>
                    {rs.breakdown.map((d, i) => (
                      <li key={i} style={{ color: "var(--text)" }}>
                        {d.reasoning_class
                          ? `${REASONING_LABELS[d.reasoning_class] || d.reasoning_class}: ${d.deduction}`
                          : d.type === "escalation"
                          ? `Escalation: ${d.deduction}`
                          : `${d.deduction}`}
                      </li>
                    ))}
                  </ul>
                )}
                {(!rs.breakdown || rs.breakdown.length === 0) && (
                  <p style={{ color: "#2ecc71", fontSize: "0.82rem", margin: "0.5rem 0 0" }}>No faults — perfect score</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "0.6rem 0.75rem",
  fontSize: "0.85rem",
  fontWeight: 600,
};

const tdStyle: React.CSSProperties = {
  padding: "0.5rem 0.75rem",
  fontSize: "0.85rem",
};
