"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/documents", label: "Lessons" },
  { href: "/contact", label: "Contact" },
];

export default function Navbar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <header className="border-b border-slate-200/80 bg-white/88 px-4 py-4 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1110px] items-center justify-between gap-4">
        <Link href="/" className="text-[34px] font-black tracking-tight text-slate-900 md:text-[36px]">
          LearnStral
        </Link>

        <nav className="flex items-center gap-6 md:gap-9">
          {NAV_ITEMS.map((item) => (
            <Link
              key={`${item.label}-${item.href}`}
              href={item.href}
              className={`text-[15px] font-semibold transition ${
                isActive(item.href)
                  ? "text-slate-900 underline decoration-brand-500 underline-offset-[10px]"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
