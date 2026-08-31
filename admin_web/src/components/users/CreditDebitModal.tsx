"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Field, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { utilisateursApi } from "@/lib/api";
import type { Utilisateur } from "@/lib/types";

export function CreditDebitModal({
  utilisateur,
  mode,
  onClose,
  onEffectue,
}: {
  utilisateur: Utilisateur | null;
  mode: "crediter" | "debiter";
  onClose: () => void;
  onEffectue: () => void;
}) {
  const [montant, setMontant] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!utilisateur) return;
    setErreur(null);
    setChargement(true);
    try {
      if (mode === "crediter") {
        await utilisateursApi.crediter(utilisateur.id, montant);
      } else {
        await utilisateursApi.debiter(utilisateur.id, montant);
      }
      setMontant("");
      onEffectue();
      onClose();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Operation impossible";
      setErreur(message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <Modal
      open={utilisateur !== null}
      onClose={onClose}
      title={mode === "crediter" ? `Crediter ${utilisateur?.username ?? ""}` : `Debiter ${utilisateur?.username ?? ""}`}
    >
      <form onSubmit={onSubmit}>
        <Field label="Montant (AR)">
          <Input
            type="number"
            step="0.01"
            min="0.01"
            value={montant}
            onChange={(e) => setMontant(e.target.value)}
            required
            autoFocus
          />
        </Field>

        {erreur && <p className="mb-3 text-sm text-critical">{erreur}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" variant={mode === "debiter" ? "danger" : "primary"} disabled={chargement}>
            {chargement ? "..." : mode === "crediter" ? "Crediter" : "Debiter"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
