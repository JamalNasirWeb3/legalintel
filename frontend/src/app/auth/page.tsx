"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function AuthPage() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      if (mode === "signin") {
        await signIn(email, password);
        // AuthGuard redirects to /cases automatically
      } else {
        await signUp(email, password);
        setInfo(
          "Account created! Check your email to confirm your address, then sign in."
        );
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white text-lg font-bold mb-3">
            LI
          </div>
          <h1 className="text-xl font-bold text-gray-900">Legal Intelligence</h1>
          <p className="text-sm text-gray-500 mt-1">AI-powered debtor investigation</p>
        </div>

        <div className="bg-white border rounded-2xl p-8 shadow-sm">
          {/* Tab toggle */}
          <div className="flex rounded-lg border border-gray-200 p-1 mb-6 gap-1">
            {(["signin", "signup"] as const).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(""); setInfo(""); }}
                className={`flex-1 text-sm font-medium py-1.5 rounded-md transition-colors ${
                  mode === m
                    ? "bg-blue-600 text-white"
                    : "text-gray-500 hover:text-gray-800"
                }`}
              >
                {m === "signin" ? "Sign in" : "Create account"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="attorney@lawfirm.com"
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "signup" ? "At least 6 characters" : "••••••••"}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">
                {error}
              </p>
            )}
            {info && (
              <p className="text-sm text-green-700 bg-green-50 border border-green-200 px-3 py-2 rounded-lg">
                {info}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-medium text-sm py-2.5 rounded-lg transition-colors"
            >
              {loading
                ? "Please wait…"
                : mode === "signin"
                ? "Sign in"
                : "Create account"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          All data is encrypted and stored securely.
        </p>
      </div>
    </div>
  );
}
