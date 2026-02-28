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
    <section className="mx-auto max-w-xl">
      <div className="card p-8">
        <h1 className="font-display text-3xl font-bold text-slate-900">Login</h1>
        <p className="mt-2 text-sm text-slate-600">Use Google OAuth, or run with DEV_AUTH_BYPASS=true for local iteration.</p>

        <a
          href={backendAuthLoginUrl()}
          className="mt-6 inline-block rounded-md bg-brand-500 px-5 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Login with Google
        </a>

        {devBypass ? (
          <p className="mt-4 rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-700">Dev mode enabled on backend.</p>
        ) : null}

        {isLoggedIn ? (
          <Link className="mt-4 inline-block text-sm font-medium text-brand-700" href="/documents">
            Continue to documents
          </Link>
        ) : null}
      </div>
    </section>
  );
}
