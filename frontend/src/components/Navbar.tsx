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
    <header className="border-b border-slate-100 bg-white px-6 py-5">
      <div className="mx-auto grid w-full max-w-[1110px] grid-cols-[1fr_auto_1fr] items-center gap-2">
        <Link href="/" className="text-2xl font-black tracking-tight text-slate-900">
          LearnStral
        </Link>

        <nav className="flex items-center justify-center gap-7">
          {NAV_ITEMS.map((item) => (
            <Link
              key={`${item.label}-${item.href}`}
              href={item.href}
              className={`text-[14px] font-semibold transition ${
                isActive(item.href) ? "text-slate-900" : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div aria-hidden className="w-[84px] justify-self-end" />
      </div>
    </header>
  );
}
