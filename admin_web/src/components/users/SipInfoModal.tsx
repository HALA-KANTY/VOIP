"use client";

import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { utilisateursApi } from "@/lib/api";
import type { Utilisateur } from "@/lib/types";

export function SipInfoModal({
  utilisateur,
  onClose,
  onChange,
}: {
  utilisateur: Utilisateur | null;
  onClose: () => void;
  onChange: () => void;
}) {
  const [chargement, setChargement] = useState(false);
  const [secretRegenere, setSecretRegenere] = useState<string | null>(null);
  const secretAffiche = secretRegenere ?? utilisateur?.sip_secret ?? null;

  async function regenerer() {
    if (!utilisateur) return;
    setChargement(true);
    try {
      const mis_a_jour = await utilisateursApi.regenererSecretSip(utilisateur.id);
      setSecretRegenere(mis_a_jour.sip_secret);
      onChange();
    } finally {
      setChargement(false);
    }
  }

  function fermer() {
    setSecretRegenere(null);
    onClose();
  }

  return (
    <Modal open={utilisateur !== null} onClose={fermer} title={`Identifiants SIP — ${utilisateur?.username ?? ""}`}>
      {!utilisateur?.sip_id ? (
        <p className="text-sm text-ink-secondary">Cet utilisateur n&apos;a pas de sip_id.</p>
      ) : (
        <>
          <p className="mb-3 text-sm text-ink-secondary">A configurer dans Linphone :</p>
          <div className="mb-4 space-y-2 rounded-lg bg-surface-2 px-4 py-3 font-mono text-sm">
            <p>
              <span className="text-ink-muted">Nom d&apos;utilisateur : </span>
              <span className="text-accent">{utilisateur.sip_id}</span>
            </p>
            <p>
              <span className="text-ink-muted">Mot de passe : </span>
              <span className="text-accent">{secretAffiche}</span>
            </p>
          </div>
          <p className="mb-4 text-xs text-ink-muted">
            Régénérer invalide immédiatement l&apos;ancien secret : Linphone devra être
            reconfiguré avec le nouveau.
          </p>
        </>
      )}
      <div className="flex justify-end gap-2">
        {utilisateur?.sip_id && (
          <Button variant="secondary" onClick={regenerer} disabled={chargement}>
            {chargement ? "..." : "Régénérer"}
          </Button>
        )}
        <Button onClick={fermer}>Fermer</Button>
      </div>
    </Modal>
  );
}
