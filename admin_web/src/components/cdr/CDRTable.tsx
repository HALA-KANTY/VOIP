import type { CDR } from "@/lib/types";
import { Badge, statutCDRTone } from "@/components/ui/Badge";
import { formatMontant, formatDate, formatDuree } from "@/lib/format";

const LABELS_STATUT: Record<string, string> = {
  termine: "Terminé",
  echoue: "Échoué",
  coupe: "Coupé (appelant)",
  occupe: "Occupé",
  sans_reponse: "Sans réponse",
  hors_ligne: "Hors ligne",
};

export function CDRTable({ cdrs }: { cdrs: CDR[] }) {
  if (cdrs.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Aucun appel ne correspond a ces filtres.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs text-ink-muted">
            <th className="pb-3 pr-4 font-medium">Date</th>
            <th className="pb-3 pr-4 font-medium">Utilisateur</th>
            <th className="pb-3 pr-4 font-medium">Destination</th>
            <th className="pb-3 pr-4 font-medium">Duree</th>
            <th className="pb-3 pr-4 font-medium">Cout</th>
            <th className="pb-3 pr-4 font-medium">Statut</th>
            <th className="pb-3 pr-4 font-medium">Connexion</th>
          </tr>
        </thead>
        <tbody>
          {cdrs.map((c) => (
            <tr key={c.id} className="border-b border-border last:border-0 hover:bg-surface-2/50">
              <td className="py-3 pr-4 text-ink-secondary">{formatDate(c.date_appel)}</td>
              <td className="py-3 pr-4">
                {c.utilisateur_nom} <span className="text-ink-muted">#{c.utilisateur_id}</span>
              </td>
              <td className="py-3 pr-4">{c.destination}</td>
              <td className="py-3 pr-4 tabular-nums">{formatDuree(c.duree)}</td>
              <td className="py-3 pr-4 tabular-nums">{formatMontant(c.cout)}</td>
              <td className="py-3 pr-4">
                <Badge tone={statutCDRTone(c.statut)}>{LABELS_STATUT[c.statut] ?? c.statut}</Badge>
              </td>
              <td className="py-3 pr-4 text-ink-secondary">{c.type_connexion}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
