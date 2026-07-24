import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import api from "../services/api";

interface ScoreData {
  id: number;
  actor_id: number;
  role: string;
  period: string;
  computed_value: number;
  breakdown: Array<{
    event_id: number;
    event_type: string;
    delta: number;
    reason: string;
    created_at: string;
  }> | null;
}

export default function Scores() {
  const [actorId, setActorId] = useState<string>("");
  const [scores, setScores] = useState<ScoreData[]>([]);
  const [selectedScore, setSelectedScore] = useState<ScoreData | null>(null);

  const fetchScores = () => {
    if (actorId) {
      api.get(`/scores/${actorId}`).then((r) => setScores(r.data));
    }
  };

  const handleBarClick = (_data: unknown, index: number) => {
    if (scores[index]) {
      setSelectedScore(scores[index]);
    }
  };

  return (
    <div>
      <h2>Role Scores</h2>
      <p style={{ color: "#666" }}>
        Scores are per-role, absolute, and fully explainable. Every score shows
        the facts behind it.
      </p>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
        <input
          type="number"
          placeholder="Actor ID"
          value={actorId}
          onChange={(e) => setActorId(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc" }}
        />
        <button
          onClick={fetchScores}
          style={{
            padding: "0.5rem 1rem",
            background: "#3498db",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Load Scores
        </button>
      </div>

      {scores.length > 0 && (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={scores}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Bar
                dataKey="computed_value"
                fill="#2ecc71"
                onClick={handleBarClick}
                style={{ cursor: "pointer" }}
              />
            </BarChart>
          </ResponsiveContainer>

          {/* Score breakdown - explainability (NFR-4) */}
          {selectedScore && selectedScore.breakdown && (
            <div style={{ marginTop: "2rem" }}>
              <h3>
                Score Breakdown: {selectedScore.role} — {selectedScore.period}
              </h3>
              <p>
                Total: <strong>{selectedScore.computed_value}</strong>
              </p>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
                    <th style={{ padding: "0.5rem" }}>Event</th>
                    <th style={{ padding: "0.5rem" }}>Delta</th>
                    <th style={{ padding: "0.5rem" }}>Reason</th>
                    <th style={{ padding: "0.5rem" }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedScore.breakdown.map((event) => (
                    <tr
                      key={event.event_id}
                      style={{ borderBottom: "1px solid #eee" }}
                    >
                      <td style={{ padding: "0.5rem" }}>{event.event_type}</td>
                      <td
                        style={{
                          padding: "0.5rem",
                          color: event.delta >= 0 ? "#2ecc71" : "#e74c3c",
                          fontWeight: "bold",
                        }}
                      >
                        {event.delta >= 0 ? "+" : ""}
                        {event.delta}
                      </td>
                      <td style={{ padding: "0.5rem" }}>{event.reason}</td>
                      <td style={{ padding: "0.5rem" }}>
                        {new Date(event.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {scores.length === 0 && actorId && (
        <p style={{ color: "#999" }}>
          No scores found. Record quality events to generate scores.
        </p>
      )}
    </div>
  );
}
