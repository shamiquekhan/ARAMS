"use client";

import { useParams, useRouter } from "next/navigation";
import { useResearchTask } from "@/hooks/useResearchTask";
import { getReport } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import { useState, useEffect } from "react";
import type { ResearchReport } from "@/types";

const AGENTS = [
  "Supervisor", "Research Agent", "Source Evaluator",
  "Fact Checker", "Reflection Agent", "Synthesis Agent",
  "Report Writer", "Memory Agent"
];

const STATUS_MAP: Record<string, number> = {
  pending: 0,
  planning_complete: 1,
  running: 2,
  source_evaluating: 3,
  fact_checking: 4,
  reflecting: 5,
  synthesizing: 6,
  writing_report: 7,
  awaiting_approval: 7,
  complete: 8,
  completed: 8,
  failed: -1
};

function getAgentStatus(agentIndex: number, currentPhase: number, isFailed: boolean): { label: string; cls: string; showSpinner: boolean } {
  if (isFailed) return { label: "Failed", cls: "status-running", showSpinner: false };
  if (agentIndex < currentPhase) return { label: "Done", cls: "status-done", showSpinner: false };
  if (agentIndex === currentPhase) {
    if (currentPhase === 8) return { label: "Done", cls: "status-done", showSpinner: false };
    return { label: "Running", cls: "status-running", showSpinner: true };
  }
  return { label: "Waiting", cls: "status-waiting", showSpinner: false };
}

function AgentAvatar({ color = "var(--color-primary)" }: { color?: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  );
}

export default function ResearchTaskPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.task_id as string;
  const { task, loading, error } = useResearchTask(taskId);
  const [reportData, setReportData] = useState<ResearchReport | null>(null);
  const [reportError, setReportError] = useState(false);

  useEffect(() => {
    if (task && (task.status === "complete" || task.status === "completed")) {
      getReport(taskId)
        .then(setReportData)
        .catch(() => setReportError(true));
    }
  }, [task, taskId]);

  const isComplete = task?.status === "complete" || task?.status === "completed";
  const isFailed = task?.status === "failed";
  const phase = STATUS_MAP[task?.status || "pending"] ?? 0;

  if (loading && !task) {
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
        <div className="welcome-title">Loading research task...</div>
        <div className="welcome-sub">
          <div className="spinner" style={{ margin: "20px auto", width: "20px", height: "20px", borderWidth: "2px" }}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="welcome">
        <div className="welcome-title" style={{ color: "var(--color-error)" }}>Error</div>
        <div className="welcome-sub" style={{ color: "var(--color-error)" }}>{error}</div>
        <button className="new-research-btn" style={{ width: "auto" }} onClick={() => router.push("/research/new")}>
          Start New Research
        </button>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="welcome">
        <div className="welcome-title">Task Not Found</div>
        <div className="welcome-sub">This task may have expired or the backend was restarted.</div>
        <button className="new-research-btn" style={{ width: "auto" }} onClick={() => router.push("/research/new")}>
          Start New Research
        </button>
      </div>
    );
  }

  const doneCount = AGENTS.filter((_, i) => i < phase || isComplete).length;
  const confidence = task.confidence_score ?? 0;

  return (
    <>
      <div className="chat-topbar">
        <div className="chat-topic">{task.query}</div>
        <div className="topbar-actions">
          {(isComplete || phase > 5) && (
            <div className="confidence-badge">
              <div className="dot-green"></div>
              {Math.round(confidence * 100)}% confidence
            </div>
          )}
        </div>
      </div>

      <div className="messages">
        <div className="msg-wrap">

          <div className="msg-user">
            <div className="msg-user-bubble">{task.query}</div>
          </div>

          <div className="msg-agent">
            <div className="agent-avatar">
              <AgentAvatar />
            </div>
            <div className="agent-body">
              <div className="agent-name-row">
                <span className="agent-name">AMARS</span>
                <span className="agent-timestamp">
                  {isComplete ? "Research complete" : "Research in progress"}
                </span>
              </div>
              <div className="agent-progress">
                <div className="progress-header">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-on-dark-soft)" strokeWidth="2">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                  </svg>
                  <span className="progress-title">Agent Pipeline</span>
                  <span className="progress-count">{doneCount} of {AGENTS.length} complete</span>
                </div>
                <div className="agent-rows">
                  {AGENTS.map((name, i) => {
                    const st = getAgentStatus(i, phase, isFailed);
                    return (
                      <div className="agent-row" key={name}>
                        <span className="agent-row-name">{name}</span>
                        {st.showSpinner && <div className="spinner"></div>}
                        <span className={`agent-row-status ${st.cls}`}>{st.label}</span>
                      </div>
                    );
                  })}
                </div>

                {phase > 0 && (
                  <div className="confidence-bar-wrap">
                    <div className="confidence-bar-label">
                      <span>Research confidence</span>
                      <span style={{ color: "var(--color-success)" }}>{Math.round(confidence * 100)}%</span>
                    </div>
                    <div className="confidence-bar-track">
                      <div className="confidence-bar-fill" style={{ width: `${Math.round(confidence * 100)}%` }}></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {isComplete && (
            <div className="divider-label">
              <div className="divider-line"></div>
              <div className="divider-text">RESEARCH COMPLETE</div>
              <div className="divider-line"></div>
            </div>
          )}

          {(isComplete && reportData) && (
            <div className="msg-agent">
              <div className="agent-avatar">
                <AgentAvatar />
              </div>
              <div className="agent-body">
                <div className="agent-name-row">
                  <span className="agent-name">AMARS</span>
                  <span className="agent-timestamp">{reportData.word_count} words · {task.iteration_count} research passes</span>
                </div>
                <div className="agent-content report-content">
                  <ReactMarkdown>{reportData.full_content}</ReactMarkdown>
                </div>

                {reportData.citations && reportData.citations.length > 0 && (
                  <div className="sources-strip">
                    {reportData.citations.map((c: Record<string, unknown>, idx: number) => {
                      const url = c.url ? String(c.url) : null;
                      const title = (c.title ? String(c.title) : url) || "Source";
                      return (
                        <a key={idx} className="source-chip" href={url ?? "#"} target="_blank" rel="noopener noreferrer">
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                          </svg>
                          {title.slice(0, 30)}
                        </a>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {(isComplete && !reportData && !reportError) && (
            <div className="msg-agent">
              <div className="agent-avatar">
                <AgentAvatar />
              </div>
              <div className="agent-body">
                <div className="agent-content">
                  <p>Research is complete but the report is loading. Please wait...</p>
                </div>
              </div>
            </div>
          )}

          {isFailed && (
            <div className="msg-agent">
              <div className="agent-avatar">
                <AgentAvatar color="var(--color-error)" />
              </div>
              <div className="agent-body">
                <div className="agent-name-row">
                  <span className="agent-name" style={{ color: "var(--color-error)" }}>Research Failed</span>
                </div>
                <div className="agent-content">
                  <p>The research task encountered an error. Please try again.</p>
                </div>
                <button className="new-research-btn" style={{ width: "auto" }} onClick={() => router.push("/research/new")}>
                  Start New Research
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
