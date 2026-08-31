"use client";

import { useCallback, useEffect, useState } from "react";
import { tokensApi } from "@/lib/api";
import type { Token } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { IconPlus } from "@/components/ui/icons";
import { TokenTable } from "@/components/tokens/TokenTable";
import { TokenGeneratorModal } from "@/components/tokens/TokenGeneratorModal";
import { BulkTokenModal } from "@/components/tokens/BulkTokenModal";

type FiltreStatutToken = "tous" | "non_utilise" | "utilise";

export default function TokensPage() {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [chargement, setChargement] = useState(true);
  const [modalOuvert, setModalOuvert] = useState(false);
  const [bulkOuvert, setBulkOuvert] = useState(false);
  const [filtreStatut, setFiltreStatut] = useState<FiltreStatutToken>("tous");

  const recharger = useCallback(() => {
    setChargement(true);
    tokensApi
      .lister()
      .then(setTokens)
      .finally(() => setChargement(false));
  }, []);

  useEffect(() => {
    function chargerInitial() {
      recharger();
    }
    chargerInitial();
  }, [recharger]);

  const tokensAffiches = tokens.filter((t) => filtreStatut === "tous" || t.statut === filtreStatut);

  async function supprimer(t: Token) {
    if (!confirm(`Supprimer le token ${t.code} ?`)) return;
    await tokensApi.supprimer(t.id);
    recharger();
  }

  return (
    <div>
      <PageHeader
        title="Tokens"
        subtitle="Generation et suivi des tokens de rechargement"
        action={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setBulkOuvert(true)}>
              <IconPlus /> Générer un lot
            </Button>
            <Button onClick={() => setModalOuvert(true)}>
              <IconPlus /> Générer un token
            </Button>
          </div>
        }
      />

      <Card>
        <div className="mb-4 flex gap-2">
          {(
            [
              { valeur: "tous", label: "Tous" },
              { valeur: "non_utilise", label: "Non utilisés" },
              { valeur: "utilise", label: "Utilisés" },
            ] as const
          ).map((option) => (
            <button
              key={option.valeur}
              onClick={() => setFiltreStatut(option.valeur)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                filtreStatut === option.valeur
                  ? "bg-accent text-white"
                  : "bg-surface-2 text-ink-secondary hover:bg-surface-3"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        {chargement ? (
          <p className="py-12 text-center text-sm text-ink-muted">Chargement...</p>
        ) : (
          <TokenTable tokens={tokensAffiches} onSupprimer={supprimer} />
        )}
      </Card>

      <TokenGeneratorModal open={modalOuvert} onClose={() => setModalOuvert(false)} onGenere={recharger} />
      <BulkTokenModal open={bulkOuvert} onClose={() => setBulkOuvert(false)} onEffectue={recharger} />
    </div>
  );
}
