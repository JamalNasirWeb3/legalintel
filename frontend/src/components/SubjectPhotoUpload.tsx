"use client";

import { useRef, useState } from "react";
import { supabase } from "@/lib/supabase";

interface Props {
  subjectId: string;
  currentUrl?: string | null;
  onUpload: (url: string) => void;
}

const BUCKET = "subject-photos";
const MAX_SIZE_MB = 5;

export default function SubjectPhotoUpload({ subjectId, currentUrl, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<string | null>(currentUrl ?? null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large (max ${MAX_SIZE_MB} MB).`);
      return;
    }

    setError("");
    setUploading(true);

    // Show local preview immediately
    setPreview(URL.createObjectURL(file));

    // Get user ID from current session
    const { data: { session } } = await supabase.auth.getSession();
    const userId = session?.user?.id;
    if (!userId) {
      setError("Not signed in.");
      setUploading(false);
      return;
    }

    const ext = file.name.split(".").pop()?.toLowerCase() || "jpg";
    const path = `${userId}/${subjectId}.${ext}`;

    const { error: uploadErr } = await supabase.storage
      .from(BUCKET)
      .upload(path, file, { upsert: true, contentType: file.type });

    if (uploadErr) {
      setError(uploadErr.message);
      setPreview(currentUrl ?? null);
      setUploading(false);
      return;
    }

    const { data } = supabase.storage.from(BUCKET).getPublicUrl(path);
    const publicUrl = `${data.publicUrl}?t=${Date.now()}`;
    setPreview(publicUrl);
    onUpload(publicUrl);
    setUploading(false);
  }

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Clickable photo box */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => !uploading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !uploading && inputRef.current?.click()}
        className={[
          "relative w-24 h-24 rounded-xl border-2 flex items-center justify-center",
          "overflow-hidden cursor-pointer group select-none",
          preview
            ? "border-gray-200"
            : "border-dashed border-gray-300 hover:border-blue-400 bg-gray-50",
        ].join(" ")}
      >
        {preview ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="Subject" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <span className="text-white text-xs font-medium">Change</span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-1 text-gray-400 pointer-events-none">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span className="text-xs">Photo</span>
          </div>
        )}

        {/* Upload spinner overlay */}
        {uploading && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="text-xs text-blue-600 hover:text-blue-500 disabled:opacity-50 transition-colors"
      >
        {uploading ? "Uploading…" : preview ? "Change photo" : "Upload photo"}
      </button>

      {error && (
        <p className="text-xs text-red-600 text-center max-w-[140px]">{error}</p>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic"
        className="hidden"
        onChange={handleFile}
      />
    </div>
  );
}
