"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { AlertTriangle, ArrowLeft, CheckCircle2, Loader2 } from "lucide-react";
import { getAudit, type AuditResponse } from "@/lib/api";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<AuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getAudit(id)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Report not found</h1>
          <p className="text-gray-500 text-sm mb-6">{error}</p>
          <button onClick={() => router.push("/")} className="text-sm text-indigo-600 hover:underline">
            ← Back to home
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

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-100 bg-white px-6 py-4 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <button
            onClick={() => router.push("/history")}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> All audits
          </button>
          <div className="flex items-center gap-2">
            {data.accepted ? (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                <CheckCircle2 className="w-3.5 h-3.5" /> Accepted
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs font-medium text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
                <AlertTriangle className="w-3.5 h-3.5" /> Concerns
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Report body */}
      <div className="max-w-3xl mx-auto px-6 py-10">
        {!data.accepted && (
          <div className="mb-8 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
            <strong>Audit had concerns:</strong> {data.summary}
          </div>
        )}

        <article className="prose prose-gray prose-headings:font-semibold prose-h1:text-2xl
          prose-h2:text-xl prose-h2:mt-10 prose-h3:text-base prose-table:text-sm
          prose-code:text-indigo-600 prose-code:bg-indigo-50 prose-code:px-1
          prose-code:rounded prose-code:before:content-none prose-code:after:content-none
          max-w-none">
          <ReactMarkdown>{data.markdown}</ReactMarkdown>
        </article>

        {/* Run ID */}
        <p className="mt-12 text-xs text-gray-300 text-center">
          Audit ID: {data.workflow_run_id}
        </p>
      </div>
    </main>
  );
}
