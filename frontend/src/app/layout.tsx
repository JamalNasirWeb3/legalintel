import type { Metadata } from "next";
import Link from "next/link";
import { AuthProvider } from "@/context/AuthContext";
import AuthGuard from "@/components/AuthGuard";
import NavBar from "@/components/NavBar";
import OnboardingModal from "@/components/OnboardingModal";
import "./globals.css";

export const metadata: Metadata = {
  title: "Legal Intelligence System",
  description: "AI-powered judgment debtor investigation tool",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <AuthProvider>
          <AuthGuard>
            <NavBar />
            <OnboardingModal />
            <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
          </AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
