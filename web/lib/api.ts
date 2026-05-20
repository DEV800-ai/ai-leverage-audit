const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ThirtyDayBet {
  target_workflow_id: string;
  title: string;
  hypothesis: string;
  success_metric: string;
  failure_metric: string;
  weekly_plan: string[];
  first_48h_actions: string[];
  expected_asset_created: string;
  estimated_weekly_time_hours: number;
  estimated_setup_cost_usd: number;
}

export interface KeepHumanArea {
  area: string;
  reason: string;
  severity: "low" | "medium" | "high";
}

export interface AutomationRisk {
  automation: string;
  what_could_break: string;
  mitigation: string;
}

export interface AgencyCheckpoint {
  trigger: string;
  required_action: string;
  cadence: "per_event" | "daily" | "weekly" | "monthly" | null;
}

export interface RiskAndAgencyMap {
  keep_human_areas: KeepHumanArea[];
  automation_risks: AutomationRisk[];
  agency_checkpoints: AgencyCheckpoint[];
  weekly_review_questions: string[];
  compliance_or_legal_flags: string[];
}

export interface PlaybookEntry {
  workflow_id: string;
  current_status: "not_yet_tested" | "experimenting" | "validated" | "rejected";
  summary: string;
  cycle_introduced: number | null;
  last_outcome_summary: string | null;
}

export interface FirstPlaybook {
  title: string;
  business_summary: string;
  workflow_entries: PlaybookEntry[];
  rules_for_human_involvement: string[];
  open_questions: string[];
  next_review_offset_days: number;
  cycle_number: number;
}

export interface OutcomeReport {
  prior_workflow_run_id: string;
  prior_bet_title: string;
  outcome: "succeeded" | "failed" | "mixed" | "abandoned";
  success_metric_triggered: boolean;
  failure_metric_triggered: boolean;
  actual_weekly_hours_invested: number;
  actual_setup_cost_usd: number;
  what_worked_text: string;
  what_surprised_text: string;
  what_owner_would_change_text: string;
  intent: "continue" | "pivot" | "stop";
}

export interface AuditState {
  workflow_run_id: string;
  thirty_day_bet: ThirtyDayBet;
  risk_agency_map: RiskAndAgencyMap;
  first_playbook: FirstPlaybook;
}

export interface AuditResponse {
  workflow_run_id: string;
  accepted: boolean;
  summary: string;
  markdown: string;
  state: AuditState;
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
  outcomeReport: OutcomeReport,
): Promise<AuditResponse> {
  const res = await fetch(`${API_BASE}/api/reflect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      outcome_report: outcomeReport,
      prior_workflow_run_id: outcomeReport.prior_workflow_run_id,
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
