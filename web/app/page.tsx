import Link from "next/link";
import { ArrowRight, CheckCircle, Clock, TrendingUp } from "lucide-react";

const tiers = [
  {
    name: "AI Leverage Audit",
    price: "$20",
    freq: "one-time",
    description:
      "Find out exactly where AI can save you time — and where it shouldn't be touched.",
    includes: [
      "Workflow map of your business",
      "AI leverage score per workflow",
      "Top 3 opportunities ranked",
      "One recommended 30-day bet",
      "Keep-human areas clearly marked",
    ],
    cta: "Get your audit",
    href: "/intake",
    highlight: false,
  },
  {
    name: "AI Operating Mentor",
    price: "$100",
    freq: "per month",
    description:
      "Run the experiment, measure the result, evolve your playbook — one cycle at a time.",
    includes: [
      "Everything in the Audit",
      "30-day bet design and tracking",
      "Weekly review questions",
      "Day-30 outcome report",
      "Continuation audit each cycle",
      "Business AI Playbook (builds over time)",
    ],
    cta: "Start mentoring",
    href: "/intake?plan=mentor",
    highlight: true,
  },
  {
    name: "AI Operating Setup",
    price: "$500",
    freq: "fixed scope",
    description:
      "One full Diagnose → Test → Evolve cycle, delivered as a completed engagement.",
    includes: [
      "AI Leverage Audit",
      "One 30-day bet, reviewed",
      "Business AI Maturity Profile",
      "Business AI Playbook v1",
      "Recommended AI stack",
      "90-day roadmap",
    ],
    cta: "Book a setup",
    href: "/intake?plan=setup",
    highlight: false,
  },
];

const steps = [
  {
    icon: Clock,
    title: "Tell us about your business",
    body: "A short intake: your workflows, tools, biggest time sinks, and what you refuse to automate.",
  },
  {
    icon: TrendingUp,
    title: "Get your AI Leverage Audit",
    body: "We score every workflow across value, risk, and owner capacity. You see where AI helps — and where it doesn't.",
  },
  {
    icon: CheckCircle,
    title: "Test one bet for 30 days",
    body: "One specific workflow. One hypothesis. Measurable success and failure criteria. No guessing.",
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-gray-100 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <span className="font-semibold text-gray-900">AI Leverage Audit</span>
          <div className="flex items-center gap-6">
            <Link
              href="/about"
              className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
            >
              About
            </Link>
            <Link
              href="/history"
              className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
            >
              Past audits
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
        <p className="text-sm font-medium text-indigo-600 mb-4 tracking-wide uppercase">
          Diagnose · Test · Evolve
        </p>
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 leading-tight mb-6">
          Find where AI actually
          <br className="hidden sm:block" /> helps your business.
        </h1>
        <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10">
          Not a chatbot. Not an automation builder. A structured audit that tells you
          which workflow to test first — and whether it worked.
        </p>
        <Link
          href="/intake"
          className="inline-flex items-center gap-2 bg-indigo-600 text-white
            px-7 py-3.5 rounded-lg font-medium hover:bg-indigo-700 transition-colors text-lg"
        >
          Get your audit <ArrowRight className="w-5 h-5" />
        </Link>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <h2 className="text-center text-2xl font-semibold text-gray-900 mb-12">
          How it works
        </h2>
        <div className="grid sm:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <div key={i} className="flex flex-col items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                <step.icon className="w-5 h-5 text-indigo-600" />
              </div>
              <h3 className="font-semibold text-gray-900">{step.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-center text-2xl font-semibold text-gray-900 mb-4">
            Choose your entry point
          </h2>
          <p className="text-center text-gray-500 mb-12">
            Start with a one-time audit. Upgrade to mentoring when you're ready to run the
            experiment.
          </p>
          <div className="grid sm:grid-cols-3 gap-6">
            {tiers.map((tier) => (
              <div
                key={tier.name}
                className={`rounded-xl p-6 flex flex-col gap-5 ${
                  tier.highlight
                    ? "bg-indigo-600 text-white ring-2 ring-indigo-600"
                    : "bg-white border border-gray-200"
                }`}
              >
                <div>
                  <p
                    className={`text-sm font-medium mb-1 ${
                      tier.highlight ? "text-indigo-200" : "text-gray-500"
                    }`}
                  >
                    {tier.name}
                  </p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold">{tier.price}</span>
                    <span
                      className={`text-sm ${
                        tier.highlight ? "text-indigo-200" : "text-gray-400"
                      }`}
                    >
                      {tier.freq}
                    </span>
                  </div>
                  <p
                    className={`text-sm mt-3 leading-relaxed ${
                      tier.highlight ? "text-indigo-100" : "text-gray-500"
                    }`}
                  >
                    {tier.description}
                  </p>
                </div>
                <ul className="flex flex-col gap-2 flex-1">
                  {tier.includes.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-sm">
                      <CheckCircle
                        className={`w-4 h-4 mt-0.5 shrink-0 ${
                          tier.highlight ? "text-indigo-200" : "text-indigo-500"
                        }`}
                      />
                      <span className={tier.highlight ? "text-indigo-50" : "text-gray-600"}>
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={tier.href}
                  className={`text-center py-2.5 rounded-lg font-medium text-sm transition-colors ${
                    tier.highlight
                      ? "bg-white text-indigo-600 hover:bg-indigo-50"
                      : "bg-indigo-600 text-white hover:bg-indigo-700"
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center text-sm text-gray-400 py-10">
        AI Leverage Audit · Built for solopreneurs and small business owners
      </footer>
    </main>
  );
}
