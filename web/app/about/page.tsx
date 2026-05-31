import Link from "next/link";
import { ArrowRight, BookOpen, RefreshCw, Shield, Target, TrendingUp, Zap } from "lucide-react";

const principles = [
  {
    icon: Target,
    title: "One bet at a time",
    body: "Generic AI advice gives you a list of ideas. This tool gives you one workflow to test, a measurable hypothesis, and explicit success and failure criteria. If it works, you know why. If it doesn't, you know that too.",
  },
  {
    icon: Shield,
    title: "Humans stay in the loop",
    body: "Every audit maps the areas where an AI error would be painful — refunds, legal, customer relationships, irreversible decisions. Those areas are marked keep-human. No pressure to automate everything.",
  },
  {
    icon: RefreshCw,
    title: "It compounds",
    body: "After 30 days you file an outcome report. The next audit reads that result and evolves your playbook — marking validated experiments, retiring failures, and finding the next bet. Your business AI strategy grows with your experience.",
  },
];

const phases = [
  {
    number: "01",
    name: "Diagnose",
    description:
      "You fill in a short intake — your workflows, tools, time sinks, and hard limits. The AI produces a workflow map, scores each workflow for leverage potential, and identifies the top opportunity.",
  },
  {
    number: "02",
    name: "Bet",
    description:
      "The audit designs one 30-day experiment: a specific workflow, a testable hypothesis, a concrete success metric, and a failure metric. You know exactly when the bet has won or lost.",
  },
  {
    number: "03",
    name: "Review",
    description:
      "At day 30 you report back: what happened, what surprised you, what you'd change. The tool reads your outcome and produces the next cycle's audit — informed by real results, not assumptions.",
  },
];

const techStack = [
  { label: "Reasoning", detail: "Claude (Anthropic) — multi-step reasoning pipeline" },
  { label: "Evaluation", detail: "Built-in judge agent validates every audit before delivery" },
  { label: "Storage", detail: "SQLite — runs locally, no data sent to third-party databases" },
  { label: "Frontend", detail: "Next.js + Tailwind CSS" },
  { label: "Backend", detail: "FastAPI + leverage-platform runtime" },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-gray-100 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href="/" className="font-semibold text-gray-900 hover:text-indigo-600 transition-colors">
            AI Leverage Audit
          </Link>
          <Link
            href="/intake"
            className="inline-flex items-center gap-1.5 text-sm bg-indigo-600 text-white
              px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            Get your audit <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-16 pb-12">
        <p className="text-sm font-medium text-indigo-600 mb-3 tracking-wide uppercase">
          About
        </p>
        <h1 className="text-4xl font-bold text-gray-900 leading-tight mb-5">
          What is the AI Leverage Audit?
        </h1>
        <p className="text-xl text-gray-500 leading-relaxed">
          A structured tool for solopreneurs and small business owners who want to use AI
          without guessing. It diagnoses your workflows, designs one testable experiment,
          and evolves your approach based on real results — not hype.
        </p>
      </section>

      {/* Problem */}
      <section className="bg-gray-50 py-14">
        <div className="max-w-3xl mx-auto px-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center shrink-0 mt-1">
              <Zap className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">The problem</h2>
              <p className="text-gray-500 leading-relaxed mb-4">
                Most small business owners are told to "use AI more" but left to figure out
                where, how, and whether it's actually working. The advice is generic, the
                tools are complex, and the results are hard to measure.
              </p>
              <p className="text-gray-500 leading-relaxed">
                The AI Leverage Audit applies a repeatable diagnosis framework to your
                specific workflows — the same way a business consultant would map processes
                before recommending changes. But faster, cheaper, and built specifically for
                owner-operators.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works — 3 phases */}
      <section className="max-w-3xl mx-auto px-6 py-16">
        <div className="flex items-center gap-2 mb-10">
          <TrendingUp className="w-5 h-5 text-indigo-600" />
          <h2 className="text-2xl font-semibold text-gray-900">How it works</h2>
        </div>
        <div className="flex flex-col gap-8">
          {phases.map((phase) => (
            <div key={phase.number} className="flex gap-6 items-start">
              <div className="shrink-0 w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center">
                <span className="text-xs font-bold text-indigo-600">{phase.number}</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{phase.name}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{phase.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Divider */}
      <div className="border-t border-gray-100 max-w-3xl mx-auto" />

      {/* Principles */}
      <section className="max-w-3xl mx-auto px-6 py-16">
        <div className="flex items-center gap-2 mb-10">
          <BookOpen className="w-5 h-5 text-indigo-600" />
          <h2 className="text-2xl font-semibold text-gray-900">Design principles</h2>
        </div>
        <div className="flex flex-col gap-10">
          {principles.map((p) => (
            <div key={p.title} className="flex gap-5 items-start">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0 mt-0.5">
                <p.icon className="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{p.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{p.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section className="bg-gray-50 py-14">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Under the hood</h2>
          <dl className="flex flex-col gap-3">
            {techStack.map((item) => (
              <div key={item.label} className="flex gap-4 text-sm">
                <dt className="w-24 shrink-0 font-medium text-gray-700">{item.label}</dt>
                <dd className="text-gray-500">{item.detail}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-6 py-16 text-center">
        <h2 className="text-2xl font-semibold text-gray-900 mb-3">
          Ready to find your leverage?
        </h2>
        <p className="text-gray-500 mb-8">
          The intake takes about 10 minutes. The audit runs in under a minute.
        </p>
        <Link
          href="/intake"
          className="inline-flex items-center gap-2 bg-indigo-600 text-white
            px-7 py-3.5 rounded-lg font-medium hover:bg-indigo-700 transition-colors text-lg"
        >
          Get your audit <ArrowRight className="w-5 h-5" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="text-center text-sm text-gray-400 py-10 border-t border-gray-100">
        AI Leverage Audit · Built for solopreneurs and small business owners
      </footer>
    </main>
  );
}
