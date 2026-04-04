"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function NavBar() {
  const { user, signOut } = useAuth();
  const pathname = usePathname();

  // Don't show the nav on the auth page
  if (pathname === "/auth") return null;

  return (
    <header className="bg-gray-900 text-white border-b border-gray-800 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <div className="w-7 h-7 rounded bg-blue-600 flex items-center justify-center text-xs font-bold">
              LI
            </div>
            <span className="font-semibold text-sm tracking-tight">Legal Intelligence</span>
          </Link>
          <nav className="hidden sm:flex items-center gap-1">
            <Link
              href="/cases"
              className="text-sm text-gray-300 hover:text-white px-3 py-1.5 rounded hover:bg-gray-800 transition-colors"
            >
              Cases
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <span className="hidden sm:block text-xs text-gray-400 max-w-[180px] truncate">
              {user.email}
            </span>
          )}
          <Link
            href="/cases/new"
            className="text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded transition-colors font-medium"
          >
            + New Case
          </Link>
          {user && (
            <button
              onClick={() => signOut()}
              className="text-sm text-gray-400 hover:text-white px-3 py-1.5 rounded hover:bg-gray-800 transition-colors"
            >
              Sign out
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
