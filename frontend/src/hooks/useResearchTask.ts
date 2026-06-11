"use client";

import { useState, useEffect, useCallback } from "react";
import { getTaskStatus, getReport } from "@/lib/api";
import type { ResearchTask, ResearchReport } from "@/types";

interface UseResearchTaskResult {
  task: ResearchTask | null;
  report: ResearchReport | null;
  loading: boolean;
  error: string | null;
  poll: () => void;
}

export function useResearchTask(taskId: string): UseResearchTaskResult {
  const [task, setTask] = useState<ResearchTask | null>(null);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!taskId) return;
    try {
      const taskData = await getTaskStatus(taskId);
      setTask(taskData);
      setError(null);

      if (
        (taskData.status === "complete" || taskData.status === "completed") &&
        !report
      ) {
        try {
          const reportData = await getReport(taskId);
          setReport(reportData);
        } catch {
          // report might not be ready yet
        }
      }

      if (
        taskData.status !== "complete" &&
        taskData.status !== "completed" &&
        taskData.status !== "failed"
      ) {
        return; // will be polled again
      }
      setLoading(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch task status"
      );
      setLoading(false);
    }
  }, [taskId, report]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const poll = useCallback(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  return { task, report, loading, error, poll };
}
