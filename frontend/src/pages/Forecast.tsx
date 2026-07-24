import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import api from "../services/api";

interface RiskFactor {
  factor: string;
  value: number;
  impact: number;
  description: string;
}

interface Forecast {
  id: number;
  project_id: number;
  sprint_id: number | null;
  release: string | null;
  risk_score: number;
  confidence: number;
  factors: RiskFactor[];
  recommendations: string[];
  created_at: string;
}

interface TrendPeriod {
  period: string;
  sprint_id: number | null;
  stories: number;
  bugs: number;
  bug_density: number;
  completion_rate: number;
  positive_event_ratio: number;
}

interface TrendForecast {
  direction: string;
  bug_density_trend: string;
  completion_trend: string;
  predicted_bug_density: number;
  predicted_completion_rate: number;
  confidence: number;
}

interface QualityTrend {
  project_id: number;
  periods: TrendPeriod[];
  forecast: TrendForecast;
}

interface HealthIndex {
  health_index: number;
  components: {
    zero_bug_rate: number;
    positive_event_ratio: number;
    production_stability: number;
  };
  totals: {
    stories: number;
    bugs: number;
    production_defects: number;
    quality_events: number;
  };
}

interface ProjectBenchmark {
  project_id: number;
  project_name: string;
  health_index: number;
  zero_bug_rate: number;
  production_stability: number;
  bug_density: number;
  total_stories: number;
  total_bugs: number;
}

interface OrgBenchmark {
  org_health_index: number;
  org_bug_density: number;
  project_count: number;
  projects: ProjectBenchmark[];
}

const RISK_COLORS = {
  low: "#10b981",
  moderate: "#f59e0b",
  high: "#ef4444",
};

function getRiskLevel(score: number): "low" | "moderate" | "high" {
  if (score >= 70) return "high";
  if (score >= 40) return "moderate";
  return "low";
}

function getDirectionEmoji(direction: string): string {
  if (direction === "improving") return "📈";
  if (direction === "declining") return "📉";
  return "➡️";
}

