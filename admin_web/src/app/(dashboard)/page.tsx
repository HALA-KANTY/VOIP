"use client";

import { useEffect, useState } from "react";
import { statistiquesApi } from "@/lib/api";
import { formatMontant } from "@/lib/format";
import type { RevenuParPeriode, StatistiquesAppels, StatistiquesUtilisateurs, TopDestination } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import { RevenueChart } from "@/components/charts/RevenueChart";
import { DestinationsChart } from "@/components/charts/DestinationsChart";
import { IconCall, IconWallet, IconUsers, IconStats } from "@/components/ui/icons";
import { MonitoringCard } from "@/components/monitoring/MonitoringCard";

export default function DashboardPage() {
  const [appels, setAppels] = useState<StatistiquesAppels | null>(null);
  const [utilisateurs, setUtilisateurs] = useState<StatistiquesUtilisateurs | null>(null);
  const [revenus, setRevenus] = useState<RevenuParPeriode[]>([]);
  const [destinations, setDestinations] = useState<TopDestination[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    Promise.all([
      statistiquesApi.appels(),
      statistiquesApi.utilisateurs(),
      statistiquesApi.revenus(),
      statistiquesApi.destinations(5),
    ])
      .then(([a, u, r, d]) => {
        setAppels(a);
        setUtilisateurs(u);
        setRevenus(r);
        setDestinations(d);
      })
      .finally(() => setChargement(false));
  }, []);

  const revenuTotal = revenus.reduce((somme, r) => somme + Number(r.revenu), 0);

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Vue d'ensemble de la plateforme VoIP" />

      {chargement ? (
        <p className="text-sm text-ink-muted">Chargement...</p>
      ) : (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              icon={<IconCall />}
              label="Total appels"
              value={String(appels?.total_appels ?? 0)}
              hint={`${appels?.appels_termines ?? 0} termines`}
            />
            <KpiCard
              icon={<IconWallet />}
              label="Revenus"
              value={formatMontant(revenuTotal)}
              hint="Sur la periode affichee"
            />
            <KpiCard
              icon={<IconUsers />}
              label="Utilisateurs actifs"
              value={String(utilisateurs?.utilisateurs_actifs ?? 0)}
              hint={`${utilisateurs?.total_utilisateurs ?? 0} au total`}
            />
            <KpiCard
              icon={<IconStats />}
              label="Solde total"
              value={formatMontant(utilisateurs?.solde_total ?? "0")}
              hint="Cumule de tous les utilisateurs"
            />
          </div>

          <div className="mb-6">
            <MonitoringCard />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card title="Revenus par jour">
              <RevenueChart data={revenus} />
            </Card>
            <Card title="Top destinations">
              <DestinationsChart data={destinations} />
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
