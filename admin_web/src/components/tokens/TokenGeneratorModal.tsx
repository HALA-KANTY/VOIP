"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Field, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { tokensApi } from "@/lib/api";

export function TokenGeneratorModal({
  open,
  onClose,
  onGenere,
}: {
  open: boolean;
  onClose: () => void;
  onGenere: () => void;
}) {
  const [montant, setMontant] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);
  const [dernierCode, setDernierCode] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setErreur(null);
    setChargement(true);
    try {
      const token = await tokensApi.generer(montant);
      setDernierCode(token.code);
      setMontant("");
      onGenere();
    } catch {
      setErreur("Erreur lors de la generation");
    } finally {
      setChargement(false);
    }
  }

  function fermer() {
    setDernierCode(null);
    onClose();
  }

  return (
    <Modal open={open} onClose={fermer} title="Generer un token">
      {dernierCode ? (
        <div>
          <p className="mb-1 text-sm text-ink-secondary">Token genere :</p>
          <p className="mb-4 rounded-lg bg-surface-2 px-4 py-3 text-center font-mono text-lg tracking-wider text-accent">
            {dernierCode}
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDernierCode(null)}>
              Generer un autre
            </Button>
            <Button onClick={fermer}>Fermer</Button>
          </div>
        </div>
      ) : (
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
            <Button type="button" variant="secondary" onClick={fermer}>
              Annuler
            </Button>
            <Button type="submit" disabled={chargement}>
              {chargement ? "Generation..." : "Generer"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
