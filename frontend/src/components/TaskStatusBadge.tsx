"use client";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  planning_complete: "bg-purple-100 text-purple-800",
  source_evaluating: "bg-indigo-100 text-indigo-800",
  fact_checking: "bg-orange-100 text-orange-800",
  reflecting: "bg-teal-100 text-teal-800",
  synthesizing: "bg-pink-100 text-pink-800",
  writing_report: "bg-violet-100 text-violet-800",
  complete: "bg-green-100 text-green-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

interface TaskStatusBadgeProps {
  status: string;
}

export default function TaskStatusBadge({ status }: TaskStatusBadgeProps) {
  const colorClass =
    statusColors[status] || "bg-gray-100 text-gray-800";
  const label = status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
    >
      {label}
    </span>
  );
}
