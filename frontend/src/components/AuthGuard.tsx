"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const PUBLIC_PATHS = ["/auth"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    if (!user && !PUBLIC_PATHS.includes(pathname)) {
      router.replace("/auth");
    }
    if (user && PUBLIC_PATHS.includes(pathname)) {
      router.replace("/cases");
    }
  }, [user, loading, pathname, router]);

  // Show a full-page loader while session is being resolved
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-400">Loading…</p>
        </div>
      </div>
    );
  }

  // On the /auth page show it always; elsewhere only show if authenticated
  if (!user && !PUBLIC_PATHS.includes(pathname)) return null;

  return <>{children}</>;
}
