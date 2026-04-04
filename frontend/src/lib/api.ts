import type { Case, CaseCreate, Subject, SubjectCreate, SubjectUpdate, InvestigationJob, Report } from "@/types";
import { supabase } from "./supabase";

// All requests go through Next.js rewrite proxy → avoids CORS entirely
const BASE = "/api/backend";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Attach the current user's access token so the backend can verify identity
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Cases
export const getCases = () => request<Case[]>("/cases");
export const getCase = (id: string) => request<Case>(`/cases/${id}`);
export const createCase = (body: CaseCreate) =>
  request<Case>("/cases", { method: "POST", body: JSON.stringify(body) });
export const updateCase = (id: string, body: Partial<CaseCreate & { status: string }>) =>
  request<Case>(`/cases/${id}`, { method: "PATCH", body: JSON.stringify(body) });
export const deleteCase = (id: string) =>
  request<void>(`/cases/${id}`, { method: "DELETE" });

// Subjects
export const getSubjects = (caseId?: string) =>
  request<Subject[]>(`/subjects${caseId ? `?case_id=${caseId}` : ""}`);
export const getSubject = (id: string) => request<Subject>(`/subjects/${id}`);
export const createSubject = (body: SubjectCreate) =>
  request<Subject>("/subjects", { method: "POST", body: JSON.stringify(body) });
export const updateSubject = (id: string, body: SubjectUpdate) =>
  request<Subject>(`/subjects/${id}`, { method: "PATCH", body: JSON.stringify(body) });

// Agent
export const runInvestigation = (caseId: string, subjectId: string) =>
  request<InvestigationJob>("/agent/run", {
    method: "POST",
    body: JSON.stringify({ case_id: caseId, subject_id: subjectId }),
  });
export const getJobStatus = (jobId: string) =>
  request<InvestigationJob>(`/agent/status/${jobId}`);

// Reports
export const getReports = (caseId?: string) =>
  request<Report[]>(`/reports${caseId ? `?case_id=${caseId}` : ""}`);
export const getReport = (id: string) => request<Report>(`/reports/${id}`);
export const emailReport = (reportId: string, email: string, subjectName: string) =>
  request<{ message: string }>(`/reports/${reportId}/email`, {
    method: "POST",
    body: JSON.stringify({ email, subject_name: subjectName }),
  });
