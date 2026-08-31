"use client";

import { useCallback, useEffect, useState } from "react";
import { utilisateursApi } from "@/lib/api";
import type { Utilisateur } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { IconPlus } from "@/components/ui/icons";
import { UserTable } from "@/components/users/UserTable";
import { UserFormModal } from "@/components/users/UserFormModal";
import { UserEditModal } from "@/components/users/UserEditModal";
import { CreditDebitModal } from "@/components/users/CreditDebitModal";
import { SipInfoModal } from "@/components/users/SipInfoModal";

export default function UtilisateursPage() {
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [chargement, setChargement] = useState(true);
  const [modalCreation, setModalCreation] = useState(false);
  const [operation, setOperation] = useState<{ utilisateur: Utilisateur; mode: "crediter" | "debiter" } | null>(
    null
  );
  const [utilisateurSip, setUtilisateurSip] = useState<Utilisateur | null>(null);
  const [utilisateurEdition, setUtilisateurEdition] = useState<Utilisateur | null>(null);

  const recharger = useCallback(() => {
    setChargement(true);
    utilisateursApi
      .lister()
      .then(setUtilisateurs)
      .finally(() => setChargement(false));
  }, []);

  useEffect(() => {
    function chargerInitial() {
      recharger();
    }
    chargerInitial();
  }, [recharger]);

  async function supprimer(u: Utilisateur) {
    if (!confirm(`Supprimer l'utilisateur ${u.username} ?`)) return;
    await utilisateursApi.supprimer(u.id);
    recharger();
  }

  async function basculerStatut(u: Utilisateur) {
    const nouveauStatut = u.statut === "suspendu" ? "actif" : "suspendu";
    if (!confirm(`${nouveauStatut === "suspendu" ? "Suspendre" : "Reactiver"} ${u.username} ?`)) return;
    await utilisateursApi.modifier(u.id, { statut: nouveauStatut });
    recharger();
  }

  return (
    <div>
      <PageHeader
        title="Utilisateurs"
        subtitle="Gestion des comptes et des soldes prepayes"
        action={
          <Button onClick={() => setModalCreation(true)}>
            <IconPlus /> Nouvel utilisateur
          </Button>
        }
      />

      <Card>
        {chargement ? (
          <p className="py-12 text-center text-sm text-ink-muted">Chargement...</p>
        ) : (
          <UserTable
            utilisateurs={utilisateurs}
            onCrediter={(u) => setOperation({ utilisateur: u, mode: "crediter" })}
            onDebiter={(u) => setOperation({ utilisateur: u, mode: "debiter" })}
            onSupprimer={supprimer}
            onVoirSip={setUtilisateurSip}
            onModifier={setUtilisateurEdition}
            onBasculerStatut={basculerStatut}
          />
        )}
      </Card>

      <UserFormModal open={modalCreation} onClose={() => setModalCreation(false)} onCree={recharger} />
      <CreditDebitModal
        utilisateur={operation?.utilisateur ?? null}
        mode={operation?.mode ?? "crediter"}
        onClose={() => setOperation(null)}
        onEffectue={recharger}
      />
      <SipInfoModal utilisateur={utilisateurSip} onClose={() => setUtilisateurSip(null)} onChange={recharger} />
      <UserEditModal
        utilisateur={utilisateurEdition}
        onClose={() => setUtilisateurEdition(null)}
        onModifie={recharger}
      />
    </div>
  );
}
