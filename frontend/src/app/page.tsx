import Link from "next/link";

export default function HomePage() {
  return (
    <section className="mx-auto max-w-6xl">
      <div className="grid gap-8 md:grid-cols-[1.05fr_1fr] md:items-center">
        <div className="hero-illustration">
          <span className="hero-star s1">✦</span>
          <span className="hero-star s2">✦</span>
          <span className="hero-star s3">✦</span>

          <div className="hero-badge badge-a">AI First</div>
          <div className="hero-badge badge-b">Learning</div>
          <div className="hero-badge badge-c">Platform</div>
        </div>

        <div className="space-y-5">
          <h1 className="text-5xl font-black leading-[1.05] text-slate-900 md:text-6xl">
            LearnStral empowers you to learn anything you've ever wanted.
          </h1>
          <p className="max-w-lg text-base leading-relaxed text-slate-600">
            Upload any PDF, generate clear lessons with narration and captions, and ask questions to understand faster.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/documents"
              className="rounded-full bg-brand-500 px-6 py-3 text-sm font-bold text-white shadow-[0_10px_22px_rgba(95,67,255,0.28)] transition hover:bg-brand-700"
            >
              View Lessons
            </Link>
            <Link
              href="/contact"
              className="rounded-full border border-slate-300 bg-white px-6 py-3 text-sm font-bold text-slate-700 transition hover:border-slate-700"
            >
              Contact
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
