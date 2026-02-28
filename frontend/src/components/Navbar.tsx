"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchSession } from "@/lib/auth";
import { AuthMeResponse } from "@/lib/types";

export default function Navbar() {
  const [session, setSession] = useState<AuthMeResponse | null>(null);

  useEffect(() => {
    fetchSession().then(setSession);
  }, []);

  return (
    <nav className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/documents" className="font-display text-lg font-bold text-brand-700">
          Math Tutor
        </Link>
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <Link href="/documents" className="hover:text-slate-900">
            Documents
          </Link>
          <Link href="/login" className="hover:text-slate-900">
            Login
          </Link>
          {session?.user ? <span>{session.user.email}</span> : <span>Guest</span>}
        </div>
      </div>
    </nav>
  );
}
