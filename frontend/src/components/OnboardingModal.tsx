"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "li_onboarding_complete";
const PROFILE_KEY = "li_user_profile";

export interface UserProfile {
  name: string;
  firm: string;
  email: string;
}

export function getStoredProfile(): UserProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const STEPS = [
  {
    id: "welcome",
    title: "Welcome to Legal Intelligence",
    subtitle: "AI-powered judgment debtor investigation",
  },
  {
    id: "profile",
    title: "Your Profile",
    subtitle: "We'll use this to personalise your reports.",
  },
  {
    id: "tour",
    title: "How It Works",
    subtitle: "Three steps to a complete investigation.",
  },
];

export default function OnboardingModal() {
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState<UserProfile>({ name: "", firm: "", email: "" });
  const [errors, setErrors] = useState<Partial<UserProfile>>({});

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  function validateProfile() {
    const e: Partial<UserProfile> = {};
    if (!profile.name.trim()) e.name = "Name is required";
    if (!profile.email.trim()) e.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email))
      e.email = "Enter a valid email address";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleNext() {
    if (STEPS[step].id === "profile" && !validateProfile()) return;
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      finish();
    }
  }

  function finish() {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
  }

  const current = STEPS[step];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Progress bar */}
        <div className="h-1 bg-gray-100">
          <div
            className="h-full bg-blue-600 transition-all duration-500"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        <div className="p-8">
          {/* Step indicator */}
          <div className="flex gap-1.5 mb-6">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full flex-1 transition-colors ${
                  i <= step ? "bg-blue-600" : "bg-gray-200"
                }`}
              />
            ))}
          </div>

          {/* Header */}
          <h2 className="text-2xl font-bold text-gray-900 mb-1">{current.title}</h2>
          <p className="text-sm text-gray-500 mb-8">{current.subtitle}</p>

          {/* Step content */}
          {current.id === "welcome" && <WelcomeStep />}
          {current.id === "profile" && (
            <ProfileStep profile={profile} setProfile={setProfile} errors={errors} />
          )}
          {current.id === "tour" && <TourStep />}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">
            <button
              onClick={finish}
              className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
            >
              Skip setup
            </button>
            <button
              onClick={handleNext}
              className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-6 py-2.5 rounded-lg transition-colors"
            >
              {step < STEPS.length - 1 ? "Continue" : "Get started"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function WelcomeStep() {
  return (
    <div className="space-y-4">
      <div className="w-14 h-14 rounded-xl bg-blue-600 flex items-center justify-center text-white text-2xl font-bold mb-6">
        LI
      </div>
      <div className="space-y-3 text-sm text-gray-600">
        <Feature icon="🔍" text="Searches court records, property filings, business registrations, and more" />
        <Feature icon="🤖" text="AI agent investigates using Claude — reads and reasons across sources" />
        <Feature icon="📄" text="Delivers a structured report you can email as a PDF to any address" />
        <Feature icon="🌐" text="Supports US and Pakistan jurisdictions" />
      </div>
    </div>
  );
}

function Feature({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="text-lg flex-shrink-0">{icon}</span>
      <span>{text}</span>
    </div>
  );
}

function ProfileStep({
  profile,
  setProfile,
  errors,
}: {
  profile: UserProfile;
  setProfile: (p: UserProfile) => void;
  errors: Partial<UserProfile>;
}) {
  return (
    <div className="space-y-4">
      <Field
        label="Your name *"
        placeholder="Jane Smith"
        value={profile.name}
        error={errors.name}
        onChange={(v) => setProfile({ ...profile, name: v })}
      />
      <Field
        label="Law firm / organisation"
        placeholder="Smith & Associates"
        value={profile.firm}
        onChange={(v) => setProfile({ ...profile, firm: v })}
      />
      <Field
        label="Email address *"
        type="email"
        placeholder="jane@smithlaw.com"
        value={profile.email}
        error={errors.email}
        onChange={(v) => setProfile({ ...profile, email: v })}
      />
      <p className="text-xs text-gray-400">
        Your email is stored locally in your browser and used to pre-fill the
        &quot;Send Report&quot; field.
      </p>
    </div>
  );
}

function Field({
  label,
  placeholder,
  value,
  type = "text",
  error,
  onChange,
}: {
  label: string;
  placeholder: string;
  value: string;
  type?: string;
  error?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
          error ? "border-red-400 bg-red-50" : "border-gray-300"
        }`}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

function TourStep() {
  const steps = [
    {
      n: "1",
      title: "Create a case",
      desc: 'Go to Cases → New Case. Fill in case details and the judgment debtor\'s information.',
    },
    {
      n: "2",
      title: "Run investigation",
      desc: "Open the case, click Run Investigation. The AI agent searches public records automatically.",
    },
    {
      n: "3",
      title: "Review & email the report",
      desc: "When complete, view the structured report and email the PDF to any address in one click.",
    },
  ];

  return (
    <div className="space-y-5">
      {steps.map(({ n, title, desc }) => (
        <div key={n} className="flex gap-4">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center flex-shrink-0">
            {n}
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-sm">{title}</p>
            <p className="text-sm text-gray-500 mt-0.5">{desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
