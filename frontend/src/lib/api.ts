import axios from "axios";
import type { ResearchRequest, ResearchTask, ResearchReport } from "@/types";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  timeout: 30000,
});

export async function startResearch(
  request: ResearchRequest
): Promise<{ task_id: string; status: string }> {
  const { data } = await api.post("/research", request);
  return data;
}

export async function getTaskStatus(
  taskId: string
): Promise<ResearchTask> {
  const { data } = await api.get(`/research/${taskId}`);
  return data;
}

export async function getReport(
  taskId: string
): Promise<ResearchReport> {
  const { data } = await api.get(`/reports/${taskId}`);
  return data;
}

export async function approveReport(
  taskId: string
): Promise<void> {
  await api.post(`/reports/${taskId}/approve`);
}

export async function getHistory(
  skip = 0,
  limit = 20
): Promise<ResearchTask[]> {
  const { data } = await api.get("/history", { params: { skip, limit } });
  return data;
}
