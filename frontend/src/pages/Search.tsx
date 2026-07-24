import { useState } from "react";
import api from "../services/api";

interface SearchResultItem {
  entity_type: string;
  entity_id: number;
  title: string;
  snippet: string;
  relevance_score: number;
}

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (query.length < 2) return;
    setLoading(true);
    try {
      const r = await api.get("/search", { params: { q: query, limit: 20 } });
      setResults(r.data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
      setSearched(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  const entityIcon = (type: string) => {
    switch (type) {
      case "story":
        return "📋";
      case "bug":
        return "🐛";
      case "event":
        return "⚡";
      default:
        return "📄";
    }
  };

  return (
    <div>
      <h2>🔍 Semantic Search</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Search across stories, bugs, and quality events using natural language
        (FR-10).
      </p>

      {/* Search Bar */}
      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "2rem" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g., 'validation bugs in Auth module' or 'login issue'"
          style={{
            flex: 1,
            padding: "0.75rem 1rem",
            fontSize: "1rem",
            border: "2px solid #e5e7eb",
            borderRadius: "8px",
            outline: "none",
          }}
        />
        <button
          onClick={handleSearch}
          disabled={query.length < 2 || loading}
          style={{
            padding: "0.75rem 2rem",
            background: query.length >= 2 ? "#2563eb" : "#ccc",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: query.length >= 2 ? "pointer" : "not-allowed",
            fontSize: "1rem",
          }}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Results */}
      {searched && (
        <div>
          <p style={{ color: "#666", fontSize: "0.85rem", marginBottom: "1rem" }}>
            {results.length} result{results.length !== 1 ? "s" : ""} found
          </p>

          {results.map((result, idx) => (
            <div
              key={`${result.entity_type}-${result.entity_id}-${idx}`}
              style={{
                padding: "1rem 1.25rem",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
                marginBottom: "0.75rem",
                background: "#fff",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <span style={{ marginRight: "0.5rem" }}>
                    {entityIcon(result.entity_type)}
                  </span>
                  <strong style={{ fontSize: "0.95rem" }}>{result.title}</strong>
                </div>
                <span
                  style={{
                    fontSize: "0.75rem",
                    color: "#888",
                    background: "#f3f4f6",
                    padding: "0.2rem 0.5rem",
                    borderRadius: "4px",
                  }}
                >
                  {result.entity_type} · {(result.relevance_score * 100).toFixed(0)}%
                  match
                </span>
              </div>
              {result.snippet && (
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "#555",
                    marginTop: "0.5rem",
                    marginBottom: 0,
                  }}
                >
                  {result.snippet}
                </p>
              )}
            </div>
          ))}

          {results.length === 0 && (
            <div
              style={{
                padding: "2rem",
                textAlign: "center",
                color: "#999",
                border: "1px dashed #d1d5db",
                borderRadius: "8px",
              }}
            >
              No results found. Try different search terms.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
