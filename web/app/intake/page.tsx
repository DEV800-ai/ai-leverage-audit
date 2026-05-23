"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { runAudit } from "@/lib/api";

const STEPS = [
  "Your business",
  "Weekly workflows",
  "Tools & pain",
  "Budget & goals",
  "Review & submit",
];

interface IntakeForm {
  business_type: string;
  current_role: string;
  team_size: string;
  months_in_business: string;
  weekly_tasks_text: string;
  current_tools_text: string;
  top_time_sinks_text: string;
  error_sensitive_areas_text: string;
  customer_facing_areas_text: string;
  primary_goal_text: string;
  weekly_time_to_invest_hours: string;
  monthly_budget_usd: string;
  things_owner_refuses_to_automate_text: string;
  measurement_context_text: string;
}

const EMPTY: IntakeForm = {
  business_type: "",
  current_role: "",
  team_size: "",
  months_in_business: "",
  weekly_tasks_text: "",
  current_tools_text: "",
  top_time_sinks_text: "",
  error_sensitive_areas_text: "",
  customer_facing_areas_text: "",
  primary_goal_text: "",
  weekly_time_to_invest_hours: "",
  monthly_budget_usd: "",
  things_owner_refuses_to_automate_text: "",
  measurement_context_text: "",
};

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-gray-700 mb-1">{children}</label>;
}

function Hint({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-gray-400 mt-1">{children}</p>;
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
      {hint && <Hint>{hint}</Hint>}
    </div>
  );
}

function NAField({
  label,
  hint,
  naValue,
  value,
  onChange,
  children,
}: {
  label: string;
  hint?: string;
  naValue: string;
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
}) {
  const isNA = value === naValue;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <Label>{label}</Label>
        {!isNA && (
          <button
            type="button"
            onClick={() => onChange(naValue)}
            className="text-xs text-gray-400 hover:text-indigo-600 transition-colors ml-2 shrink-0"
          >
            N/A
          </button>
        )}
      </div>
      {isNA ? (
        <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
          <span className="text-sm text-gray-400 italic">Not applicable</span>
          <button
            type="button"
            onClick={() => onChange("")}
            className="text-xs text-indigo-600 hover:underline ml-4"
          >
            Clear
          </button>
        </div>
      ) : (
        children
      )}
      {hint && !isNA && <Hint>{hint}</Hint>}
    </div>
  );
}

const NA_ERROR_SENSITIVE =
  "Not applicable — this business has no error-sensitive or financially irreversible workflows.";
const NA_CUSTOMER_FACING =
  "Not applicable — this business has no direct customer-facing outputs or communications.";
const NA_REFUSES_AUTOMATE =
  "Not applicable — no specific restrictions; open to automating any eligible workflow.";

const inputCls =
  "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 " +
  "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent " +
  "placeholder:text-gray-300";

const textareaCls = inputCls + " resize-none";

