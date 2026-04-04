"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createCase, createSubject } from "@/lib/api";

export default function NewCasePage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    const get = (k: string) => (fd.get(k) as string)?.trim() || undefined;

    try {
      const newCase = await createCase({
        title: fd.get("title") as string,
        attorney_name: get("attorney_name"),
        client_name: get("client_name"),
        judgment_amount: get("judgment_amount") ? Number(get("judgment_amount")) : undefined,
        notes: get("notes"),
      });

      await createSubject({
        case_id: newCase.id,
        full_name: fd.get("subject_name") as string,
        date_of_birth: get("date_of_birth"),
        address_street: get("address_street"),
        address_city: get("address_city"),
        address_state: get("address_state"),
        address_zip: get("address_zip"),
        aliases: get("aliases") ? get("aliases")!.split(",").map((s) => s.trim()) : undefined,
        known_spouses: get("known_spouses") ? get("known_spouses")!.split(",").map((s) => s.trim()) : undefined,
        country: ((fd.get("country") as string) || "US") as "US" | "PK" | "BOTH",
        known_employers: get("known_employers") ? get("known_employers")!.split(",").map((s) => s.trim()) : undefined,
        known_businesses: get("known_businesses") ? get("known_businesses")!.split(",").map((s) => s.trim()) : undefined,
      });

      router.push(`/cases/${newCase.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create case");
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <a href="/cases" className="text-sm text-gray-500 hover:underline">Cases</a>
        <span className="text-gray-400 mx-2">/</span>
        <span className="text-sm">New Case</span>
      </div>

      <h1 className="text-2xl font-bold mb-6">New Case</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Case info */}
        <section className="bg-white border rounded-lg p-5 space-y-4">
          <h2 className="font-semibold text-gray-700">Case Information</h2>

          <Field label="Case Title *" name="title" required placeholder="e.g. Smith v. Jones #2024-001" />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Attorney Name" name="attorney_name" placeholder="Your name" />
            <Field label="Client Name" name="client_name" placeholder="Judgment creditor" />
          </div>
          <Field
            label="Judgment Amount ($)"
            name="judgment_amount"
            type="number"
            placeholder="0.00"
          />
          <Field label="Notes" name="notes" as="textarea" placeholder="Case context, court, docket number..." />
        </section>

        {/* Subject info */}
        <section className="bg-white border rounded-lg p-5 space-y-4">
          <h2 className="font-semibold text-gray-700">Judgment Debtor (Subject)</h2>

          <Field label="Full Legal Name *" name="subject_name" required placeholder="First Last" />
          <Field label="Aliases / Other Names" name="aliases" placeholder="Maiden name, DBA, nicknames (comma-separated)" />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Date of Birth" name="date_of_birth" type="date" />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Country *</label>
              <select name="country" defaultValue="US" className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400">
                <option value="US">United States</option>
                <option value="PK">Pakistan</option>
                <option value="BOTH">Both (US + Pakistan)</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="City" name="address_city" placeholder="e.g. Karachi / Denver" />
            <Field label="State / Province" name="address_state" placeholder="e.g. Sindh / CO" />
          </div>
          <Field label="Street Address" name="address_street" placeholder="Street address" />
          <Field label="ZIP / Postal Code" name="address_zip" placeholder="e.g. 75600 / 80201" />
          <Field label="Known Spouses / Partners" name="known_spouses" placeholder="Comma-separated names" />
          <Field label="Known Employers" name="known_employers" placeholder="Comma-separated" />
          <Field label="Known Businesses" name="known_businesses" placeholder="Comma-separated" />
        </section>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="bg-gray-900 text-white px-6 py-2 rounded hover:bg-gray-700 disabled:opacity-50"
          >
            {saving ? "Creating..." : "Create Case"}
          </button>
          <a href="/cases" className="px-6 py-2 border rounded hover:bg-gray-50 text-sm">
            Cancel
          </a>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  name,
  required,
  placeholder,
  type = "text",
  as,
  maxLength,
}: {
  label: string;
  name: string;
  required?: boolean;
  placeholder?: string;
  type?: string;
  as?: "textarea";
  maxLength?: number;
}) {
  const cls = "w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400";
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {as === "textarea" ? (
        <textarea name={name} placeholder={placeholder} className={`${cls} h-20`} />
      ) : (
        <input
          type={type}
          name={name}
          required={required}
          placeholder={placeholder}
          maxLength={maxLength}
          className={cls}
        />
      )}
    </div>
  );
}
