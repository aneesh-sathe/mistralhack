"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { backendAuthLoginUrl } from "@/lib/api";
import { fetchSession } from "@/lib/auth";

export default function LoginPage() {
  const [devBypass, setDevBypass] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    fetchSession().then((session) => {
      if (!session) return;
      setDevBypass(session.dev_auth_bypass);
      setIsLoggedIn(true);
    });
  }, []);

  return (
    <section className="mx-auto max-w-4xl">
      <div className="soft-section grid gap-5 p-6 md:grid-cols-[1fr_0.9fr] md:p-8">
        <div>
          <p className="mb-3 inline-flex rounded-full border border-slate-300 bg-white/80 px-3 py-1 text-xs font-bold uppercase tracking-[0.11em] text-slate-700">
            Secure Access
          </p>
          <h1 className="text-4xl font-black leading-tight text-slate-900">Welcome back to LearnStral</h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-700">
            Sign in to upload documents, generate narrated lessons, and chat with module content.
          </p>
          <a
            href={backendAuthLoginUrl()}
            className="mt-6 inline-flex rounded-xl bg-brand-500 px-5 py-3 text-sm font-bold text-white shadow-[0_10px_22px_rgba(53,83,222,0.28)] transition hover:bg-brand-700"
          >
            Login with Google
          </a>
          {isLoggedIn ? (
            <div className="mt-4">
              <Link className="text-sm font-semibold text-brand-700 underline underline-offset-4" href="/documents">
                Continue to dashboard
              </Link>
            </div>
          ) : null}
        </div>

        <div className="card flex flex-col justify-between p-5">
          <h2 className="text-lg font-black text-slate-900">Environment Status</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            <p>OAuth callback: <span className="font-semibold">/api/auth/google/callback</span></p>
            <p>Session storage: <span className="font-semibold">HttpOnly JWT cookie</span></p>
            <p>Mode: <span className="font-semibold">{devBypass ? "DEV_AUTH_BYPASS=true" : "Google OAuth"}</span></p>
          </div>
          {devBypass ? (
            <p className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
              Dev mode is active. You can use the app without Google OAuth.
            </p>
          ) : (
            <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Configure Google credentials in `.env` to enable real OAuth login.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
