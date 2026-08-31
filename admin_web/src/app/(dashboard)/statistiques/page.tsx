"use client";

import { useEffect, useState } from "react";
import { statistiquesApi } from "@/lib/api";
import { formatMontant, formatDuree } from "@/lib/format";
import type { RevenuParPeriode, StatistiquesAppels, TopDestination } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { RevenueChart } from "@/components/charts/RevenueChart";
import { DestinationsChart } from "@/components/charts/DestinationsChart";

export default function StatistiquesPage() {
  const [appels, setAppels] = useState<StatistiquesAppels | null>(null);
  const [revenus, setRevenus] = useState<RevenuParPeriode[]>([]);
  const [destinations, setDestinations] = useState<TopDestination[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    Promise.all([statistiquesApi.appels(), statistiquesApi.revenus(), statistiquesApi.destinations(10)])
      .then(([a, r, d]) => {
        setAppels(a);
        setRevenus(r);
        setDestinations(d);
      })
      .finally(() => setChargement(false));
  }, []);

  if (chargement) {
    return <p className="text-sm text-ink-muted">Chargement...</p>;
  }

  const repartition = [
    { label: "Termines", valeur: appels?.appels_termines ?? 0, tone: "text-good" },
    { label: "Echoues", valeur: appels?.appels_echoues ?? 0, tone: "text-critical" },
    { label: "Coupes", valeur: appels?.appels_coupes ?? 0, tone: "text-warning" },
  ];

  return (
    <div>
      <PageHeader title="Statistiques" subtitle="Analyse des appels, revenus et destinations" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Revenus par jour">
          <RevenueChart data={revenus} />
        </Card>
        <Card title="Top destinations">
          <DestinationsChart data={destinations} />
        </Card>

        <Card title="Repartition des appels">
          <div className="grid grid-cols-3 gap-4 text-center">
            {repartition.map((r) => (
              <div key={r.label}>
                <p className={`text-2xl font-semibold tabular-nums ${r.tone}`}>{r.valeur}</p>
                <p className="mt-1 text-xs text-ink-muted">{r.label}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 border-t border-border pt-4 text-sm text-ink-secondary">
            <div className="flex justify-between py-1">
              <span>Duree totale</span>
              <span className="tabular-nums text-ink">{formatDuree(appels?.duree_totale_secondes ?? 0)}</span>
            </div>
            <div className="flex justify-between py-1">
              <span>Duree moyenne</span>
              <span className="tabular-nums text-ink">
                {formatDuree(Math.round(appels?.duree_moyenne_secondes ?? 0))}
              </span>
            </div>
          </div>
        </Card>

        <Card title="Top destinations (detail)">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-ink-muted">
                  <th className="pb-2 pr-4 font-medium">Destination</th>
                  <th className="pb-2 pr-4 font-medium">Appels</th>
                  <th className="pb-2 pr-4 font-medium">Cout total</th>
                </tr>
              </thead>
              <tbody>
                {destinations.map((d) => (
                  <tr key={d.destination} className="border-b border-border last:border-0">
                    <td className="py-2 pr-4">{d.destination}</td>
                    <td className="py-2 pr-4 tabular-nums">{d.nombre_appels}</td>
                    <td className="py-2 pr-4 tabular-nums">{formatMontant(d.cout_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
