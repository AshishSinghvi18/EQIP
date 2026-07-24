import { useEffect, useState } from "react";
import api from "../services/api";

interface Recommendation {
  id: number;
  user_id: number;
  module: string | null;
  category: string;
  recommendation: string;
  supporting_data: Record<string, unknown> | null;
  is_dismissed: boolean;
  created_at: string;
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

interface Forecast {
  id: number;
  project_id: number;
  risk_score: number;
  confidence: number;
  factors: Array<{ factor: string; value: number; impact: number; description: string }>;
  recommendations: string[];
  created_at: string;
}

export default function Coaching() {
  const [userId, setUserId] = useState(1);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [projectId, setProjectId] = useState(1);
  const [healthIndex, setHealthIndex] = useState<HealthIndex | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);

  useEffect(() => {
    api
      .get(`/coaching/${userId}`)
      .then((r) => setRecommendations(r.data))
      .catch(() => setRecommendations([]));
  }, [userId]);

  const loadHealthIndex = () => {
    api
      .get(`/health/${projectId}`)
      .then((r) => setHealthIndex(r.data))
      .catch(() => setHealthIndex(null));
  };

  const generateForecast = () => {
    api
      .post(`/forecast?project_id=${projectId}`)
      .then((r) => setForecast(r.data))
      .catch(() => setForecast(null));
  };

  const generateCoaching = () => {
    api
      .post(`/coaching/${userId}/generate?period=current`)
      .then((r) => setRecommendations(r.data))
      .catch(() => {});
  };

  const dismissRecommendation = (id: number) => {
    api.post(`/coaching/${id}/dismiss`).then(() => {
      setRecommendations((prev) => prev.filter((r) => r.id !== id));
    });
  };

  const riskColor = (score: number) => {
    if (score >= 70) return "#dc2626";
    if (score >= 40) return "#f59e0b";
    return "#16a34a";
  };

  return (
    <div>
      <h2>💡 Coaching & Insights</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        AI-powered coaching recommendations, engineering health index, and
        release-risk predictions (FR-15, Phase 3-4).
      </p>

      {/* Coaching Section */}
      <div style={{ marginBottom: "3rem" }}>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          <h3 style={{ margin: 0 }}>📚 Coaching Recommendations</h3>
          <input
            type="number"
            value={userId}
            onChange={(e) => setUserId(Number(e.target.value))}
            style={{
              width: "80px",
              padding: "0.25rem 0.5rem",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
            }}
            min={1}
          />
          <button
            onClick={generateCoaching}
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
            Generate New
          </button>
        </div>

        {recommendations.length > 0 ? (
          recommendations.map((rec) => (
            <div
              key={rec.id}
              style={{
                padding: "1rem",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
                marginBottom: "0.75rem",
                background:
                  rec.category === "positive_trend" ? "#f0fdf4" : "#fffbeb",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                }}
              >
                <div>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      background: "#e5e7eb",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "4px",
                      textTransform: "uppercase",
                    }}
                  >
                    {rec.category}
                  </span>
                  {rec.module && (
                    <span
                      style={{
                        fontSize: "0.7rem",
                        background: "#dbeafe",
                        padding: "0.15rem 0.5rem",
                        borderRadius: "4px",
                        marginLeft: "0.5rem",
                      }}
                    >
                      {rec.module}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => dismissRecommendation(rec.id)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: "#999",
                  }}
                >
                  ✕
                </button>
              </div>
              <p style={{ fontSize: "0.9rem", marginTop: "0.5rem", marginBottom: 0 }}>
                {rec.recommendation}
              </p>
            </div>
          ))
        ) : (
          <p style={{ color: "#999" }}>
            No coaching recommendations. Click "Generate New" to analyze patterns.
          </p>
        )}
      </div>

      {/* Health Index & Forecast */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
        {/* Health Index */}
        <div>
          <div
            style={{
              display: "flex",
              gap: "1rem",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h3 style={{ margin: 0 }}>🏥 Engineering Health Index</h3>
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
            <button
              onClick={loadHealthIndex}
              style={{
                padding: "0.4rem 1rem",
                background: "#059669",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.85rem",
              }}
            >
              Load
            </button>
          </div>

          {healthIndex && (
            <div
              style={{
                padding: "1.5rem",
                background: "#f9fafb",
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
              }}
            >
              <div
                style={{
                  fontSize: "3rem",
                  fontWeight: "bold",
                  textAlign: "center",
                  color:
                    healthIndex.health_index >= 70
                      ? "#16a34a"
                      : healthIndex.health_index >= 40
                      ? "#f59e0b"
                      : "#dc2626",
                }}
              >
                {healthIndex.health_index}
              </div>
              <div
                style={{ textAlign: "center", color: "#666", marginBottom: "1rem" }}
              >
                Health Index (0-100)
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                <Metric
                  label="Zero-Bug Rate"
                  value={`${healthIndex.components.zero_bug_rate}%`}
                />
                <Metric
                  label="Positive Events"
                  value={`${healthIndex.components.positive_event_ratio}%`}
                />
                <Metric
                  label="Prod Stability"
                  value={`${healthIndex.components.production_stability}%`}
                />
                <Metric
                  label="Total Stories"
                  value={healthIndex.totals.stories.toString()}
                />
              </div>
            </div>
          )}
        </div>

        {/* Release Forecast */}
        <div>
          <div
            style={{
              display: "flex",
              gap: "1rem",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h3 style={{ margin: 0 }}>🔮 Release Risk Forecast</h3>
            <button
              onClick={generateForecast}
              style={{
                padding: "0.4rem 1rem",
                background: "#dc2626",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.85rem",
              }}
            >
              Generate
            </button>
          </div>

          {forecast && (
            <div
              style={{
                padding: "1.5rem",
                background: "#f9fafb",
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
              }}
            >
              <div
                style={{
                  fontSize: "2.5rem",
                  fontWeight: "bold",
                  textAlign: "center",
                  color: riskColor(forecast.risk_score),
                }}
              >
                {forecast.risk_score}
              </div>
              <div
                style={{ textAlign: "center", color: "#666", marginBottom: "1rem" }}
              >
                Risk Score (0-100) · Confidence: {(forecast.confidence * 100).toFixed(0)}%
              </div>

              {/* Risk Factors */}
              <h4 style={{ fontSize: "0.85rem", marginBottom: "0.5rem" }}>
                Risk Factors:
              </h4>
              {forecast.factors?.map((f, i) => (
                <div
                  key={i}
                  style={{
                    fontSize: "0.8rem",
                    padding: "0.3rem 0",
                    borderBottom: "1px solid #f0f0f0",
                  }}
                >
                  <strong>{f.factor}:</strong> {f.description} (impact: +
                  {f.impact})
                </div>
              ))}

              {/* Recommendations */}
              <h4
                style={{ fontSize: "0.85rem", marginTop: "1rem", marginBottom: "0.5rem" }}
              >
                Recommendations:
              </h4>
              {forecast.recommendations?.map((r, i) => (
                <div key={i} style={{ fontSize: "0.8rem", padding: "0.2rem 0" }}>
                  • {r}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        padding: "0.5rem",
        background: "#fff",
        borderRadius: "4px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "0.7rem", color: "#888" }}>{label}</div>
      <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{value}</div>
    </div>
  );
}
