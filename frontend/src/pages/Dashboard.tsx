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
} from "recharts";
import api from "../services/api";

interface Summary {
  total_stories: number;
  total_bugs: number;
  zero_bug_stories: number;
  zero_bug_percentage: number;
  production_defects: number;
  severity_breakdown: Record<string, number>;
}

interface ModuleData {
  module: string;
  bug_count: number;
}

interface BugTypeData {
  category: string;
  count: number;
  percentage: number;
}

const COLORS = [
  "#e74c3c",
  "#f39c12",
  "#3498db",
  "#2ecc71",
  "#9b59b6",
  "#1abc9c",
  "#e67e22",
  "#34495e",
];

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [heatmap, setHeatmap] = useState<ModuleData[]>([]);
  const [bugTypes, setBugTypes] = useState<BugTypeData[]>([]);
  const [selectedModule, setSelectedModule] = useState<string | null>(null);

  useEffect(() => {
    api.get("/dashboard/summary").then((r) => setSummary(r.data));
    api.get("/dashboard/module-heatmap").then((r) => setHeatmap(r.data));
  }, []);

  useEffect(() => {
    if (selectedModule) {
      api
        .get("/dashboard/bug-type-breakdown", {
          params: { module: selectedModule },
        })
        .then((r) => setBugTypes(r.data));
    }
  }, [selectedModule]);

  const handleBarClick = (_data: unknown, index: number) => {
    if (heatmap[index]) {
      setSelectedModule(heatmap[index].module);
    }
  };

  return (
    <div>
      <h2>Quality Dashboard</h2>

      {/* Summary Cards */}
      {summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <Card title="Total Stories" value={summary.total_stories} />
          <Card title="Total Bugs" value={summary.total_bugs} />
          <Card title="Zero-Bug Stories" value={summary.zero_bug_stories} />
          <Card
            title="Zero-Bug %"
            value={`${summary.zero_bug_percentage}%`}
          />
          <Card title="Production Defects" value={summary.production_defects} />
        </div>
      )}

      {/* Module Heatmap */}
      <h3>Module Defect Density</h3>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Click a module to drill down into bug types
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={heatmap}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="module" />
          <YAxis />
          <Tooltip />
          <Bar
            dataKey="bug_count"
            fill="#e74c3c"
            onClick={handleBarClick}
            style={{ cursor: "pointer" }}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Drill-down: Bug Type Breakdown */}
      {selectedModule && bugTypes.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3>
            Bug Types in {selectedModule}{" "}
            <button onClick={() => setSelectedModule(null)}>✕ Clear</button>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={bugTypes}
                dataKey="count"
                nameKey="category"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, payload }) =>
                  `${name} (${payload.percentage}%)`
                }
              >
                {bugTypes.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function Card({ title, value }: { title: string; value: string | number }) {
  return (
    <div
      style={{
        padding: "1.5rem",
        background: "#f8f9fa",
        borderRadius: "8px",
        border: "1px solid #e9ecef",
      }}
    >
      <div style={{ fontSize: "0.85rem", color: "#666" }}>{title}</div>
      <div style={{ fontSize: "2rem", fontWeight: "bold", marginTop: "0.5rem" }}>
        {value}
      </div>
    </div>
  );
}
