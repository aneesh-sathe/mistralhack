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
    <section className="mx-auto max-w-5xl">
      <div className="grid gap-5 md:grid-cols-[1fr_0.9fr]">
        <div className="soft-section p-7">
          <h1 className="text-4xl font-black leading-tight text-slate-900">Welcome back to LearnStral</h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-600">
            Sign in to upload PDFs, generate lessons, and chat with your content.
          </p>
          <a
            href={backendAuthLoginUrl()}
            className="mt-6 inline-flex rounded-full bg-brand-500 px-6 py-3 text-sm font-bold text-white shadow-[0_10px_22px_rgba(95,67,255,0.28)] transition hover:bg-brand-700"
          >
            Log in with Google
          </a>
          {isLoggedIn ? (
            <div className="mt-4">
              <Link className="text-sm font-semibold text-brand-700 underline underline-offset-4" href="/documents">
                Continue to lessons
              </Link>
            </div>
          ) : null}
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-black text-slate-900">Environment Status</h2>
          <div className="mt-4 space-y-2 text-sm text-slate-600">
            <p>
              OAuth callback: <span className="font-semibold text-slate-800">/api/auth/google/callback</span>
            </p>
            <p>
              Session storage: <span className="font-semibold text-slate-800">HttpOnly JWT cookie</span>
            </p>
            <p>
              Mode: <span className="font-semibold text-slate-800">{devBypass ? "DEV_AUTH_BYPASS=true" : "Google OAuth"}</span>
            </p>
          </div>
          {devBypass ? (
            <p className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
              Dev mode is active. You can use the app without Google OAuth.
            </p>
          ) : (
            <p className="mt-5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Configure Google credentials in `.env` to enable real OAuth login.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
