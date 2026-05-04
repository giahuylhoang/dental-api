const ITEMS = [
  { title: "Clinical Precision", body: "Every workflow is treated like a procedure — predictable, audited, and reviewable. We measure twice, save once." },
  { title: "Sovereign Ownership", body: "Your patient data, your schedule, your reports — all live in your tenancy. We export, we never lock in." },
  { title: "One Connected System", body: "Schedule, chart, lab, billing, insurance — one engine. No double-entry. No drift. No lost recalls." },
];

export function Philosophy() {
  return (
    <section className="bg-sidebar py-24 px-12 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-5">
        <div className="absolute top-1/5 -left-5 w-3/5 h-3/5 border border-white rotate-8" />
      </div>
      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid grid-cols-2 gap-20 items-center">
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-primary mb-6">Our Philosophy</div>
            <blockquote className="m-0 pl-7 border-l-4 border-primary">
              <p className="font-display font-bold italic text-3xl leading-snug text-sidebar-foreground">
                &ldquo;Open the chart. The history is already there.&rdquo;
              </p>
            </blockquote>
            <p className="text-base leading-loose text-sidebar-foreground/55 mt-7 max-w-md">
              Clinical operations are too important to be held together by spreadsheets and email. Every screen in Rockyridge Dental AI assumes the operator is mid-shift, the patient is in the chair, and the answer needs to be one click away.
            </p>
          </div>
          <div className="flex flex-col">
            {ITEMS.map((item, i) => (
              <div key={item.title} className={`flex gap-5 items-start py-7 ${i < 2 ? "border-b border-white/10" : ""}`}>
                <span className="font-display font-black text-2xl leading-none tracking-tight text-primary/25 shrink-0 w-8">
                  0{i + 1}
                </span>
                <div>
                  <div className="font-display font-bold text-lg text-sidebar-foreground mb-2">{item.title}</div>
                  <div className="text-sm leading-relaxed text-sidebar-foreground/55">{item.body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
