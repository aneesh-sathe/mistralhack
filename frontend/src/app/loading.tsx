export default function GlobalLoading() {
  return (
    <section className="space-y-4">
      <div className="soft-section animate-pulse p-6">
        <div className="h-8 w-2/5 rounded bg-slate-200" />
        <div className="mt-3 h-4 w-3/5 rounded bg-slate-100" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div key={idx} className="card animate-pulse p-4">
            <div className="h-5 w-3/4 rounded bg-slate-200" />
            <div className="mt-3 h-4 w-full rounded bg-slate-100" />
            <div className="mt-2 h-4 w-5/6 rounded bg-slate-100" />
            <div className="mt-5 h-8 w-28 rounded-full bg-slate-200" />
          </div>
        ))}
      </div>
    </section>
  );
}
