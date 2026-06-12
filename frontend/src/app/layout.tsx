"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getHistory } from "@/lib/api";
import type { ResearchTask } from "@/types";
import "./globals.css";

function SpikeMark() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="12" y1="2" x2="12" y2="22" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <line x1="4.9" y1="4.9" x2="19.1" y2="19.1" />
      <line x1="19.1" y1="4.9" x2="4.9" y2="19.1" />
    </svg>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [history, setHistory] = useState<ResearchTask[]>([]);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    getHistory()
      .then(setHistory)
      .catch(() => {});
  }, []);

  const currentTaskId = pathname.match(/\/research\/([^/]+)/)?.[1];

  return (
    <html lang="en">
      <body>
        <div className="window-shell">
          <div className="titlebar">
            <div className="traffic-lights">
              <div className="dot close"></div>
              <div className="dot min"></div>
              <div className="dot max"></div>
            </div>
            <div className="titlebar-center">
              <div className="spike-mark" style={{ color: "var(--color-ink)" }}>
                <SpikeMark />
              </div>
              <span className="titlebar-name">AMARS</span>
            </div>
          </div>

          <div className="app-body">
            <aside className="sidebar">
              <div className="sidebar-top">
                <button className="new-research-btn" onClick={() => router.push("/research/new")}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                  New Research
                </button>
              </div>

              <div className="sidebar-search">
                <input type="text" placeholder="Search history..." readOnly />
              </div>

              <div className="sidebar-section">
                <div className="sidebar-label">Recent</div>
              </div>

              <div className="history-list">
                {history.length === 0 && (
                  <div className="history-item">
                    <div className="history-title" style={{ color: "var(--color-muted-soft)", fontSize: "11px" }}>
                      No research yet
                    </div>
                  </div>
                )}
                {history.map((task) => (
                  <a
                    key={task.task_id}
                    className={`history-item ${task.task_id === currentTaskId ? "active" : ""}`}
                    href={`/research/${task.task_id}`}
                    onClick={(e) => { e.preventDefault(); router.push(`/research/${task.task_id}`); }}
                  >
                    <div className="history-title">{task.query}</div>
                    <div className="history-meta">
                      <span className={`status-dot ${task.status === "complete" || task.status === "completed" ? "done" : task.status === "failed" ? "amber" : ""}`}></span>
                      <span>{task.status} · {new Date(task.created_at).toLocaleDateString()}</span>
                    </div>
                  </a>
                ))}
              </div>

              <div className="sidebar-bottom">
                <div className="user-row">
                  <div className="avatar">S</div>
                  <div className="user-info">
                    <div className="user-name">User</div>
                    <div className="user-plan">Free Plan</div>
                  </div>
                </div>
              </div>
            </aside>

            <main className="chat-main">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
