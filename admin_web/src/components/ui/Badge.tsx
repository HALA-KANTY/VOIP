type Tone = "good" | "warning" | "serious" | "critical" | "neutral";

const TONE_CLASSES: Record<Tone, string> = {
  good: "bg-good-soft text-good",
  warning: "bg-warning-soft text-warning",
  serious: "bg-serious-soft text-serious",
  critical: "bg-critical-soft text-critical",
  neutral: "bg-surface-2 text-ink-secondary",
};

export function Badge({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}

export function statutUtilisateurTone(statut: string): Tone {
  if (statut === "actif") return "good";
  if (statut === "suspendu") return "critical";
  return "neutral";
}

export function statutCDRTone(statut: string): Tone {
  if (statut === "termine") return "good";
  if (statut === "echoue") return "critical";
  if (statut === "coupe") return "warning";
  if (statut === "occupe") return "warning";
  if (statut === "sans_reponse") return "serious";
  if (statut === "hors_ligne") return "serious";
  return "neutral";
}

export function statutTokenTone(statut: string): Tone {
  return statut === "utilise" ? "neutral" : "good";
}
