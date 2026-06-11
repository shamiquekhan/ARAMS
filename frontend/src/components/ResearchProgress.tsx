"use client";

import { useResearchStore } from "@/stores/researchStore";
import type { TaskStatus } from "@/types";

const statusSteps: { key: TaskStatus; label: string }[] = [
  { key: "pending", label: "Queued" },
  { key: "planning_complete", label: "Planning" },
  { key: "running", label: "Researching" },
  { key: "source_evaluating", label: "Evaluating Sources" },
  { key: "fact_checking", label: "Fact Checking" },
  { key: "reflecting", label: "Reflecting" },
  { key: "synthesizing", label: "Synthesizing" },
  { key: "writing_report", label: "Writing Report" },
  { key: "complete", label: "Complete" },
];

const statusIndex: Record<string, number> = {};
statusSteps.forEach((s, i) => {
  statusIndex[s.key] = i;
});

interface ResearchProgressProps {
  currentStatus: string;
}

export default function ResearchProgress({
  currentStatus,
}: ResearchProgressProps) {
  const currentIdx = statusIndex[currentStatus] ?? 0;

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between">
        {statusSteps.map((step, idx) => (
          <div key={step.key} className="flex flex-col items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                idx <= currentIdx
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              {idx <= currentIdx ? "✓" : idx + 1}
            </div>
            <span
              className={`text-xs mt-1 ${
                idx <= currentIdx ? "text-blue-600 font-medium" : "text-gray-400"
              }`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
      <div className="relative mt-2">
        <div className="absolute top-0 left-0 h-1 bg-gray-200 w-full rounded" />
        <div
          className="absolute top-0 left-0 h-1 bg-blue-600 rounded transition-all duration-500"
          style={{ width: `${(currentIdx / (statusSteps.length - 1)) * 100}%` }}
        />
      </div>
    </div>
  );
}
