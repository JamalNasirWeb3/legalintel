"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getCase, getSubjects, getReports, runInvestigation, getJobStatus, updateCase, deleteCase, updateSubject } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import type { Case, Subject, SubjectUpdate, Report, InvestigationJob } from "@/types";

const STATUS_LABEL: Record<string, string> = {
  pending: "Queued",
  running: "Running investigation...",
  complete: "Complete",
  failed: "Failed",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "text-yellow-600",
  running: "text-blue-600",
  complete: "text-green-600",
  failed: "text-red-600",
};

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [subject, setSubject] = useState<Subject | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [job, setJob] = useState<InvestigationJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Case edit state
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Case>>({});
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Subject edit state
  const [editingSubject, setEditingSubject] = useState(false);
  const [subjectForm, setSubjectForm] = useState<SubjectUpdate>({});
  const [savingSubject, setSavingSubject] = useState(false);
  const [subjectError, setSubjectError] = useState("");

  // Photo upload state
  const photoInputRef = useRef<HTMLInputElement>(null);
  const [photoUploading, setPhotoUploading] = useState(false);
  const [photoError, setPhotoError] = useState("");

  const loadData = useCallback(async () => {
    try {
      const [c, subs, reps] = await Promise.all([
        getCase(id),
        getSubjects(id),
        getReports(id),
      ]);
      setCaseData(c);
      setSubject(subs[0] || null);
      setReports(reps);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll job status while running — keep polling through transient connection errors
  useEffect(() => {
    if (!job || job.status === "complete" || job.status === "failed") return;

    let consecutiveErrors = 0;

    const interval = setInterval(async () => {
      try {
        const updated = await getJobStatus(job.id);
        consecutiveErrors = 0;
        setJob(updated);
        if (updated.status === "complete" || updated.status === "failed") {
          clearInterval(interval);
          if (updated.status === "complete") loadData();
        }
      } catch {
        consecutiveErrors += 1;
        // Only stop after 10 consecutive failures (~30s of no response)
        if (consecutiveErrors >= 10) clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [job, loadData]);

  function startEditSubject() {
    if (!subject) return;
    setSubjectForm({
      full_name: subject.full_name,
      country: subject.country ?? "US",
      aliases: subject.aliases ?? [],
      date_of_birth: subject.date_of_birth ?? "",
      address_street: subject.address_street ?? "",
      address_city: subject.address_city ?? "",
      address_state: subject.address_state ?? "",
      address_zip: subject.address_zip ?? "",
      known_spouses: subject.known_spouses ?? [],
      known_employers: subject.known_employers ?? [],
      known_businesses: subject.known_businesses ?? [],
    });
    setEditingSubject(true);
  }

  async function handleSaveSubject() {
    if (!subject) return;
    setSavingSubject(true);
    setSubjectError("");
    try {
      // Strip empty strings so Pydantic receives undefined rather than ""
      const payload = Object.fromEntries(
        Object.entries(subjectForm).filter(([, v]) =>
          v !== "" && !(Array.isArray(v) && v.length === 0)
        )
      ) as SubjectUpdate;
      console.log("[SubjectSave] payload →", JSON.stringify(payload));
      const updated = await updateSubject(subject.id, payload);
      console.log("[SubjectSave] response →", JSON.stringify(updated));
      setSubject(updated);
      setEditingSubject(false);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to save subject";
      console.error("[SubjectSave] error →", msg);
      setSubjectError(msg);
    } finally {
      setSavingSubject(false);
    }
  }

  async function handlePhotoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !subject) return;
    setPhotoError("");
    setPhotoUploading(true);
    const { data: { session } } = await supabase.auth.getSession();
    const userId = session?.user?.id;
    if (!userId) { setPhotoError("Not signed in."); setPhotoUploading(false); return; }
    const ext = file.name.split(".").pop()?.toLowerCase() || "jpg";
    const path = `${userId}/${subject.id}.${ext}`;
    const { error: upErr } = await supabase.storage.from("subject-photos")
      .upload(path, file, { upsert: true, contentType: file.type });
    if (upErr) { setPhotoError(upErr.message); setPhotoUploading(false); return; }
    const { data } = supabase.storage.from("subject-photos").getPublicUrl(path);
    const url = `${data.publicUrl}?t=${Date.now()}`;
    const updated = await updateSubject(subject.id, { photo_url: url });
    setSubject(updated);
    setPhotoUploading(false);
  }

  async function handleRunInvestigation() {
    if (!subject) return;
    try {
      const newJob = await runInvestigation(id, subject.id);
      setJob(newJob);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start investigation");
    }
  }

  function startEdit() {
    if (!caseData) return;
    setEditForm({
      title: caseData.title,
      attorney_name: caseData.attorney_name ?? "",
      client_name: caseData.client_name ?? "",
      judgment_amount: caseData.judgment_amount,
      notes: caseData.notes ?? "",
      status: caseData.status,
    });
    setEditing(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateCase(id, editForm);
      setCaseData(updated);
      setEditing(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete case "${caseData?.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await deleteCase(id);
      router.push("/cases");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete");
      setDeleting(false);
    }
  }

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!caseData) return <p>Case not found.</p>;

  const canRun = subject && (!job || job.status === "failed" || job.status === "complete");

  return (
    <div className="space-y-6">
      <div>
        <a href="/cases" className="text-sm text-gray-500 hover:underline">Cases</a>
        <span className="text-gray-400 mx-2">/</span>
        <span className="text-sm">{caseData.title}</span>
      </div>

      {/* Case header */}
      <div className="bg-white border rounded-lg p-5">
        {editing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Title *</label>
                <input
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={editForm.title ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Attorney</label>
                <input
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={editForm.attorney_name ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, attorney_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Client</label>
                <input
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={editForm.client_name ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, client_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Judgment Amount ($)</label>
                <input
                  type="number"
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={editForm.judgment_amount ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, judgment_amount: e.target.value ? Number(e.target.value) : undefined })}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Status</label>
                <select
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={editForm.status ?? "open"}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value as Case["status"] })}
                >
                  <option value="open">Open</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Notes</label>
                <textarea
                  className="w-full border rounded px-3 py-2 text-sm"
                  rows={3}
                  value={editForm.notes ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving || !editForm.title}
                className="bg-gray-900 text-white px-4 py-2 rounded text-sm hover:bg-gray-700 disabled:opacity-40"
              >
                {saving ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="border px-4 py-2 rounded text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold">{caseData.title}</h1>
              {caseData.client_name && <p className="text-sm text-gray-500 mt-1">Client: {caseData.client_name}</p>}
              {caseData.attorney_name && <p className="text-sm text-gray-500">Attorney: {caseData.attorney_name}</p>}
              {caseData.judgment_amount && (
                <p className="text-sm text-gray-500">
                  Judgment: ${Number(caseData.judgment_amount).toLocaleString()}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full capitalize">
                {caseData.status}
              </span>
              <button
                onClick={startEdit}
                className="text-sm text-gray-500 hover:text-gray-900 border rounded px-3 py-1 hover:bg-gray-50"
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-sm text-red-500 hover:text-red-700 border border-red-200 rounded px-3 py-1 hover:bg-red-50 disabled:opacity-40"
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        )}
        {!editing && caseData.notes && (
          <p className="text-sm text-gray-600 mt-3 border-t pt-3">{caseData.notes}</p>
        )}
      </div>

      {/* Subject */}
      {subject ? (
        <div className="bg-white border rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-700">Subject (Judgment Debtor)</h2>
            {!editingSubject && (
              <button
                onClick={startEditSubject}
                className="text-sm text-gray-500 hover:text-gray-900 border rounded px-3 py-1 hover:bg-gray-50"
              >
                Edit
              </button>
            )}
          </div>

          {/* Photo upload */}
          {!editingSubject && (
            <div className="flex items-start gap-4 mb-4 pb-4 border-b">
              {/* Preview / click target */}
              <div
                onClick={() => !photoUploading && photoInputRef.current?.click()}
                className="w-20 h-20 rounded-lg border-2 border-dashed border-gray-300 hover:border-blue-400 flex flex-col items-center justify-center cursor-pointer overflow-hidden flex-shrink-0 bg-gray-50"
              >
                {subject.photo_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={subject.photo_url} alt="Subject" className="w-full h-full object-cover" />
                ) : photoUploading ? (
                  <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span className="text-xs text-gray-400 mt-1">Photo</span>
                  </>
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700 mb-1">Debtor photo</p>
                {subject.photo_url ? (
                  <p className="text-xs text-green-700 mb-2">Photo uploaded — vision analysis enabled</p>
                ) : (
                  <p className="text-xs text-gray-400 mb-2">Upload a photo to enable AI visual analysis and improve the confidence score.</p>
                )}
                <button
                  type="button"
                  disabled={photoUploading}
                  onClick={() => photoInputRef.current?.click()}
                  className="text-xs border rounded px-3 py-1.5 hover:bg-gray-50 disabled:opacity-50"
                >
                  {photoUploading ? "Uploading…" : subject.photo_url ? "Change photo" : "Upload photo"}
                </button>
                {photoError && <p className="text-xs text-red-600 mt-1">{photoError}</p>}
              </div>
              <input ref={photoInputRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoUpload} />
            </div>
          )}

          {editingSubject ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Full Legal Name *</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.full_name ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, full_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Country / Jurisdiction</label>
                  <select
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.country ?? "US"}
                    onChange={(e) => setSubjectForm({ ...subjectForm, country: e.target.value as Subject["country"] })}
                  >
                    <option value="US">United States</option>
                    <option value="PK">Pakistan</option>
                    <option value="BOTH">Both (US + Pakistan)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Date of Birth</label>
                  <input
                    type="date"
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.date_of_birth ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, date_of_birth: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">City</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.address_city ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, address_city: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">State / Province</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.address_state ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, address_state: e.target.value })}
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Street Address</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.address_street ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, address_street: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">ZIP / Postal Code</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.address_zip ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, address_zip: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Aliases (comma-separated)</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.aliases?.join(", ") ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, aliases: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Known Spouses (comma-separated)</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.known_spouses?.join(", ") ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, known_spouses: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Known Employers (comma-separated)</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.known_employers?.join(", ") ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, known_employers: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Known Businesses (comma-separated)</label>
                  <input
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={subjectForm.known_businesses?.join(", ") ?? ""}
                    onChange={(e) => setSubjectForm({ ...subjectForm, known_businesses: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
                  />
                </div>
              </div>
              {subjectError && <p className="text-red-600 text-sm">{subjectError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleSaveSubject}
                  disabled={savingSubject || !subjectForm.full_name}
                  className="bg-gray-900 text-white px-4 py-2 rounded text-sm hover:bg-gray-700 disabled:opacity-40"
                >
                  {savingSubject ? "Saving..." : "Save"}
                </button>
                <button
                  onClick={() => { setEditingSubject(false); setSubjectError(""); }}
                  className="border px-4 py-2 rounded text-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Info label="Full Name" value={subject.full_name} />
              <Info label="Jurisdiction" value={{ US: "United States", PK: "Pakistan", BOTH: "US + Pakistan" }[subject.country] ?? subject.country} />
              {subject.date_of_birth && <Info label="Date of Birth" value={subject.date_of_birth} />}
              {subject.address_state && (
                <Info
                  label="Last Known Location"
                  value={[subject.address_city, subject.address_state].filter(Boolean).join(", ")}
                />
              )}
              {subject.aliases?.length && <Info label="Aliases" value={subject.aliases.join(", ")} />}
              {subject.known_spouses?.length && <Info label="Known Spouses" value={subject.known_spouses.join(", ")} />}
              {subject.known_employers?.length && <Info label="Known Employers" value={subject.known_employers.join(", ")} />}
              {subject.known_businesses?.length && <Info label="Known Businesses" value={subject.known_businesses.join(", ")} />}
            </div>
          )}
        </div>
      ) : (
        <p className="text-gray-500 text-sm">No subject on file.</p>
      )}

      {/* Investigation */}
      <div className="bg-white border rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-700">Investigation</h2>
          <button
            onClick={handleRunInvestigation}
            disabled={!canRun}
            className="bg-gray-900 text-white px-4 py-2 rounded text-sm hover:bg-gray-700 disabled:opacity-40"
          >
            Run Investigation
          </button>
        </div>

        {job && (
          <div className={`text-sm font-medium ${STATUS_COLOR[job.status]}`}>
            {STATUS_LABEL[job.status]}
            {job.status === "failed" && job.error_message && (
              <p className="text-red-500 font-normal mt-1">{job.error_message}</p>
            )}
          </div>
        )}

        {!job && !reports.length && (
          <p className="text-sm text-gray-400">No investigation run yet.</p>
        )}
      </div>

      {/* Reports */}
      {reports.length > 0 && (
        <div className="bg-white border rounded-lg p-5">
          <h2 className="font-semibold text-gray-700 mb-3">Reports</h2>
          <div className="space-y-2">
            {reports.map((r) => (
              <Link
                key={r.id}
                href={`/cases/${id}/report/${r.id}`}
                className="flex items-center justify-between border rounded px-4 py-3 hover:shadow-sm transition-shadow"
              >
                <div>
                  <p className="text-sm font-medium">Investigation Report</p>
                  <p className="text-xs text-gray-400">{new Date(r.created_at).toLocaleString()}</p>
                </div>
                {r.confidence_score !== undefined && (
                  <span className="text-xs text-gray-500">
                    Confidence: {Math.round(r.confidence_score * 100)}%
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-gray-400 text-xs">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}

