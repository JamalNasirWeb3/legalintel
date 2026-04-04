"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCases, deleteCase } from "@/lib/api";
import type { Case } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  open: "bg-blue-50 text-blue-700 border-blue-200",
  active: "bg-amber-50 text-amber-700 border-amber-200",
  closed: "bg-gray-100 text-gray-500 border-gray-200",
};

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    getCases()
      .then(setCases)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(e: React.MouseEvent, c: Case) {
    e.preventDefault();
    if (!confirm(`Delete case "${c.title}"? This cannot be undone.`)) return;
    setDeletingId(c.id);
    try {
      await deleteCase(c.id);
      setCases((prev) => prev.filter((x) => x.id !== c.id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cases</h1>
          {!loading && cases.length > 0 && (
            <p className="text-sm text-gray-500 mt-0.5">{cases.length} case{cases.length !== 1 ? "s" : ""}</p>
          )}
        </div>
        <Link
          href="/cases/new"
          className="bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-700 text-sm font-medium transition-colors"
        >
          + New Case
        </Link>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white border rounded-xl px-5 py-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/4" />
            </div>
          ))}
        </div>
      )}

      {!loading && cases.length === 0 && !error && (
        <div className="text-center py-20 bg-white border rounded-xl">
          <div className="text-4xl mb-4">⚖️</div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">No cases yet</h2>
          <p className="text-sm text-gray-400 mb-6">Create your first case to start an investigation.</p>
          <Link
            href="/cases/new"
            className="inline-flex items-center gap-2 bg-gray-900 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            + Create First Case
          </Link>
        </div>
      )}

      <div className="space-y-3">
        {cases.map((c) => (
          <div
            key={c.id}
            className="relative group bg-white border rounded-xl px-5 py-4 hover:shadow-sm transition-shadow"
          >
            <Link href={`/cases/${c.id}`} className="block">
              <div className="flex items-start justify-between pr-24">
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900 truncate">{c.title}</p>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    {c.client_name && (
                      <span className="text-xs text-gray-500">Client: {c.client_name}</span>
                    )}
                    {c.attorney_name && (
                      <span className="text-xs text-gray-500">Attorney: {c.attorney_name}</span>
                    )}
                    {c.judgment_amount && (
                      <span className="text-xs text-gray-500">
                        ${Number(c.judgment_amount).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full border capitalize flex-shrink-0 ${STATUS_STYLES[c.status] ?? STATUS_STYLES.open}`}
                >
                  {c.status}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Created {new Date(c.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}
              </p>
            </Link>

            {/* Action buttons revealed on hover */}
            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Link
                href={`/cases/${c.id}`}
                onClick={(e) => e.stopPropagation()}
                className="text-xs text-gray-600 hover:text-gray-900 border rounded-md px-3 py-1.5 bg-white hover:bg-gray-50 transition-colors"
              >
                Open
              </Link>
              <button
                onClick={(e) => handleDelete(e, c)}
                disabled={deletingId === c.id}
                className="text-xs text-red-500 hover:text-red-700 border border-red-200 rounded-md px-3 py-1.5 bg-white hover:bg-red-50 disabled:opacity-40 transition-colors"
              >
                {deletingId === c.id ? "..." : "Delete"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
