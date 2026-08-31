"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { tarifsApi } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";

export default function TarifsPage() {
  const [tarifActif, setTarifActif] = useState<string | null>(null);
  const [nouveauTarif, setNouveauTarif] = useState("");
  const [chargement, setChargement] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const recharger = useCallback(() => {
    tarifsApi
      .obtenirActif()
      .then((data) => setTarifActif(data.montant_par_seconde))
      .catch(() => setMessage("❌ Impossible de récupérer le tarif actuel."));
  }, []);

  useEffect(() => {
    function chargerInitial() {
      recharger();
    }
    chargerInitial();
  }, [recharger]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setChargement(true);
    setMessage(null);

    try {
      await tarifsApi.changer(nouveauTarif);
      setNouveauTarif("");
      recharger();
      setMessage("✅ Le tarif a été mis à jour à chaud sur Asterisk !");
    } catch {
      setMessage("❌ Erreur lors de la modification du tarif.");
    } finally {
      setChargement(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Tarification"
        subtitle="Modifiez le coût des communications en temps réel. Le changement s'applique instantanément aux appels en cours."
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card className="flex flex-col justify-center bg-surface-2/30">
          <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">Tarif actuel</span>
          <span className="mt-2 text-4xl font-extrabold text-accent">
            {tarifActif ?? "..."} AR <span className="text-lg font-normal text-ink-muted">/ seconde</span>
          </span>
        </Card>

        <Card>
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="Nouveau tarif (Ariary par seconde)">
              <Input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="Ex: 1.50"
                value={nouveauTarif}
                onChange={(e) => setNouveauTarif(e.target.value)}
                required
              />
            </Field>

            {message && <p className="text-sm font-medium text-ink-primary">{message}</p>}

            <div className="flex justify-end">
              <Button type="submit" variant="primary" disabled={chargement}>
                {chargement ? "Mise à jour..." : "Appliquer le tarif"}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
