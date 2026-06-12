"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getHistory } from "@/lib/api";
import TaskStatusBadge from "@/components/TaskStatusBadge";
import type { ResearchTask } from "@/types";

export default function HistoryPage() {
  const [tasks, setTasks] = useState<ResearchTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getHistory();
        setTasks(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load history"
        );
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
        <div style={{ textAlign: "center" }}>
          <div className="spinner" style={{ margin: "0 auto 12px", width: "20px", height: "20px", borderWidth: "2px" }}></div>
          <p style={{ fontSize: "14px", color: "var(--color-muted)" }}>Loading history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%", padding: "24px" }}>
        <div style={{
          background: "rgba(198,69,69,0.08)", border: "1px solid rgba(198,69,69,0.25)",
          borderRadius: "var(--radius-md)", padding: "16px", maxWidth: "480px", width: "100%"
        }}>
          <h2 style={{ fontSize: "16px", fontWeight: 600, color: "var(--color-error)", marginBottom: "6px" }}>Error</h2>
          <p style={{ fontSize: "14px", color: "var(--color-body)" }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ overflow: "auto", height: "100%", padding: "32px 24px" }}>
      <div style={{ maxWidth: "640px", margin: "0 auto" }}>
        <h1 style={{
          fontFamily: "var(--font-display)", fontSize: "28px", fontWeight: 400,
          color: "var(--color-ink)", marginBottom: "24px", letterSpacing: "-0.3px"
        }}>
          Research History
        </h1>

        {tasks.length === 0 ? (
          <div style={{
            background: "var(--color-surface-card)", borderRadius: "var(--radius-lg)",
            padding: "32px", textAlign: "center"
          }}>
            <p style={{ fontSize: "14px", color: "var(--color-muted)", marginBottom: "16px" }}>
              No research tasks yet.
            </p>
            <Link
              href="/research/new"
              style={{
                display: "inline-block", padding: "9px 20px",
                background: "var(--color-primary)", color: "var(--color-on-primary)",
                borderRadius: "var(--radius-md)", fontSize: "14px", fontWeight: 500,
                textDecoration: "none"
              }}
            >
              Start Your First Research
            </Link>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {tasks.map((task) => (
              <Link
                key={task.task_id}
                href={`/research/${task.task_id}`}
                style={{
                  display: "block",
                  background: "var(--color-surface-card)",
                  borderRadius: "var(--radius-lg)",
                  padding: "16px 18px",
                  textDecoration: "none",
                  transition: "border-color 0.15s",
                  border: "1px solid transparent"
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--color-primary)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "transparent"; }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                  <h3 style={{
                    fontSize: "14px", fontWeight: 500, color: "var(--color-ink)",
                    flex: 1, marginRight: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
                  }}>
                    {task.query}
                  </h3>
                  <TaskStatusBadge status={task.status} />
                </div>
                <div style={{ display: "flex", gap: "12px", fontSize: "12px", color: "var(--color-muted-soft)" }}>
                  <span>{new Date(task.created_at).toLocaleDateString()}</span>
                  {task.confidence_score != null && (
                    <span>Confidence: {Math.round(task.confidence_score * 100)}%</span>
                  )}
                  <span>{task.iteration_count} iterations</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
