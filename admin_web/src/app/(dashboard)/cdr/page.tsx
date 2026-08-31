"use client";

import { useEffect, useState } from "react";
import { cdrApi } from "@/lib/api";
import type { CDR, CDRFiltres } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { CDRFiltersForm } from "@/components/cdr/CDRFilters";
import { CDRTable } from "@/components/cdr/CDRTable";
import { ExportButton } from "@/components/cdr/ExportButton";

export default function CDRPage() {
  const [filtres, setFiltres] = useState<CDRFiltres>({});
  const [cdrs, setCdrs] = useState<CDR[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    function charger() {
      setChargement(true);
      cdrApi
        .lister(filtres)
        .then(setCdrs)
        .finally(() => setChargement(false));
    }
    charger();
  }, [filtres]);

  return (
    <div>
      <PageHeader
        title="Journal d'appels"
        subtitle="Historique des CDR avec filtres combinables"
        action={<ExportButton filtres={filtres} />}
      />

      <Card>
        <CDRFiltersForm filtres={filtres} onChange={setFiltres} />
        {chargement ? (
          <p className="py-12 text-center text-sm text-ink-muted">Chargement...</p>
        ) : (
          <CDRTable cdrs={cdrs} />
        )}
      </Card>
    </div>
  );
}
