import { useEffect, useState } from "react";
import api from "../services/api";

interface Story {
  id: number;
  story_id: string;
  title: string;
  module: string | null;
  status: string;
  priority: string | null;
  story_points: number | null;
}

export default function Stories() {
  const [stories, setStories] = useState<Story[]>([]);

  useEffect(() => {
    api.get("/stories").then((r) => setStories(r.data));
  }, []);

  return (
    <div>
      <h2>Stories</h2>
      <table
        style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}
      >
        <thead>
          <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
            <th style={{ padding: "0.75rem" }}>ID</th>
            <th style={{ padding: "0.75rem" }}>Title</th>
            <th style={{ padding: "0.75rem" }}>Module</th>
            <th style={{ padding: "0.75rem" }}>Status</th>
            <th style={{ padding: "0.75rem" }}>Priority</th>
            <th style={{ padding: "0.75rem" }}>Points</th>
          </tr>
        </thead>
        <tbody>
          {stories.map((s) => (
            <tr key={s.id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ padding: "0.75rem" }}>{s.story_id}</td>
              <td style={{ padding: "0.75rem" }}>{s.title}</td>
              <td style={{ padding: "0.75rem" }}>{s.module || "—"}</td>
              <td style={{ padding: "0.75rem" }}>{s.status}</td>
              <td style={{ padding: "0.75rem" }}>{s.priority || "—"}</td>
              <td style={{ padding: "0.75rem" }}>{s.story_points ?? "—"}</td>
            </tr>
          ))}
          {stories.length === 0 && (
            <tr>
              <td
                colSpan={6}
                style={{ padding: "2rem", textAlign: "center", color: "#999" }}
              >
                No stories yet. Import stories via the API.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
