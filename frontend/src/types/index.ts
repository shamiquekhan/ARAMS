export interface ResearchTask {
  task_id: string;
  query: string;
  status: string;
  iteration_count: number;
  confidence_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface ResearchReport {
  report_id: string;
  title: string;
  executive_summary: string;
  full_content: string;
  citations: Array<Record<string, unknown>>;
  word_count: number;
  created_at: string;
}

export interface ResearchRequest {
  query: string;
  depth?: "shallow" | "medium" | "deep";
  format?: "markdown" | "pdf" | "html";
}

export type TaskStatus =
  | "pending"
  | "running"
  | "planning_complete"
  | "source_evaluating"
  | "fact_checking"
  | "reflecting"
  | "synthesizing"
  | "writing_report"
  | "complete"
  | "failed";
