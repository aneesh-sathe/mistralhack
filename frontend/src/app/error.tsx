"use client";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <section className="mx-auto max-w-3xl">
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6">
        <h1 className="text-2xl font-black text-rose-900">Something went wrong</h1>
        <p className="mt-2 text-sm text-rose-800">{error.message || "Unexpected error"}</p>
        <button
          type="button"
          onClick={reset}
          className="mt-4 inline-flex rounded-full border border-rose-300 bg-white px-4 py-2 text-sm font-semibold text-rose-700 transition hover:border-rose-500"
        >
          Try again
        </button>
      </div>
    </section>
  );
}
