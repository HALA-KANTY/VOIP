"use client";

import type { CDRFiltres } from "@/lib/types";
import { Field, Input } from "@/components/ui/Field";

export function CDRFiltersForm({
  filtres,
  onChange,
}: {
  filtres: CDRFiltres;
  onChange: (filtres: CDRFiltres) => void;
}) {
  function set<K extends keyof CDRFiltres>(cle: K, valeur: CDRFiltres[K]) {
    onChange({ ...filtres, [cle]: valeur || undefined });
  }

  return (
    <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <Field label="Date debut">
        <Input type="date" onChange={(e) => set("date_debut", e.target.value)} />
      </Field>
      <Field label="Date fin">
        <Input type="date" onChange={(e) => set("date_fin", e.target.value)} />
      </Field>
      <Field label="Destination">
        <Input placeholder="0341234567" onChange={(e) => set("destination", e.target.value)} />
      </Field>
      <Field label="Duree min (s)">
        <Input type="number" min={0} onChange={(e) => set("duree_min", Number(e.target.value) || undefined)} />
      </Field>
      <Field label="Duree max (s)">
        <Input type="number" min={0} onChange={(e) => set("duree_max", Number(e.target.value) || undefined)} />
      </Field>
      <Field label="ID utilisateur">
        <Input type="number" min={1} onChange={(e) => set("utilisateur_id", Number(e.target.value) || undefined)} />
      </Field>
    </div>
  );
}
