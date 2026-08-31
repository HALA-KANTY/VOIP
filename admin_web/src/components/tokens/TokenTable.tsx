import type { Token } from "@/lib/types";
import { Badge, statutTokenTone } from "@/components/ui/Badge";
import { formatMontant, formatDate } from "@/lib/format";

export function TokenTable({
  tokens,
  onSupprimer,
}: {
  tokens: Token[];
  onSupprimer: (t: Token) => void;
}) {
  if (tokens.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Aucun token ne correspond a ce filtre.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs text-ink-muted">
            <th className="pb-3 pr-4 font-medium">Code</th>
            <th className="pb-3 pr-4 font-medium">Montant</th>
            <th className="pb-3 pr-4 font-medium">Statut</th>
            <th className="pb-3 pr-4 font-medium">Cree le</th>
            <th className="pb-3 pr-4 font-medium">Utilise le</th>
            <th className="pb-3 pr-4 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((t) => (
            <tr key={t.id} className="border-b border-border last:border-0 hover:bg-surface-2/50">
              <td className="py-3 pr-4 font-mono text-xs tracking-wide">{t.code}</td>
              <td className="py-3 pr-4 tabular-nums">{formatMontant(t.montant)}</td>
              <td className="py-3 pr-4">
                <Badge tone={statutTokenTone(t.statut)}>{t.statut.replace("_", " ")}</Badge>
              </td>
              <td className="py-3 pr-4 text-ink-secondary">{formatDate(t.date_creation)}</td>
              <td className="py-3 pr-4 text-ink-secondary">
                {t.date_utilisation ? formatDate(t.date_utilisation) : "—"}
              </td>
              <td className="py-3 pr-4 text-right">
                {t.statut === "non_utilise" && (
                  <button
                    onClick={() => onSupprimer(t)}
                    className="rounded-lg px-3 py-1 text-xs text-red-500 hover:bg-red-50"
                  >
                    Supprimer
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
