const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AuditResponse {
  workflow_run_id: string;
  accepted: boolean;
  summary: string;
  markdown: string;
  state: Record<string, unknown>;
}

export interface RunSummary {
  workflow_run_id: string;
  status: string;
  started_at: string;
  cycle_number: number | null;
}

export async function runAudit(intake: Record<string, unknown>): Promise<AuditResponse> {
  const res = await fetch(`${API_BASE}/api/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intake }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Audit failed");
  }
  return res.json();
}

export async function getAudit(id: string): Promise<AuditResponse> {
  const res = await fetch(`${API_BASE}/api/audit/${id}`);
  if (!res.ok) throw new Error("Report not found");
  return res.json();
}

export async function runReflect(
  outcomeReport: Record<string, unknown>,
  priorWorkflowRunId: string,
): Promise<AuditResponse> {
  const res = await fetch(`${API_BASE}/api/reflect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      outcome_report: outcomeReport,
      prior_workflow_run_id: priorWorkflowRunId,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Reflection failed");
  }
  return res.json();
}

export async function getHistory(): Promise<RunSummary[]> {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) return [];
  return res.json();
}
