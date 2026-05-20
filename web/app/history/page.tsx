"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Clock } from "lucide-react";
import { getHistory, type RunSummary } from "@/lib/api";

function statusBadge(status: string) {
  const base = "text-xs font-medium px-2 py-0.5 rounded-full";
  if (status === "succeeded") return `${base} bg-emerald-50 text-emerald-700`;
  if (status === "failed") return `${base} bg-red-50 text-red-700`;
  return `${base} bg-gray-100 text-gray-500`;
}

function fmt(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function HistoryPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then(setRuns)
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="border-b border-gray-100 bg-white px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Home
          </Link>
          <span className="font-semibold text-gray-900 text-sm">Audit history</span>
          <Link href="/intake" className="text-sm text-indigo-600 hover:underline">
            New audit →
          </Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Past audits</h1>
        <p className="text-sm text-gray-400 mb-8">All audit runs from this instance.</p>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Clock className="w-4 h-4 animate-pulse" /> Loading…
          </div>
        ) : runs.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-400 text-sm mb-4">No audits yet.</p>
            <Link href="/intake" className="text-indigo-600 text-sm hover:underline">
              Run your first audit →
            </Link>
          </div>
        ) : (
          <ul className="flex flex-col gap-3">
            {runs.map((run) => (
              <li key={run.workflow_run_id}>
                <Link
                  href={`/report/${run.workflow_run_id}`}
                  className="flex items-center justify-between bg-white border border-gray-200
                    rounded-xl px-5 py-4 hover:border-indigo-300 hover:shadow-sm transition-all group"
                >
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className={statusBadge(run.status)}>{run.status}</span>
                      {run.cycle_number && run.cycle_number > 1 && (
                        <span className="text-xs text-indigo-500 font-medium">
                          Cycle {run.cycle_number}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400">{fmt(run.started_at)}</p>
                    <p className="text-xs text-gray-300 font-mono">{run.workflow_run_id}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-indigo-500 transition-colors" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
