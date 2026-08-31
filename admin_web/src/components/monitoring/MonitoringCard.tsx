"use client";

import { useEffect, useState } from "react";
import { monitoringApi } from "@/lib/api";
import type { ResumeMonitoring } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";

export function MonitoringCard() {
  const [donnees, setDonnees] = useState<ResumeMonitoring | null>(null);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    function charger() {
      monitoringApi
        .resume()
        .then(setDonnees)
        .finally(() => setChargement(false));
    }
    charger();
    const interval = setInterval(charger, 5000);
    return () => clearInterval(interval);
  }, []);

  if (chargement && !donnees) {
    return (
      <Card>
        <p className="py-8 text-center text-sm text-ink-muted">Chargement...</p>
      </Card>
    );
  }

  const statusColor = donnees?.ami_connecte 
    ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" 
    : "bg-rose-500/10 text-rose-500 border border-rose-500/20";

  return (
    <div className="mt-6 space-y-4 w-full">
      <div className="grid grid-cols-3 gap-4 w-full items-stretch">
        
        <KpiCard
          icon={<span>🔌</span>}
          label="AMI"
          value={
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}`}>
              {donnees?.ami_connecte ? "Connecté" : "Déconnecté"}
            </span>
          }
          hint="Asterisk Manager Interface"
        />

        <KpiCard
          icon={<span>👥</span>}
          label="Utilisateurs actifs"
          value={
            <span className="font-bold text-lg text-ink-primary">
              {`${donnees?.utilisateurs_actifs ?? 0} / ${donnees?.total_utilisateurs ?? 0}`}
            </span>
          }
          hint="Total des utilisateurs"
        />

        <KpiCard
          icon={<span>📞</span>}
          label="Appels en cours"
          value={
            <span className="font-bold text-lg text-ink-primary">
              {`${donnees?.appels_en_cours ?? 0}`}
            </span>
          }
          hint="Conversations actives"
        />
      </div>

      {donnees?.appels_en_cours ? (
        <Card className="mt-4">
          <h3 className="mb-4 text-sm font-medium text-ink-secondary">Appels en cours</h3>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="border-b border-surface-3 text-left text-xs text-ink-muted">
                  <th className="px-4 py-3 font-medium">Canal</th>
                  <th className="px-4 py-3 font-medium">Utilisateur</th>
                  <th className="px-4 py-3 font-medium">Durée (s)</th>
                  <th className="px-4 py-3 font-medium">Solde initial</th>
                </tr>
              </thead>
              <tbody>
                {donnees.details_appels.map((appel) => (
                  <tr key={appel.channel} className="border-b border-surface-3 last:border-0 hover:bg-surface-2/50">
                    <td className="px-4 py-3 font-mono text-xs text-ink-primary">{appel.channel}</td>
                    <td className="px-4 py-3 text-sm text-ink-primary">
                      {appel.utilisateur_nom} <span className="text-ink-muted">#{appel.utilisateur_id}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-ink-primary">{appel.secondes_ecoulees}</td>
                    <td className="px-4 py-3 text-sm text-ink-primary">{appel.solde_initial} AR</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card className="mt-4">
          <p className="py-8 text-center text-sm text-ink-muted">
            Aucun appel en cours.
          </p>
        </Card>
      )}
    </div>
  );
}
