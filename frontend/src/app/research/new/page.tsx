"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { startResearch } from "@/lib/api";

export default function NewResearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Focus the textarea on mount
    const ta = document.querySelector("textarea");
    if (ta) ta.focus();
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await startResearch({ query: query.trim() });
      router.push(`/research/${data.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start research. Is the backend running?");
      setLoading(false);
    }
  };

  return (
    <div className="welcome">
      <div className="welcome-logo">A</div>
      <div className="welcome-title">Start New Research</div>
      <div className="welcome-sub">
        Enter a query to start a new multi-agent research session.
      </div>

      {error && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: "var(--radius-md)", padding: "12px 16px", marginBottom: "20px",
          maxWidth: "540px", width: "100%", fontSize: "13px", color: "var(--red)"
        }}>
          {error}
        </div>
      )}

      <div style={{ width: "100%", maxWidth: "540px" }}>
        <div className="input-box">
          <textarea
            placeholder="What would you like to research today?"
            rows={2}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                handleSubmit();
              }
            }}
            disabled={loading}
            autoFocus
          />
          <div className="input-actions">
            <button
              className="send-btn"
              disabled={loading || !query.trim()}
              onClick={() => handleSubmit()}
              style={{ width: "auto", padding: "0 16px", borderRadius: "9px", gap: "6px" }}
            >
              {loading ? "Starting..." : "Run Research"}
            </button>
          </div>
        </div>
        <div className="input-footer">
          <span className="input-hint">Press</span>
          <span className="shortcut">Ctrl</span>
          <span className="shortcut">Enter</span>
          <span className="input-hint">to send</span>
        </div>
      </div>
    </div>
  );
}