export default function IntakePage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<IntakeForm>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set(field: keyof IntakeForm, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function canAdvance(): boolean {
    const ok = (v: string, min = 1) => v.trim().length >= min;
    if (step === 0) return ok(form.business_type) && ok(form.current_role);
    if (step === 1) return ok(form.weekly_tasks_text, 30) && ok(form.top_time_sinks_text, 30);
    if (step === 2)
      return (
        ok(form.current_tools_text, 30) &&
        (form.error_sensitive_areas_text === NA_ERROR_SENSITIVE || ok(form.error_sensitive_areas_text, 30)) &&
        (form.customer_facing_areas_text === NA_CUSTOMER_FACING || ok(form.customer_facing_areas_text, 30))
      );
    if (step === 3)
      return (
        ok(form.primary_goal_text, 30) &&
        (form.things_owner_refuses_to_automate_text === NA_REFUSES_AUTOMATE || ok(form.things_owner_refuses_to_automate_text, 30))
      );
    return true;
  }

  async function submit() {
    setSubmitting(true);
    setError(null);

    const MIN = 30;
    const short = (v: string) => v.trim().length < MIN;
    const naOk = (v: string, na: string) => v === na || !short(v);
    const problems: string[] = [];
    if (short(form.weekly_tasks_text)) problems.push("Weekly tasks — add more detail");
    if (short(form.top_time_sinks_text)) problems.push("Time sinks — add more detail");
    if (short(form.current_tools_text)) problems.push("Tools — add more detail");
    if (!naOk(form.error_sensitive_areas_text, NA_ERROR_SENSITIVE))
      problems.push("Error-sensitive areas — add more detail or mark N/A");
    if (!naOk(form.customer_facing_areas_text, NA_CUSTOMER_FACING))
      problems.push("Customer-facing areas — add more detail or mark N/A");
    if (short(form.primary_goal_text)) problems.push("Primary goal — add more detail");
    if (!naOk(form.things_owner_refuses_to_automate_text, NA_REFUSES_AUTOMATE))
      problems.push("Won't automate — add more detail or mark N/A");
    if (problems.length > 0) {
      setError("Please complete: " + problems.join(" · "));
      setSubmitting(false);
      return;
    }

    try {
      const intake = {
        ...form,
        team_size: parseInt(form.team_size) || 1,
        months_in_business: parseInt(form.months_in_business) || 1,
        weekly_time_to_invest_hours: parseFloat(form.weekly_time_to_invest_hours) || 2,
        monthly_budget_usd: parseInt(form.monthly_budget_usd) || 50,
      };
      const result = await runAudit(intake);
      router.push(`/report/${result.workflow_run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setSubmitting(false);
    }
  }

  const steps = [
    // Step 0 — Business basics
    <div key={0} className="flex flex-col gap-5">
      <Field label="What type of business do you run?" hint="e.g. 'Solo consulting practice', 'Shopify skincare brand', 'Dental clinic'">
        <input className={inputCls} value={form.business_type} onChange={(e) => set("business_type", e.target.value)} placeholder="Independent neighbourhood supermarket, ~800 SKUs, 4 staff" />
      </Field>
      <Field label="What is your role?">
        <input className={inputCls} value={form.current_role} onChange={(e) => set("current_role", e.target.value)} placeholder="Owner-operator — handles purchasing, supplier relations, and daily operations" />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Team size (including you)">
          <input type="number" min={1} className={inputCls} value={form.team_size} onChange={(e) => set("team_size", e.target.value)} placeholder="4" />
        </Field>
        <Field label="Months in business">
          <input type="number" min={1} className={inputCls} value={form.months_in_business} onChange={(e) => set("months_in_business", e.target.value)} placeholder="36" />
        </Field>
      </div>
    </div>,

    // Step 1 — Workflows
    <div key={1} className="flex flex-col gap-5">
      <Field label="Describe your typical weekly tasks" hint="List the recurring things you or your team do each week. Include rough time spent if you know it.">
        <textarea rows={6} className={textareaCls} value={form.weekly_tasks_text} onChange={(e) => set("weekly_tasks_text", e.target.value)} placeholder="Respond to customer emails (1h/day), create Instagram content (2h/week), process supplier invoices (3 invoices × 35min)..." />
      </Field>
      <Field label="What are your biggest time sinks?" hint="Be specific — describe the actual pain, not just a category. e.g. 'Answering the same 5 shipping questions every day' not just 'emails'.">
        <textarea rows={4} className={textareaCls} value={form.top_time_sinks_text} onChange={(e) => set("top_time_sinks_text", e.target.value)} placeholder="Answering the same shipping and return questions every day. Manual data entry for every supplier invoice — typing each line item from a PDF." />
      </Field>
    </div>,

    // Step 2 — Tools & sensitivity
    <div key={2} className="flex flex-col gap-5">
      <Field label="What tools do you currently use?">
        <textarea rows={3} className={textareaCls} value={form.current_tools_text} onChange={(e) => set("current_tools_text", e.target.value)} placeholder="Shopify, Gmail, Instagram, Canva, Google Sheets, WhatsApp for suppliers..." />
      </Field>
      <NAField
        label="Where would an error be most painful?"
        hint="Describe the workflows that touch customers, money, or data that's hard to reverse. What would make you lose sleep?"
        naValue={NA_ERROR_SENSITIVE}
        value={form.error_sensitive_areas_text}
        onChange={(v) => set("error_sensitive_areas_text", v)}
      >
        <textarea rows={3} className={textareaCls} value={form.error_sensitive_areas_text} onChange={(e) => set("error_sensitive_areas_text", e.target.value)} placeholder="Customer refund decisions, supplier purchase orders, and any pricing changes — a mistake here costs real money or damages trust." />
      </NAField>
      <NAField
        label="Which parts of your work are customer-facing?"
        hint="Where does a bad output directly affect what a customer sees or experiences?"
        naValue={NA_CUSTOMER_FACING}
        value={form.customer_facing_areas_text}
        onChange={(v) => set("customer_facing_areas_text", v)}
      >
        <textarea rows={3} className={textareaCls} value={form.customer_facing_areas_text} onChange={(e) => set("customer_facing_areas_text", e.target.value)} placeholder="All customer support replies, order confirmation emails, and anything posted on Instagram or the website." />
      </NAField>
    </div>,

    // Step 3 — Budget & goals
    <div key={3} className="flex flex-col gap-5">
      <Field label="What's your primary goal for using AI?">
        <textarea rows={3} className={textareaCls} value={form.primary_goal_text} onChange={(e) => set("primary_goal_text", e.target.value)} placeholder="Reduce time on customer support from 5h/week to under 1h, so I can focus on product development." />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Hours per week you can invest in setup" hint="Realistic — not aspirational.">
          <input type="number" min={0} step={0.5} className={inputCls} value={form.weekly_time_to_invest_hours} onChange={(e) => set("weekly_time_to_invest_hours", e.target.value)} placeholder="3" />
        </Field>
        <Field label="Monthly budget for AI tools ($)">
          <input type="number" min={0} className={inputCls} value={form.monthly_budget_usd} onChange={(e) => set("monthly_budget_usd", e.target.value)} placeholder="100" />
        </Field>
      </div>
      <NAField
        label="What will you never automate?"
        hint="Be specific. This protects you."
        naValue={NA_REFUSES_AUTOMATE}
        value={form.things_owner_refuses_to_automate_text}
        onChange={(v) => set("things_owner_refuses_to_automate_text", v)}
      >
        <textarea rows={3} className={textareaCls} value={form.things_owner_refuses_to_automate_text} onChange={(e) => set("things_owner_refuses_to_automate_text", e.target.value)} placeholder="Final refund decisions. Replies to angry or distressed customers. Any pricing changes." />
      </NAField>
      <Field label="Measurement baseline (optional)" hint="If you have numbers — volume, time per task, error rate — paste them here. They make your bet metrics concrete.">
        <textarea rows={4} className={textareaCls} value={form.measurement_context_text} onChange={(e) => set("measurement_context_text", e.target.value)} placeholder="I get ~100 support emails/week. 70% are order status or return requests, each takes 3-5 min. I spend ~5h/week on this." />
      </Field>
    </div>,

    // Step 4 — Review
    <div key={4} className="flex flex-col gap-4">
      <p className="text-sm text-gray-500">Review your answers before we run the audit. You can go back to edit any step.</p>
      {[
        ["Business", form.business_type],
        ["Role", form.current_role],
        ["Team / months", `${form.team_size} people · ${form.months_in_business} months`],
        ["Weekly tasks", form.weekly_tasks_text],
        ["Time sinks", form.top_time_sinks_text],
        ["Tools", form.current_tools_text],
        ["Error-sensitive areas", form.error_sensitive_areas_text],
        ["Customer-facing areas", form.customer_facing_areas_text],
        ["Primary goal", form.primary_goal_text],
        ["Budget", `${form.weekly_time_to_invest_hours}h/wk · $${form.monthly_budget_usd}/mo`],
        ["Won't automate", form.things_owner_refuses_to_automate_text],
      ].map(([label, value]) => (
        <div key={label} className="text-sm">
          <span className="font-medium text-gray-700">{label}: </span>
          <span className="text-gray-500">{value || <em className="text-gray-300">not filled</em>}</span>
        </div>
      ))}
    </div>,
  ];

  const isLast = step === STEPS.length - 1;

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-100 bg-white px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <span className="font-semibold text-gray-900 text-sm">AI Leverage Audit</span>
          <span className="text-xs text-gray-400">Step {step + 1} of {STEPS.length}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-100">
        <div
          className="h-full bg-indigo-500 transition-all duration-300"
          style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
        />
      </div>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-10">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{STEPS[step]}</h1>
        <p className="text-sm text-gray-400 mb-8">
          {step === 0 && "Tell us the basics about your business."}
          {step === 1 && "What does a typical week look like?"}
          {step === 2 && "Where does it hurt, and what can't go wrong?"}
          {step === 3 && "What are you trying to achieve, and what are your limits?"}
          {step === 4 && "Everything look right? We'll run the audit in about 30 seconds."}
        </p>

        {steps[step]}

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-10">
          <button
            onClick={() => setStep((s) => s - 1)}
            disabled={step === 0}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900
              disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>

          {isLast ? (
            <button
              onClick={submit}
              disabled={submitting}
              className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2.5
                rounded-lg font-medium text-sm hover:bg-indigo-700 transition-colors
                disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Running audit…
                </>
              ) : (
                <>Run my audit <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          ) : (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canAdvance()}
              className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2.5
                rounded-lg font-medium text-sm hover:bg-indigo-700 transition-colors
                disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </main>
  );
}
