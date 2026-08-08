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
  acceptance_criteria: string | null;
  epic: string | null;
  onboarding_complete?: boolean;
  completeness_gaps?: string[] | null;
  quality_class?: string | null;
  description?: string | null;
  unit_test_cases?: string[] | null;
  ba_test_cases?: string[] | null;
}

interface Attachment {
  id: number;
  story_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  description: string | null;
  created_at: string;
}

export default function StoryOnboarding() {
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importMessage, setImportMessage] = useState("");

  useEffect(() => {
    api.get("/stories").then((r) => setStories(r.data));
  }, []);

  useEffect(() => {
    if (selectedStory) {
      api
        .get(`/attachments/stories/${selectedStory.id}/attachments`)
        .then((r) => setAttachments(r.data))
        .catch(() => setAttachments([]));
    }
  }, [selectedStory]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedStory) return;

    setUploading(true);
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post(
        `/attachments/stories/${selectedStory.id}/attachments`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setUploadMessage(`✓ "${file.name}" uploaded successfully`);
      // Refresh attachments
      const r = await api.get(
        `/attachments/stories/${selectedStory.id}/attachments`
      );
      setAttachments(r.data);
    } catch {
      setUploadMessage(`✗ Upload failed. Please try again.`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleImport = async () => {
    if (!importFile) return;
    setImportMessage("");
    const formData = new FormData();
    formData.append("file", importFile);

    try {
      const r = await api.post("/stories/import?project_id=1", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportMessage(
        `✓ Imported ${r.data.imported}/${r.data.total_rows} stories. ${r.data.errors.length} errors.`
      );
      // Refresh stories
      const storiesRes = await api.get("/stories");
      setStories(storiesRes.data);
    } catch {
      setImportMessage("✗ Import failed. Check file format.");
    }
    setImportFile(null);
  };

  const downloadAttachment = (attachment: Attachment) => {
    window.open(
      `${api.defaults.baseURL}/attachments/${attachment.id}/download`,
      "_blank"
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div>
      <h2>Story Onboarding</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Import stories and attach reference documents (Word, PDF, Excel) to
        provide full context for quality tracking.
      </p>

      {/* Import Section */}
      <div
        style={{
          background: "#f0f7ff",
          padding: "1.5rem",
          borderRadius: "8px",
          marginBottom: "2rem",
          border: "1px solid #b3d9ff",
        }}
      >
        <h3 style={{ margin: "0 0 1rem 0" }}>📥 Import Stories</h3>
        <p style={{ color: "#555", fontSize: "0.9rem", marginBottom: "1rem" }}>
          Upload an Excel (.xlsx), CSV, or JSON file to bulk-import stories.
        </p>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <input
            type="file"
            accept=".xlsx,.xls,.csv,.json"
            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
          />
          <button
            onClick={handleImport}
            disabled={!importFile}
            style={{
              padding: "0.5rem 1.5rem",
              background: importFile ? "#2563eb" : "#ccc",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: importFile ? "pointer" : "not-allowed",
            }}
          >
            Import
          </button>
        </div>
        {importMessage && (
          <p
            style={{
              marginTop: "0.75rem",
              color: importMessage.startsWith("✓") ? "#16a34a" : "#dc2626",
            }}
          >
            {importMessage}
          </p>
        )}
      </div>

      {/* Story List and Detail */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
        {/* Story List */}
        <div>
          <h3>Stories ({stories.length})</h3>
          <div
            style={{
              maxHeight: "600px",
              overflowY: "auto",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
            }}
          >
            {stories.map((story) => (
              <div
                key={story.id}
                onClick={() => setSelectedStory(story)}
                style={{
                  padding: "1rem",
                  borderBottom: "1px solid #f0f0f0",
                  cursor: "pointer",
                  background:
                    selectedStory?.id === story.id ? "#eff6ff" : "transparent",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                  {story.story_id}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#444" }}>
                  {story.title}
                </div>
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#888",
                    marginTop: "0.25rem",
                  }}
                >
                  {story.module || "No module"} · {story.status} ·{" "}
                  {story.story_points ?? "—"} pts
                  {story.onboarding_complete ? (
                    <span style={{ color: "#16a34a", marginLeft: "0.5rem" }}>✓ Onboarded</span>
                  ) : (
                    <span style={{ color: "#dc2626", marginLeft: "0.5rem" }}>⚠ Needs data</span>
                  )}
                </div>
              </div>
            ))}
            {stories.length === 0 && (
              <div style={{ padding: "2rem", textAlign: "center", color: "#999" }}>
                No stories yet. Import stories above.
              </div>
            )}
          </div>
        </div>

        {/* Story Detail + Attachments */}
        <div>
          {selectedStory ? (
            <>
              <h3>
                {selectedStory.story_id}: {selectedStory.title}
              </h3>
              <div
                style={{
                  background: "#f9fafb",
                  padding: "1rem",
                  borderRadius: "8px",
                  marginBottom: "1.5rem",
                }}
              >
                <div style={{ fontSize: "0.85rem", color: "#555" }}>
                  <strong>Epic:</strong> {selectedStory.epic || "—"}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#555" }}>
                  <strong>Module:</strong> {selectedStory.module || "—"}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#555" }}>
                  <strong>Priority:</strong> {selectedStory.priority || "—"}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#555" }}>
                  <strong>Status:</strong> {selectedStory.status}
                </div>
                {selectedStory.acceptance_criteria && (
                  <div style={{ marginTop: "0.75rem" }}>
                    <strong style={{ fontSize: "0.85rem" }}>
                      Acceptance Criteria:
                    </strong>
                    <p
                      style={{
                        fontSize: "0.85rem",
                        color: "#333",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {selectedStory.acceptance_criteria}
                    </p>
                  </div>
                )}
                {/* v1.1 Onboarding Data Gate Status */}
                <div style={{ marginTop: "1rem", padding: "0.75rem", background: selectedStory.onboarding_complete ? "#f0fdf4" : "#fef2f2", borderRadius: "6px", border: `1px solid ${selectedStory.onboarding_complete ? "#bbf7d0" : "#fecaca"}` }}>
                  <strong style={{ fontSize: "0.85rem" }}>
                    Onboarding Status: {selectedStory.onboarding_complete ? "✅ Complete" : "⚠️ Insufficient Data"}
                  </strong>
                  {selectedStory.completeness_gaps && selectedStory.completeness_gaps.length > 0 && (
                    <ul style={{ margin: "0.5rem 0 0", padding: "0 0 0 1.25rem", fontSize: "0.8rem", color: "#dc2626" }}>
                      {selectedStory.completeness_gaps.map((gap, i) => (
                        <li key={i}>{gap.replace(/_/g, " ")}</li>
                      ))}
                    </ul>
                  )}
                  <button
                    onClick={async () => {
                      try {
                        await api.post(`/story-quality/story/${selectedStory.id}/check-onboarding`);
                        const r = await api.get("/stories");
                        setStories(r.data);
                        const updated = r.data.find((s: Story) => s.id === selectedStory.id);
                        if (updated) setSelectedStory(updated);
                      } catch { /* ignore */ }
                    }}
                    style={{ marginTop: "0.5rem", padding: "0.3rem 0.75rem", fontSize: "0.8rem", background: "#3b82f6", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
                  >
                    🔄 Re-check Onboarding
                  </button>
                </div>
              </div>

              {/* Reference Documents */}
              <h4>📎 Reference Documents</h4>
              <p style={{ fontSize: "0.85rem", color: "#666", marginBottom: "1rem" }}>
                Attach Word, PDF, or Excel documents as reference material.
              </p>

              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "inline-block",
                    padding: "0.5rem 1rem",
                    background: "#2563eb",
                    color: "#fff",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  {uploading ? "Uploading..." : "📤 Upload Document"}
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.md"
                    onChange={handleFileUpload}
                    style={{ display: "none" }}
                    disabled={uploading}
                  />
                </label>
              </div>

              {uploadMessage && (
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: uploadMessage.startsWith("✓") ? "#16a34a" : "#dc2626",
                    marginBottom: "1rem",
                  }}
                >
                  {uploadMessage}
                </p>
              )}

              {/* Attachment List */}
              {attachments.length > 0 ? (
                <div
                  style={{
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    overflow: "hidden",
                  }}
                >
                  {attachments.map((att) => (
                    <div
                      key={att.id}
                      style={{
                        padding: "0.75rem 1rem",
                        borderBottom: "1px solid #f0f0f0",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <div style={{ fontSize: "0.85rem", fontWeight: 500 }}>
                          {att.filename}
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "#888" }}>
                          {att.file_type.toUpperCase()} ·{" "}
                          {formatFileSize(att.file_size)} ·{" "}
                          {new Date(att.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        onClick={() => downloadAttachment(att)}
                        style={{
                          padding: "0.25rem 0.75rem",
                          background: "#f3f4f6",
                          border: "1px solid #d1d5db",
                          borderRadius: "4px",
                          cursor: "pointer",
                          fontSize: "0.8rem",
                        }}
                      >
                        ⬇ Download
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div
                  style={{
                    padding: "1.5rem",
                    textAlign: "center",
                    color: "#999",
                    border: "1px dashed #d1d5db",
                    borderRadius: "8px",
                  }}
                >
                  No documents attached yet.
                </div>
              )}
            </>
          ) : (
            <div
              style={{
                padding: "3rem",
                textAlign: "center",
                color: "#999",
                border: "1px dashed #d1d5db",
                borderRadius: "8px",
              }}
            >
              Select a story to view details and attach reference documents.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
