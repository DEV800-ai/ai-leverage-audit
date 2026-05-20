"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Circle,
  Clock,
  DollarSign,
  Loader2,
  ShieldAlert,
  Target,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { getAudit, type AuditResponse, type KeepHumanArea } from "@/lib/api";

function severityBadge(severity: KeepHumanArea["severity"]) {
  if (severity === "high")
    return "text-xs font-medium px-2 py-0.5 rounded-full bg-red-50 text-red-700";
  if (severity === "medium")
    return "text-xs font-medium px-2 py-0.5 rounded-full bg-amber-50 text-amber-700";
  return "text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-500";
}

function cadenceLabel(cadence: string | null) {
  if (!cadence) return null;
  const labels: Record<string, string> = {
    per_event: "per event",
    daily: "daily",
    weekly: "weekly",
    monthly: "monthly",
  };
  return labels[cadence] ?? cadence;
}

function storageKey(id: string) {
  return `bet-checklist-${id}`;
}

export default function BetPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<AuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (!id) return;
    getAudit(id)
      .then((d) => {
        setData(d);
        const saved = localStorage.getItem(storageKey(id));
        if (saved) setChecked(JSON.parse(saved));
      })
      .catch((e) => setError(e.message));
  }, [id]);

  function toggleCheck(i: number) {
    setChecked((prev) => {
      const next = { ...prev, [i]: !prev[i] };
      localStorage.setItem(storageKey(id), JSON.stringify(next));
      return next;
    });
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Run not found</h1>
          <p className="text-gray-500 text-sm mb-6">{error}</p>
          <button onClick={() => router.push("/history")} className="text-sm text-indigo-600 hover:underline">
            ← Back to history
          </button>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </main>
    );
  }

  const bet = data.state.thirty_day_bet;
  const risk = data.state.risk_agency_map;
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const totalActions = bet.first_48h_actions.length;

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-100 bg-white px-6 py-4 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Link
            href={`/report/${id}`}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Full report
          </Link>
          <span className="font-semibold text-gray-900 text-sm">30-Day Bet</span>
          <Link
            href={`/outcome/${id}`}
            className="text-sm text-indigo-600 hover:underline flex items-center gap-1"
          >
            Day 30 debrief <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-8">
        {/* Title + hypothesis */}
        <div>
          <div className="flex items-center gap-2 text-xs text-indigo-600 font-medium mb-2 uppercase tracking-wide">
            <Target className="w-3.5 h-3.5" /> Active experiment
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-3">{bet.title}</h1>
          <p className="text-gray-600 text-sm leading-relaxed italic">
            &ldquo;{bet.hypothesis}&rdquo;
          </p>
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            <Clock className="w-4 h-4 text-gray-400" />
            {bet.estimated_weekly_time_hours}h / week
          </div>
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            <DollarSign className="w-4 h-4 text-gray-400" />
            {bet.estimated_setup_cost_usd === 0
              ? "No setup cost"
              : `$${bet.estimated_setup_cost_usd} setup`}
          </div>
        </div>

        {/* Win / Stop conditions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Win condition</span>
            </div>
            <p className="text-sm text-emerald-900 leading-relaxed">{bet.success_metric}</p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-4 h-4 text-red-500" />
              <span className="text-xs font-semibold text-red-700 uppercase tracking-wide">Stop condition</span>
            </div>
            <p className="text-sm text-red-900 leading-relaxed">{bet.failure_metric}</p>
          </div>
        </div>

        {/* First 48h actions checklist */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">First 48 hours</h2>
            <span className="text-xs text-gray-400">
              {checkedCount}/{totalActions} done
            </span>
          </div>
          {checkedCount === totalActions && totalActions > 0 && (
            <div className="flex items-center gap-2 mb-4 text-xs text-emerald-700 bg-emerald-50 px-3 py-2 rounded-lg">
              <CheckCircle2 className="w-3.5 h-3.5" /> All actions complete — you&apos;re in Week 1
            </div>
          )}
          <ul className="flex flex-col gap-3">
            {bet.first_48h_actions.map((action, i) => (
              <li key={i} className="flex items-start gap-3 cursor-pointer" onClick={() => toggleCheck(i)}>
                {checked[i] ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
                ) : (
                  <Circle className="w-5 h-5 text-gray-300 mt-0.5 shrink-0" />
                )}
                <span className={`text-sm leading-relaxed ${checked[i] ? "line-through text-gray-400" : "text-gray-700"}`}>
                  {action}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* 4-week plan */}
        <div>
          <h2 className="font-semibold text-gray-900 mb-4">4-week plan</h2>
          <div className="flex flex-col gap-3">
            {bet.weekly_plan.map((week, i) => {
              const [label, ...rest] = week.split(":");
              return (
                <div
                  key={i}
                  className="flex gap-4 bg-white border border-gray-200 rounded-xl px-5 py-4"
                >
                  <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-sm font-semibold">
                    {i + 1}
                  </div>
                  <div>
                    <p className="text-xs font-medium text-indigo-600 mb-0.5">{label}</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{rest.join(":").trim()}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Expected asset */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl px-5 py-4">
          <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-1">
            Expected output by day 30
          </p>
          <p className="text-sm text-indigo-900">{bet.expected_asset_created}</p>
        </div>

        {/* Human guardrails */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <ShieldAlert className="w-4 h-4 text-gray-500" />
            <h2 className="font-semibold text-gray-900">Keep humans in the loop</h2>
          </div>
          <ul className="flex flex-col gap-2">
            {risk.keep_human_areas.map((item, i) => (
              <li key={i} className="flex items-start gap-3 bg-white border border-gray-200 rounded-xl px-5 py-3">
                <span className={`${severityBadge(item.severity)} mt-0.5 shrink-0`}>
                  {item.severity}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.area}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{item.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Weekly review questions */}
        <div>
          <h2 className="font-semibold text-gray-900 mb-4">Weekly review questions</h2>
          <ul className="flex flex-col gap-2">
            {risk.weekly_review_questions.map((q, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-gray-700 bg-white border border-gray-200 rounded-xl px-5 py-3">
                <span className="text-gray-300 font-mono text-xs mt-0.5 shrink-0">{String(i + 1).padStart(2, "0")}</span>
                {q}
              </li>
            ))}
          </ul>
        </div>

        {/* Agency checkpoints */}
        {risk.agency_checkpoints.length > 0 && (
          <div>
            <h2 className="font-semibold text-gray-900 mb-4">Checkpoints</h2>
            <ul className="flex flex-col gap-2">
              {risk.agency_checkpoints.map((cp, i) => (
                <li key={i} className="bg-white border border-gray-200 rounded-xl px-5 py-3">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-gray-900">{cp.trigger}</p>
                    {cp.cadence && (
                      <span className="text-xs text-gray-400 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">
                        {cadenceLabel(cp.cadence)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">{cp.required_action}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Day 30 CTA */}
        <div className="border-t border-gray-200 pt-8 flex flex-col items-center gap-3 text-center">
          <p className="text-sm text-gray-500">Reached day 30? Report what happened.</p>
          <Link
            href={`/outcome/${id}`}
            className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm font-medium px-6 py-3 rounded-xl hover:bg-indigo-700 transition-colors"
          >
            Submit day-30 outcome <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </main>
  );
}
