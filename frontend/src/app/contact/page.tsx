export default function ContactPage() {
  return (
    <section className="mx-auto max-w-3xl space-y-4 text-center">
      <div className="soft-section px-6 py-10 md:px-10">
        <h1 className="text-3xl font-black text-slate-900 md:text-4xl">Contact</h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-slate-600 md:text-base">
          Built by{" "}
          <a
            href="https://www.github.com/aneesh-sathe/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-brand-500 underline underline-offset-2 hover:text-brand-700"
          >
            Aneesh Sathe
          </a>{" "}
          at Mistral Hack 2026 🔥
        </p>
      </div>
    </section>
  );
}
