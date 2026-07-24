import { useEffect, useState } from "react";
import api from "../services/api";

interface LeaderboardEntry {
  rank: number;
  actor_id: number;
  score: number;
  breakdown: Array<{ event_type: string; delta: number; reason: string }>;
}

interface Badge {
  id: number;
  name: string;
  description: string | null;
  icon: string | null;
}

interface UserBadge {
  id: number;
  user_id: number;
  badge_id: number;
  period: string;
  evidence: Array<{ note: string }> | null;
  awarded_at: string;
}

export default function Leaderboard() {
  const [role, setRole] = useState("developer");
  const [period, setPeriod] = useState("2026-Q3");
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  const [userBadges, setUserBadges] = useState<UserBadge[]>([]);

  useEffect(() => {
    api
      .get("/dashboard/leaderboard", { params: { role, period, limit: 20 } })
      .then((r) => setEntries(r.data))
      .catch(() => setEntries([]));
  }, [role, period]);

  useEffect(() => {
    api
      .get("/badges")
      .then((r) => setBadges(r.data))
      .catch(() => setBadges([]));
  }, []);

  useEffect(() => {
    if (selectedUser) {
      api
        .get(`/badges/user/${selectedUser}`)
        .then((r) => setUserBadges(r.data))
        .catch(() => setUserBadges([]));
    }
  }, [selectedUser]);

  const roleOptions = [
    { value: "developer", label: "Developer" },
    { value: "business_analyst", label: "Business Analyst" },
    { value: "tester", label: "Tester" },
    { value: "automation_engineer", label: "Automation Engineer" },
  ];

  return (
    <div>
      <h2>🏆 Leaderboard & Recognition</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Rankings built on real facts. Every rank shows its evidence — no bare
        numbers (FR-14).
      </p>

      {/* Filters */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #d1d5db" }}
        >
          {roleOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          placeholder="Period (e.g., 2026-Q3)"
          style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #d1d5db" }}
        />
      </div>

      {/* Leaderboard Table */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "2rem" }}>
        <div>
          <h3>Top Performers</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
                <th style={{ padding: "0.75rem" }}>Rank</th>
                <th style={{ padding: "0.75rem" }}>User</th>
                <th style={{ padding: "0.75rem" }}>Score</th>
                <th style={{ padding: "0.75rem" }}>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.rank}
                  style={{
                    borderBottom: "1px solid #eee",
                    cursor: "pointer",
                    background:
                      selectedUser === entry.actor_id ? "#eff6ff" : undefined,
                  }}
                  onClick={() => setSelectedUser(entry.actor_id)}
                >
                  <td style={{ padding: "0.75rem" }}>
                    {entry.rank <= 3 ? ["🥇", "🥈", "🥉"][entry.rank - 1] : `#${entry.rank}`}
                  </td>
                  <td style={{ padding: "0.75rem" }}>User #{entry.actor_id}</td>
                  <td style={{ padding: "0.75rem", fontWeight: 600 }}>
                    {entry.score.toFixed(1)}
                  </td>
                  <td style={{ padding: "0.75rem", fontSize: "0.8rem", color: "#555" }}>
                    {entry.breakdown && entry.breakdown.length > 0
                      ? entry.breakdown
                          .slice(0, 3)
                          .map((b) => b.event_type)
                          .join(", ")
                      : "—"}
                  </td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    style={{ padding: "2rem", textAlign: "center", color: "#999" }}
                  >
                    No scores available for this period.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Badges Section */}
        <div>
          <h3>🎖 Badges</h3>
          {badges.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {badges.map((badge) => (
                <div
                  key={badge.id}
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: "#fef3c7",
                    border: "1px solid #f59e0b",
                    borderRadius: "20px",
                    fontSize: "0.8rem",
                  }}
                >
                  {badge.icon || "🏅"} {badge.name}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "#999", fontSize: "0.85rem" }}>
              No badges defined yet.
            </p>
          )}

          {/* User badges */}
          {selectedUser && (
            <div style={{ marginTop: "1.5rem" }}>
              <h4>Badges for User #{selectedUser}</h4>
              {userBadges.length > 0 ? (
                userBadges.map((ub) => (
                  <div
                    key={ub.id}
                    style={{
                      padding: "0.75rem",
                      background: "#f0fdf4",
                      border: "1px solid #86efac",
                      borderRadius: "8px",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <div style={{ fontWeight: 500, fontSize: "0.85rem" }}>
                      Badge #{ub.badge_id} · {ub.period}
                    </div>
                    {ub.evidence && (
                      <div style={{ fontSize: "0.75rem", color: "#555" }}>
                        {ub.evidence.map((e) => e.note).join(", ")}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p style={{ color: "#999", fontSize: "0.85rem" }}>
                  No badges awarded yet.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
