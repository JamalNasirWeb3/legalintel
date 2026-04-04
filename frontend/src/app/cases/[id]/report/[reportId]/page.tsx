"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getReport, emailReport } from "@/lib/api";
import { getStoredProfile } from "@/components/OnboardingModal";
import type { Report } from "@/types";

export default function ReportPage() {
  const { id, reportId } = useParams<{ id: string; reportId: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Email modal state
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailAddress, setEmailAddress] = useState("");
  const [emailSending, setEmailSending] = useState(false);
  const [emailResult, setEmailResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getReport(reportId)
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [reportId]);

  // Pre-fill email from onboarding profile
  useEffect(() => {
    const profile = getStoredProfile();
    if (profile?.email) setEmailAddress(profile.email);
  }, []);

  useEffect(() => {
    if (emailModalOpen) setTimeout(() => emailInputRef.current?.focus(), 50);
  }, [emailModalOpen]);

  async function handleSendEmail() {
    if (!report) return;
    if (!emailAddress.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailAddress)) {
      setEmailResult({ ok: false, msg: "Enter a valid email address." });
      return;
    }
    setEmailSending(true);
    setEmailResult(null);
    try {
      const res = await emailReport(reportId, emailAddress.trim(), "Investigation Subject");
      setEmailResult({ ok: true, msg: res.message });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setEmailResult({ ok: false, msg });
    } finally {
      setEmailSending(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border rounded-xl p-5 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-3" />
            <div className="h-3 bg-gray-100 rounded w-full mb-2" />
            <div className="h-3 bg-gray-100 rounded w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
        {error}
      </div>
    );
  }

  if (!report) return <p className="text-gray-400">Report not found.</p>;

  const confidence = report.confidence_score !== undefined
    ? Math.round(report.confidence_score * 100)
    : null;

  const confidenceColor =
    confidence === null ? "text-gray-400"
    : confidence >= 70 ? "text-green-600"
    : confidence >= 40 ? "text-amber-600"
    : "text-red-600";

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-sm text-gray-400">
        <Link href="/cases" className="hover:text-gray-700 transition-colors">Cases</Link>
        <span>/</span>
        <Link href={`/cases/${id}`} className="hover:text-gray-700 transition-colors">Case</Link>
        <span>/</span>
        <span className="text-gray-600">Report</span>
      </div>

      {/* Header */}
      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Investigation Report</h1>
            <p className="text-sm text-gray-400 mt-1">
              Generated {new Date(report.created_at).toLocaleString(undefined, {
                year: "numeric", month: "short", day: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
            </p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            {confidence !== null && (
              <div className="text-right">
                <p className={`text-2xl font-bold ${confidenceColor}`}>{confidence}%</p>
                <p className="text-xs text-gray-400">confidence</p>
              </div>
            )}
            <button
              onClick={() => { setEmailResult(null); setEmailModalOpen(true); }}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Email PDF
            </button>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      {report.executive_summary && (
        <Section title="Executive Summary" icon="📋">
          <p className="text-gray-700 leading-relaxed">{report.executive_summary}</p>
        </Section>
      )}

      {/* Risk Flags */}
      {report.risk_flags && report.risk_flags.length > 0 && (
        <Section title="Risk Flags" icon="🚩">
          <ul className="space-y-2">
            {report.risk_flags.map((flag, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-red-100 text-red-600 text-xs font-bold flex items-center justify-center mt-0.5">!</span>
                <span className="text-gray-700">{flag}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Asset Summary */}
      {report.asset_summary && (
        <Section title="Asset Summary" icon="💰">
          <p className="text-gray-700 leading-relaxed">{report.asset_summary}</p>
        </Section>
      )}

      {/* Full Report */}
      <Section title="Full Report" icon="📄">
        {report.full_report_md ? (
          <div className="prose prose-sm max-w-none text-gray-700">
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed bg-gray-50 rounded-lg p-4 overflow-auto">
              {report.full_report_md}
            </pre>
          </div>
        ) : (
          <p className="text-gray-400 text-sm">No full report available.</p>
        )}
      </Section>

      {/* Sources */}
      {report.sources_consulted && report.sources_consulted.length > 0 && (
        <Section title="Sources Consulted" icon="🔍">
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {report.sources_consulted.map((src, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                <span className="w-4 h-4 rounded-full bg-gray-100 text-gray-400 text-xs flex items-center justify-center flex-shrink-0">
                  {i + 1}
                </span>
                {src}
              </li>
            ))}
          </ul>
        </Section>
      )}

      <div className="pt-2">
        <Link href={`/cases/${id}`} className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
          ← Back to case
        </Link>
      </div>

      {/* Email Modal */}
      {emailModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Email Report as PDF</h3>
              <button
                onClick={() => setEmailModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              A PDF copy of this report will be sent as an email attachment.
            </p>

            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recipient email address
            </label>
            <input
              ref={emailInputRef}
              type="email"
              value={emailAddress}
              onChange={(e) => { setEmailAddress(e.target.value); setEmailResult(null); }}
              onKeyDown={(e) => e.key === "Enter" && handleSendEmail()}
              placeholder="attorney@lawfirm.com"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
            />

            {emailResult && (
              <div className={`text-sm px-3 py-2 rounded-lg mb-4 ${
                emailResult.ok
                  ? "bg-green-50 text-green-700 border border-green-200"
                  : "bg-red-50 text-red-700 border border-red-200"
              }`}>
                {emailResult.msg}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setEmailModalOpen(false)}
                className="flex-1 border border-gray-300 text-gray-700 text-sm font-medium py-2.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSendEmail}
                disabled={emailSending}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
              >
                {emailSending ? "Sending…" : "Send PDF"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border rounded-xl p-5">
      <h2 className="flex items-center gap-2 font-semibold text-gray-800 mb-4">
        <span>{icon}</span>
        {title}
      </h2>
      {children}
    </div>
  );
}
