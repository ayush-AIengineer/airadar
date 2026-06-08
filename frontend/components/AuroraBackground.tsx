export function AuroraBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-20 overflow-hidden">
      <div className="absolute -top-1/3 left-1/4 h-[60vmax] w-[60vmax] -translate-x-1/2 rounded-full bg-brand-600/20 blur-[120px] animate-aurora-shift" />
      <div
        className="absolute top-1/4 right-0 h-[50vmax] w-[50vmax] rounded-full bg-brand-500/16 blur-[120px] animate-aurora-shift"
        style={{ animationDelay: "-6s" }}
      />
      <div
        className="absolute bottom-0 left-1/3 h-[45vmax] w-[45vmax] rounded-full bg-brand-400/12 blur-[120px] animate-aurora-shift"
        style={{ animationDelay: "-12s" }}
      />
    </div>
  );
}