export default function ForecastPage() {
  const [projectId, setProjectId] = useState(1);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [trend, setTrend] = useState<QualityTrend | null>(null);
  const [health, setHealth] = useState<HealthIndex | null>(null);
  const [benchmark, setBenchmark] = useState<OrgBenchmark | null>(null);
  const [loading, setLoading] = useState(false);

  const loadAll = () => {
    setLoading(true);
    Promise.all([
      api.get(`/prediction/health/${projectId}`).catch(() => null),
      api.get(`/prediction/trend/${projectId}`).catch(() => null),
      api.get(`/prediction/benchmarking`).catch(() => null),
    ]).then(([healthRes, trendRes, benchRes]) => {
      if (healthRes) setHealth(healthRes.data);
      if (trendRes) setTrend(trendRes.data);
      if (benchRes) setBenchmark(benchRes.data);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadAll();
  }, [projectId]);

  const generateForecast = () => {
    api
      .post(`/prediction/forecast?project_id=${projectId}`)
      .then((r) => setForecast(r.data))
      .catch(() => setForecast(null));
  };

  const riskLevel = forecast ? getRiskLevel(forecast.risk_score) : null;

  return (
    <div>
      <h2>📊 Release Risk & Quality Forecast</h2>
      <p style={{ color: "#666" }}>
        Phase 4: Prediction — Release-risk analysis, quality trends, and org
        benchmarking.
      </p>

      <div style={{ marginBottom: "1.5rem" }}>
        <label>
          Project ID:{" "}
          <input
            type="number"
            min={1}
            value={projectId}
            onChange={(e) => setProjectId(Number(e.target.value))}
            style={{ width: "60px", marginRight: "1rem" }}
          />
        </label>
        <button onClick={generateForecast}>🔮 Generate Risk Forecast</button>
      </div>

      {loading && <p>Loading...</p>}

      {/* Engineering Health Index */}
      {health && (
        <section
          style={{
            background: "#f8fafc",
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
          }}
        >
          <h3>🏥 Engineering Health Index</h3>
          <div
            style={{
              display: "flex",
              gap: "2rem",
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <div
              style={{
                fontSize: "3rem",
                fontWeight: "bold",
                color:
                  health.health_index >= 70
                    ? "#10b981"
                    : health.health_index >= 40
                      ? "#f59e0b"
                      : "#ef4444",
              }}
            >
              {health.health_index}
            </div>
            <div>
              <div>
                Zero-Bug Rate: <strong>{health.components.zero_bug_rate}%</strong>
              </div>
              <div>
                Positive Events:{" "}
                <strong>{health.components.positive_event_ratio}%</strong>
              </div>
              <div>
                Production Stability:{" "}
                <strong>{health.components.production_stability}%</strong>
              </div>
            </div>
            <div style={{ color: "#666", fontSize: "0.9rem" }}>
              <div>{health.totals.stories} stories</div>
              <div>{health.totals.bugs} bugs</div>
              <div>{health.totals.production_defects} production defects</div>
              <div>{health.totals.quality_events} quality events</div>
            </div>
          </div>
        </section>
      )}

      {/* Release Risk Forecast */}
      {forecast && (
        <section
          style={{
            background: "#fff",
            border: `2px solid ${RISK_COLORS[riskLevel!]}`,
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
          }}
        >
          <h3>🔮 Release Risk Prediction</h3>
          <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
            <div>
              <div
                style={{
                  fontSize: "2.5rem",
                  fontWeight: "bold",
                  color: RISK_COLORS[riskLevel!],
                }}
              >
                {forecast.risk_score}
                <span style={{ fontSize: "1rem", color: "#666" }}>/100</span>
              </div>
              <div
                style={{
                  textTransform: "uppercase",
                  fontWeight: 600,
                  color: RISK_COLORS[riskLevel!],
                }}
              >
                {riskLevel} risk
              </div>
              <div style={{ fontSize: "0.85rem", color: "#666" }}>
                Confidence: {Math.round(forecast.confidence * 100)}%
              </div>
            </div>

            <div style={{ flex: 1 }}>
              <h4 style={{ margin: "0 0 0.5rem" }}>Risk Factors</h4>
              {forecast.factors.map((f, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "0.3rem 0",
                    borderBottom: "1px solid #eee",
                  }}
                >
                  <span>{f.factor}</span>
                  <span style={{ color: "#666" }}>{f.description}</span>
                  <span
                    style={{
                      fontWeight: 600,
                      color: f.impact > 15 ? "#ef4444" : "#666",
                    }}
                  >
                    +{f.impact}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: "1rem" }}>
            <h4>Recommendations</h4>
            <ul>
              {forecast.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Quality Trend */}
      {trend && trend.periods.length > 0 && (
        <section
          style={{
            background: "#f8fafc",
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
          }}
        >
          <h3>
            📈 Quality Trend{" "}
            <span style={{ fontSize: "0.9rem", fontWeight: "normal" }}>
              {getDirectionEmoji(trend.forecast.direction)}{" "}
              {trend.forecast.direction}
            </span>
          </h3>

          <div style={{ height: 250 }}>
            <ResponsiveContainer>
              <LineChart data={trend.periods}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="bug_density"
                  stroke="#ef4444"
                  name="Bug Density"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="completion_rate"
                  stroke="#10b981"
                  name="Completion %"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="positive_event_ratio"
                  stroke="#6366f1"
                  name="Positive Events %"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div
            style={{
              display: "flex",
              gap: "2rem",
              marginTop: "1rem",
              fontSize: "0.9rem",
            }}
          >
            <div>
              Bug Density Trend:{" "}
              <strong>{trend.forecast.bug_density_trend}</strong> → predicted{" "}
              {trend.forecast.predicted_bug_density}
            </div>
            <div>
              Completion Trend:{" "}
              <strong>{trend.forecast.completion_trend}</strong> → predicted{" "}
              {trend.forecast.predicted_completion_rate}%
            </div>
            <div>
              Confidence: {Math.round(trend.forecast.confidence * 100)}%
            </div>
          </div>
        </section>
      )}

      {/* Org Benchmarking */}
      {benchmark && benchmark.projects.length > 0 && (
        <section
          style={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
          }}
        >
          <h3>🏢 Org Benchmarking</h3>
          <div style={{ marginBottom: "1rem", color: "#666" }}>
            Org Health Index:{" "}
            <strong style={{ fontSize: "1.2rem" }}>
              {benchmark.org_health_index}
            </strong>{" "}
            | Avg Bug Density: {benchmark.org_bug_density} |{" "}
            {benchmark.project_count} projects
          </div>

          <div style={{ height: 200 }}>
            <ResponsiveContainer>
              <BarChart data={benchmark.projects}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="project_name" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="health_index" name="Health Index">
                  {benchmark.projects.map((p, i) => (
                    <Cell
                      key={i}
                      fill={
                        p.health_index >= 70
                          ? "#10b981"
                          : p.health_index >= 40
                            ? "#f59e0b"
                            : "#ef4444"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <table
            style={{
              width: "100%",
              marginTop: "1rem",
              borderCollapse: "collapse",
              fontSize: "0.9rem",
            }}
          >
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0" }}>
                <th style={{ textAlign: "left", padding: "0.5rem" }}>Rank</th>
                <th style={{ textAlign: "left", padding: "0.5rem" }}>
                  Project
                </th>
                <th style={{ textAlign: "right", padding: "0.5rem" }}>
                  Health
                </th>
                <th style={{ textAlign: "right", padding: "0.5rem" }}>
                  Zero-Bug %
                </th>
                <th style={{ textAlign: "right", padding: "0.5rem" }}>
                  Bug Density
                </th>
                <th style={{ textAlign: "right", padding: "0.5rem" }}>
                  Stories
                </th>
              </tr>
            </thead>
            <tbody>
              {benchmark.projects.map((p, i) => (
                <tr
                  key={p.project_id}
                  style={{ borderBottom: "1px solid #f1f5f9" }}
                >
                  <td style={{ padding: "0.5rem" }}>#{i + 1}</td>
                  <td style={{ padding: "0.5rem" }}>{p.project_name}</td>
                  <td
                    style={{
                      textAlign: "right",
                      padding: "0.5rem",
                      fontWeight: 600,
                    }}
                  >
                    {p.health_index}
                  </td>
                  <td style={{ textAlign: "right", padding: "0.5rem" }}>
                    {p.zero_bug_rate}%
                  </td>
                  <td style={{ textAlign: "right", padding: "0.5rem" }}>
                    {p.bug_density}
                  </td>
                  <td style={{ textAlign: "right", padding: "0.5rem" }}>
                    {p.total_stories}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
