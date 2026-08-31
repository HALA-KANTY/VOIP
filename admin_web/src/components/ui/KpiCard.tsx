import type { ReactNode } from "react";

export function KpiCard({
  icon,
  label,
  value,
  hint,
}: {
  icon: ReactNode;
  label: string;
  value: ReactNode; 
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-soft text-accent">
          {icon}
        </span>
        <span className="text-sm text-ink-secondary">{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <div className="text-2xl font-semibold tabular-nums text-ink-primary flex items-center">
          {value}
        </div>
      </div>
      {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
    </div>
  );
}
