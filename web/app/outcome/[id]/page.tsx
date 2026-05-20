"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { getAudit, runReflect, type AuditResponse, type OutcomeReport } from "@/lib/api";

const OUTCOME_OPTIONS: { value: OutcomeReport["outcome"]; label: string; description: string }[] = [
  { value: "succeeded", label: "Succeeded", description: "Hit the win condition" },
  { value: "mixed", label: "Mixed", description: "Some wins, some misses" },
  { value: "failed", label: "Failed", description: "Didn't move the needle" },
  { value: "abandoned", label: "Abandoned", description: "Stopped before day 30" },
];

const INTENT_OPTIONS: { value: OutcomeReport["intent"]; label: string; description: string }[] = [
  { value: "continue", label: "Continue", description: "Keep iterating on this workflow" },
  { value: "pivot", label: "Pivot", description: "Try a different workflow next cycle" },
  { value: "stop", label: "Stop", description: "AI isn't right for this area" },
];

function BoolToggle({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint: string;
  value: boolean | null;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium text-gray-900">{label}</p>
      <p className="text-xs text-gray-500 italic">{hint}</p>
      <div className="flex gap-2 mt-1">
        {[true, false].map((v) => (
          <button
            key={String(v)}
            type="button"
            onClick={() => onChange(v)}
            className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${
              value === v
                ? v
                  ? "bg-emerald-50 border-emerald-400 text-emerald-800 font-medium"
                  : "bg-red-50 border-red-400 text-red-800 font-medium"
                : "bg-white border-gray-200 text-gray-500 hover:border-gray-400"
            }`}
          >
            {v ? "Yes" : "No"}
          </button>
        ))}
      </div>
    </div>
  );
}

function TextArea({
  label,
  hint,
  value,
  onChange,
  minLength,
}: {
  label: string;
  hint: string;
  value: string;
  onChange: (v: string) => void;
  minLength: number;
}) {
  const ok = value.trim().length >= minLength;
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-gray-900">{label}</label>
      <p className="text-xs text-gray-500">{hint}</p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        className="w-full text-sm text-gray-900 bg-white border border-gray-200 rounded-xl
          px-4 py-3 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-300
          focus:border-indigo-400 resize-none transition"
        placeholder="Write at least 30 characters…"
      />
      <div className="flex justify-end">
        <span className={`text-xs ${ok ? "text-emerald-500" : "text-gray-300"}`}>
          {value.trim().length}/{minLength}
        </span>
      </div>
    </div>
  );
}

export default function OutcomePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [outcome, setOutcome] = useState<OutcomeReport["outcome"] | null>(null);
  const [successTriggered, setSuccessTriggered] = useState<boolean | null>(null);
  const [failureTriggered, setFailureTriggered] = useState<boolean | null>(null);
  const [actualHours, setActualHours] = useState("");
  const [actualCost, setActualCost] = useState("");
  const [whatWorked, setWhatWorked] = useState("");
  const [whatSurprised, setWhatSurprised] = useState("");
  const [whatToChange, setWhatToChange] = useState("");
  const [intent, setIntent] = useState<OutcomeReport["intent"] | null>(null);

  useEffect(() => {
    if (!id) return;
    getAudit(id)
      .then(setAudit)
      .catch((e) => setLoadError(e.message));
  }, [id]);

  function isValid() {
    return (
      outcome !== null &&
      successTriggered !== null &&
      failureTriggered !== null &&
      actualHours !== "" &&
      !isNaN(parseFloat(actualHours)) &&
      parseFloat(actualHours) >= 0 &&
      actualCost !== "" &&
      !isNaN(parseInt(actualCost)) &&
      parseInt(actualCost) >= 0 &&
      whatWorked.trim().length >= 30 &&
      whatSurprised.trim().length >= 30 &&
      whatToChange.trim().length >= 30 &&
      intent !== null
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid() || !audit) return;

    const report: OutcomeReport = {
      prior_workflow_run_id: id,
      prior_bet_title: audit.state.thirty_day_bet.title,
      outcome: outcome!,
      success_metric_triggered: successTriggered!,
      failure_metric_triggered: failureTriggered!,
      actual_weekly_hours_invested: parseFloat(actualHours),
      actual_setup_cost_usd: parseInt(actualCost),
      what_worked_text: whatWorked.trim(),
      what_surprised_text: whatSurprised.trim(),
      what_owner_would_change_text: whatToChange.trim(),
      intent: intent!,
    };

    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await runReflect(report);
      router.push(`/report/${result.workflow_run_id}`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Something went wrong");
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Run not found</h1>
          <p className="text-gray-500 text-sm mb-6">{loadError}</p>
          <button onClick={() => router.push("/history")} className="text-sm text-indigo-600 hover:underline">
            ← Back to history
          </button>
        </div>
      </main>
    );
  }

  if (!audit) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </main>
    );
  }

  const bet = audit.state.thirty_day_bet;

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-100 bg-white px-6 py-4 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <Link
            href={`/bet/${id}`}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Bet tracker
          </Link>
          <span className="font-semibold text-gray-900 text-sm">Day 30 debrief</span>
          <div className="w-24" />
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Intro */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs text-indigo-600 font-medium mb-2 uppercase tracking-wide">
            <RefreshCw className="w-3.5 h-3.5" /> Cycle reflection
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">How did it go?</h1>
          <p className="text-sm text-gray-500">
            Your answers feed into the next audit cycle. Be honest — a candid failure is more
            useful than an optimistic success.
          </p>
        </div>

        {/* Bet recap */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl px-5 py-4 mb-8">
          <p className="text-xs font-medium text-indigo-600 mb-1">Bet you ran</p>
          <p className="text-sm font-semibold text-indigo-900 mb-3">{bet.title}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <p className="text-indigo-500 font-medium mb-0.5">Win condition</p>
              <p className="text-indigo-800">{bet.success_metric}</p>
            </div>
            <div>
              <p className="text-indigo-500 font-medium mb-0.5">Stop condition</p>
              <p className="text-indigo-800">{bet.failure_metric}</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-10">
          {/* Overall outcome */}
          <section className="flex flex-col gap-3">
            <h2 className="font-semibold text-gray-900">Overall outcome</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {OUTCOME_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setOutcome(opt.value)}
                  className={`flex flex-col gap-0.5 px-3 py-3 rounded-xl border text-left transition-colors ${
                    outcome === opt.value
                      ? "bg-indigo-50 border-indigo-400"
                      : "bg-white border-gray-200 hover:border-gray-400"
                  }`}
                >
                  <span className={`text-sm font-semibold ${outcome === opt.value ? "text-indigo-800" : "text-gray-800"}`}>
                    {opt.label}
                  </span>
                  <span className={`text-xs ${outcome === opt.value ? "text-indigo-500" : "text-gray-400"}`}>
                    {opt.description}
                  </span>
                </button>
              ))}
            </div>
          </section>

          {/* Metric triggers */}
          <section className="flex flex-col gap-5">
            <h2 className="font-semibold text-gray-900">Did the metrics fire?</h2>
            <BoolToggle
              label="Success metric triggered"
              hint={bet.success_metric}
              value={successTriggered}
              onChange={setSuccessTriggered}
            />
            <BoolToggle
              label="Failure metric triggered"
              hint={bet.failure_metric}
              value={failureTriggered}
              onChange={setFailureTriggered}
            />
          </section>

          {/* Actuals */}
          <section className="flex flex-col gap-4">
            <h2 className="font-semibold text-gray-900">Actual investment</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-gray-900">
                  Hours / week
                  <span className="text-gray-400 font-normal ml-1">(estimated {bet.estimated_weekly_time_hours}h)</span>
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={actualHours}
                  onChange={(e) => setActualHours(e.target.value)}
                  className="w-full text-sm text-gray-900 bg-white border border-gray-200 rounded-xl
                    px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition"
                  placeholder="e.g. 2.5"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-gray-900">
                  Setup cost USD
                  <span className="text-gray-400 font-normal ml-1">(estimated ${bet.estimated_setup_cost_usd})</span>
                </label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={actualCost}
                  onChange={(e) => setActualCost(e.target.value)}
                  className="w-full text-sm text-gray-900 bg-white border border-gray-200 rounded-xl
                    px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition"
                  placeholder="e.g. 0"
                />
              </div>
            </div>
          </section>

          {/* Reflections */}
          <section className="flex flex-col gap-6">
            <h2 className="font-semibold text-gray-900">Reflections</h2>
            <TextArea
              label="What worked"
              hint="What went as expected or better than expected?"
              value={whatWorked}
              onChange={setWhatWorked}
              minLength={30}
            />
            <TextArea
              label="What surprised you"
              hint="What did you not anticipate — positive or negative?"
              value={whatSurprised}
              onChange={setWhatSurprised}
              minLength={30}
            />
            <TextArea
              label="What you'd change"
              hint="If you ran this bet again, what would you do differently?"
              value={whatToChange}
              onChange={setWhatToChange}
              minLength={30}
            />
          </section>

          {/* Intent */}
          <section className="flex flex-col gap-3">
            <h2 className="font-semibold text-gray-900">Next step</h2>
            <div className="grid grid-cols-3 gap-2">
              {INTENT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setIntent(opt.value)}
                  className={`flex flex-col gap-0.5 px-3 py-3 rounded-xl border text-left transition-colors ${
                    intent === opt.value
                      ? "bg-indigo-50 border-indigo-400"
                      : "bg-white border-gray-200 hover:border-gray-400"
                  }`}
                >
                  <span className={`text-sm font-semibold ${intent === opt.value ? "text-indigo-800" : "text-gray-800"}`}>
                    {opt.label}
                  </span>
                  <span className={`text-xs ${intent === opt.value ? "text-indigo-500" : "text-gray-400"}`}>
                    {opt.description}
                  </span>
                </button>
              ))}
            </div>
          </section>

          {/* Error */}
          {submitError && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-800">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{submitError}</span>
            </div>
          )}

          {/* Submit */}
          <div className="border-t border-gray-200 pt-6 flex flex-col items-center gap-3">
            {isValid() && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-600 mb-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> All fields complete
              </div>
            )}
            <button
              type="submit"
              disabled={!isValid() || submitting}
              className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm font-medium
                px-8 py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-40
                disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Running next cycle…
                </>
              ) : (
                <>
                  Run cycle 2 audit <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
            <p className="text-xs text-gray-400 text-center max-w-sm">
              This will run a new AI audit using your outcome as context. It takes about a minute.
            </p>
          </div>
        </form>
      </div>
    </main>
  );
}
