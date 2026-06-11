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
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-600">Loading history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-extrabold text-gray-900 mb-6">
        Research History
      </h1>

      {tasks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500 mb-4">No research tasks yet.</p>
          <Link
            href="/research/new"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
          >
            Start Your First Research
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <Link
              key={task.task_id}
              href={`/research/${task.task_id}`}
              className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900 truncate flex-1 mr-4">
                  {task.query}
                </h3>
                <TaskStatusBadge status={task.status} />
              </div>
              <div className="flex gap-4 text-sm text-gray-500">
                <span>
                  {new Date(task.created_at).toLocaleDateString()}
                </span>
                {task.confidence_score != null && (
                  <span>
                    Confidence: {Math.round(task.confidence_score * 100)}%
                  </span>
                )}
                <span>{task.iteration_count} iterations</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
