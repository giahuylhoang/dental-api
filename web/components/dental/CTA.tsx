export interface CTAProps {
  onNav?: (anchor: string) => void;
}

export function CTA({ onNav }: CTAProps) {
  return (
    <section id="contact" className="bg-muted border-t border-border py-24 px-12">
      <div className="max-w-6xl mx-auto grid grid-cols-2 gap-20 items-center">
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-primary mb-4">
            Begin the Engagement
          </div>
          <h2 className="font-display font-bold text-4xl tracking-tight text-foreground mb-5">
            Schedule a 30-minute demo
          </h2>
          <p className="text-base leading-relaxed text-muted-foreground max-w-md">
            Walk one of your real workflows on Rockyridge Dental AI. We&apos;ll set up a sandbox with your typical schedule and run through schedule, chart, and lab side-by-side.
          </p>
          <div className="flex gap-4 mt-8">
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-semibold text-foreground">No obligation</span>
              <span className="text-xs text-muted-foreground">Operations review, not a sales call</span>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-md p-9 shadow-lg">
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3.5">
              {[["Full Name", "Dr Hau Le"], ["Clinic", "Oak Dental Calgary"]].map(([lbl, ph]) => (
                <div key={lbl} className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">{lbl}</label>
                  <input readOnly placeholder={ph} className="bg-muted border border-border rounded-md px-3 py-2 text-sm text-foreground outline-none" />
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-foreground">Practice size</label>
              <select className="bg-muted border border-border rounded-md px-3 py-2 text-sm text-foreground outline-none">
                <option>1 location · 1–3 chairs</option>
                <option>1 location · 4–8 chairs</option>
                <option>2–3 locations</option>
                <option>4+ locations / DSO</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-foreground">What&apos;s the operations gap?</label>
              <textarea rows={3} readOnly placeholder="Where is the schedule / chart / lab leaking time?" className="bg-muted border border-border rounded-md px-3 py-2 text-sm text-foreground outline-none resize-y" />
            </div>
            <button
              onClick={() => onNav?.("contact")}
              className="mt-1 bg-primary text-primary-foreground rounded-md px-4 py-2.5 text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Request a demo
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
