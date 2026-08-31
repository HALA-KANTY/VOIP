"use client";

import type { Utilisateur } from "@/lib/types";
import { Badge, statutUtilisateurTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatMontant } from "@/lib/format";

// Dictionnaire de style pour colorer dynamiquement le type d'utilisateur
const STYLES_TYPES_UTILISATEUR: Record<string, { label: string; classe: string }> = {
  normal: { 
    label: "Normal", 
    classe: "bg-slate-500/10 text-slate-400 border border-slate-500/20" 
  },
  commercial: { 
    label: "Commercial", 
    classe: "bg-amber-500/10 text-amber-400 border border-amber-500/20" 
  },
  support: { 
    label: "Support Tech", 
    classe: "bg-sky-500/10 text-sky-400 border border-sky-500/20" 
  },
  comptabilite: { 
    label: "Comptabilité", 
    classe: "bg-purple-500/10 text-purple-400 border border-purple-500/20" 
  },
};

export function UserTable({
  utilisateurs,
  onCrediter,
  onDebiter,
  onSupprimer,
  onVoirSip,
  onModifier,
  onBasculerStatut,
}: {
  utilisateurs: Utilisateur[];
  onCrediter: (u: Utilisateur) => void;
  onDebiter: (u: Utilisateur) => void;
  onSupprimer: (u: Utilisateur) => void;
  onVoirSip: (u: Utilisateur) => void;
  onModifier: (u: Utilisateur) => void;
  onBasculerStatut: (u: Utilisateur) => void;
}) {
  if (utilisateurs.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Aucun utilisateur pour le moment.</p>;
  }

  return (
    <div className="overflow-x-auto w-full">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs text-ink-muted uppercase tracking-wider">
            <th className="pb-3 pr-4 font-medium">Utilisateur</th>
            <th className="pb-3 pr-4 font-medium">SIP ID</th>
            {/* 🔴 AJOUT DE LA COLONNE DANS L'ENTÊTE DE TABLE */}
            <th className="pb-3 pr-4 font-medium">Type</th>
            <th className="pb-3 pr-4 font-medium">Solde</th>
            <th className="pb-3 pr-4 font-medium">Statut</th>
            <th className="pb-3 pr-4 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {utilisateurs.map((u) => {
            // Extraction sécurisée du style de badge associé au type (fallback 'normal')
            const configType = STYLES_TYPES_UTILISATEUR[u.type_utilisateur] || STYLES_TYPES_UTILISATEUR.normal;

            return (
              <tr key={u.id} className="border-b border-border last:border-0 hover:bg-surface-2/50 transition-colors">
                {/* Cellule Identifiants de l'utilisateur */}
                <td className="py-3 pr-4">
                  <p className="font-medium text-ink-primary">{u.nom_complet}</p>
                  <p className="text-xs text-ink-muted">@{u.username}</p>
                </td>
                
                {/* Cellule Extension SIP */}
                <td className="py-3 pr-4 text-ink-secondary font-mono">{u.sip_id ?? "—"}</td>
                
                {/* 🔴 CELLULE CORE : Badge graphique du type d'utilisateur */}
                <td className="py-3 pr-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${configType.classe}`}>
                    {configType.label}
                  </span>
                </td>
                
                {/* Cellule Solde monétaire */}
                <td className="py-3 pr-4 tabular-nums font-medium text-ink-primary">{formatMontant(u.solde)}</td>
                
                {/* Cellule Badge statut (Actif/Inactif) */}
                <td className="py-3 pr-4">
                  <Badge tone={statutUtilisateurTone(u.statut)}>{u.statut}</Badge>
                </td>
                
                {/* Cellule Actions administratives */}
                <td className="py-3 pr-4">
                  <div className="flex justify-end gap-2">
                    <Button variant="secondary" className="px-3 py-1.5 text-xs" onClick={() => onModifier(u)}>
                      Modifier
                    </Button>
                    {u.sip_id && (
                      <Button variant="secondary" className="px-3 py-1.5 text-xs" onClick={() => onVoirSip(u)}>
                        SIP
                      </Button>
                    )}
                    <Button variant="secondary" className="px-3 py-1.5 text-xs" onClick={() => onCrediter(u)}>
                      Crediter
                    </Button>
                    <Button variant="secondary" className="px-3 py-1.5 text-xs" onClick={() => onDebiter(u)}>
                      Debiter
                    </Button>
                    <Button
                      variant="secondary"
                      className="px-3 py-1.5 text-xs"
                      onClick={() => onBasculerStatut(u)}
                    >
                      {u.statut === "suspendu" ? "Reactiver" : "Suspendre"}
                    </Button>
                    <Button variant="danger" className="px-3 py-1.5 text-xs" onClick={() => onSupprimer(u)}>
                      Supprimer
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
