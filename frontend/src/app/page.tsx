"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startResearch } from "@/lib/api";

const SUGGESTIONS = [
  {
    title: "Health & Science",
    desc: "Microplastics in drinking water and their health effects",
    query: "What are the health effects of microplastics in drinking water?"
  },
  {
    title: "Technology",
    desc: "Quantum computing's impact on modern cryptography",
    query: "How will quantum computing break modern encryption?"
  },
  {
    title: "Energy",
    desc: "Solid-state battery development and timeline",
    query: "What is the current state of solid-state battery development?"
  },
  {
    title: "AI & Society",
    desc: "AI agents and the transformation of labor markets",
    query: "How are AI agents changing the future of work?"
  }
];

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (query: string) => {
    setLoading(true);
    try {
      const data = await startResearch({ query });
      router.push(`/research/${data.task_id}`);
    } catch {
      setLoading(false);
    }
  };

  return (
    <div className="welcome">
      <div className="welcome-logo">A</div>
      <div className="welcome-title">What do you want to research?</div>
      <div className="welcome-sub">
        Ask anything. AMARS deploys 8 specialized agents to search, verify, and synthesize a cited research report.
      </div>

      <div className="suggestion-grid">
        {SUGGESTIONS.map((s) => (
          <div
            key={s.title}
            className="suggestion-card"
            onClick={() => handleSubmit(s.query)}
          >
            <div className="suggestion-title">{s.title}</div>
            <div className="suggestion-desc">{s.desc}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "24px", width: "100%", maxWidth: "540px" }}>
        <div className="input-box">
          <textarea
            placeholder="Type your research question..."
            rows={1}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                const val = (e.target as HTMLTextAreaElement).value.trim();
                if (val) handleSubmit(val);
              }
            }}
            onInput={(e) => {
              const el = e.target as HTMLTextAreaElement;
              el.style.height = "auto";
              el.style.height = el.scrollHeight + "px";
            }}
            disabled={loading}
          />
          <div className="input-actions">
            <button
              className="send-btn"
              disabled={loading}
              onClick={() => {
                const textarea = document.querySelector("textarea");
                if (textarea && textarea.value.trim()) handleSubmit(textarea.value.trim());
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
        <div className="input-footer">
          <span className="input-hint">Press</span>
          <span className="shortcut">Ctrl</span>
          <span className="shortcut">Enter</span>
          <span className="input-hint">to send · AMARS may make mistakes. Verify important claims.</span>
        </div>
      </div>
    </div>
  );
}
