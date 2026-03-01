import Link from "next/link";

export default function HomePage() {
  return (
    <section className="mx-auto max-w-4xl space-y-6 text-center">
      <div className="soft-section px-6 py-10 md:px-10 md:py-14">
        <p className="mx-auto inline-flex rounded-full border border-slate-300 bg-white/85 px-3 py-1 text-xs font-bold uppercase tracking-[0.11em] text-slate-700">
          LearnStral Platform
        </p>
        <h1 className="mt-4 text-4xl font-black leading-tight text-slate-900 md:text-5xl">
          Turn PDFs Into Narrated Visual Lessons
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-slate-700 md:text-base">
          Upload any subject PDF, extract modules, generate animations with voiceover, and chat with the lesson content.
        </p>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/documents"
            className="rounded-xl bg-brand-500 px-5 py-3 text-sm font-bold text-white shadow-[0_10px_22px_rgba(53,83,222,0.28)] transition hover:bg-brand-700"
          >
            View Lessons
          </Link>
          <Link
            href="/contact"
            className="rounded-xl border border-slate-400 bg-white px-5 py-3 text-sm font-bold text-slate-700 transition hover:border-slate-700"
          >
            Contact
          </Link>
        </div>
      </div>
    </section>
  );
}
