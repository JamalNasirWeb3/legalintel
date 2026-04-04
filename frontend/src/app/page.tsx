import Link from "next/link";

const FEATURES = [
  {
    icon: "⚖️",
    title: "Court Records",
    desc: "Federal & state filings, judgments, and case history from CourtListener and PACER.",
  },
  {
    icon: "🏠",
    title: "Property Records",
    desc: "County assessor and recorder databases for real estate owned directly or via trust.",
  },
  {
    icon: "🏢",
    title: "Business Filings",
    desc: "Secretary of State registrations, OpenCorporates, and corporate officer history.",
  },
  {
    icon: "👤",
    title: "People Records",
    desc: "Public people-finder data — addresses, relatives, associates, and aliases.",
  },
  {
    icon: "💼",
    title: "Employment",
    desc: "LinkedIn profiles, professional license databases (NPPES), and employer history.",
  },
  {
    icon: "📱",
    title: "Social Media",
    desc: "Publicly visible profiles on LinkedIn, X/Twitter, and Facebook.",
  },
];

export default function LandingPage() {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero */}
      <section className="text-center space-y-6 pt-8">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-xs font-medium px-3 py-1 rounded-full border border-blue-200">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block" />
          AI-Powered · US &amp; Pakistan Jurisdictions
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 leading-tight">
          Investigate Judgment Debtors
          <br />
          <span className="text-blue-600">with AI Precision</span>
        </h1>

        <p className="max-w-2xl mx-auto text-lg text-gray-500 leading-relaxed">
          Run automated investigations across court records, property filings, business
          registrations, employment, and social media — then receive a structured attorney-ready
          report in minutes.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/cases"
            className="inline-flex items-center justify-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-lg text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Open Cases Dashboard
            <span className="text-gray-400">→</span>
          </Link>
          <Link
            href="/cases/new"
            className="inline-flex items-center justify-center gap-2 border border-gray-300 text-gray-700 px-6 py-3 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            + New Investigation
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">How it works</h2>
          <div className="flex-1 h-px bg-gray-200" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { step: "1", title: "Create a Case", desc: "Enter the judgment debtor's name, jurisdiction, and any known identifiers." },
            { step: "2", title: "Run Investigation", desc: "The AI agent searches dozens of public sources automatically — takes 2–5 minutes." },
            { step: "3", title: "Review the Report", desc: "Get a structured report with assets, court history, risk flags, and sources consulted." },
          ].map(({ step, title, desc }) => (
            <div key={step} className="bg-white border rounded-xl p-5 flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-900 text-white text-sm font-bold flex items-center justify-center">
                {step}
              </div>
              <div>
                <p className="font-semibold text-gray-800 mb-1">{title}</p>
                <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Data Sources</h2>
          <div className="flex-1 h-px bg-gray-200" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(({ icon, title, desc }) => (
            <div key={title} className="bg-white border rounded-xl p-5 hover:shadow-sm transition-shadow">
              <div className="text-2xl mb-3">{icon}</div>
              <p className="font-semibold text-gray-800 mb-1">{title}</p>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Jurisdictions */}
      <section className="bg-white border rounded-xl p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-800 mb-1">Multi-Jurisdiction Support</h3>
            <p className="text-sm text-gray-500">
              Investigate subjects in the United States, Pakistan, or both simultaneously. The agent
              automatically selects the right tools for each jurisdiction.
            </p>
          </div>
          <div className="flex gap-3 flex-shrink-0">
            <div className="flex items-center gap-2 border rounded-lg px-4 py-2 text-sm">
              <span className="text-lg">🇺🇸</span>
              <span className="font-medium text-gray-700">United States</span>
            </div>
            <div className="flex items-center gap-2 border rounded-lg px-4 py-2 text-sm">
              <span className="text-lg">🇵🇰</span>
              <span className="font-medium text-gray-700">Pakistan</span>
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <p className="text-center text-xs text-gray-400">
        All data sources are lawful public records and publicly visible web data.
        No private or restricted databases are accessed.
      </p>
    </div>
  );
}
