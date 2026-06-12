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
      <div className="welcome-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
          <line x1="12" y1="2" x2="12" y2="22" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <line x1="4.9" y1="4.9" x2="19.1" y2="19.1" />
          <line x1="19.1" y1="4.9" x2="4.9" y2="19.1" />
        </svg>
      </div>
      <div className="welcome-title">Start New Research</div>
      <div className="welcome-sub">
        Enter a query to start a new multi-agent research session.
      </div>

      {error && (
        <div style={{
          background: "rgba(198,69,69,0.08)", border: "1px solid rgba(198,69,69,0.25)",
          borderRadius: "var(--radius-md)", padding: "12px 16px", marginBottom: "20px",
          maxWidth: "540px", width: "100%", fontSize: "13px", color: "var(--color-error)"
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
              style={{ width: "auto", padding: "0 16px", borderRadius: "var(--radius-md)", gap: "6px" }}
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
