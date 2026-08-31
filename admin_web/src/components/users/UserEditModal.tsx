"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Field, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { utilisateursApi } from "@/lib/api";
import type { StatutUtilisateur, Utilisateur } from "@/lib/types";

export function UserEditModal({
  utilisateur,
  onClose,
  onModifie,
}: {
  utilisateur: Utilisateur | null;
  onClose: () => void;
  onModifie: () => void;
}) {
  const [nomComplet, setNomComplet] = useState("");
  const [email, setEmail] = useState("");
  const [sipId, setSipId] = useState("");
  const [statut, setStatut] = useState<StatutUtilisateur>("actif");
  const [typeUtilisateur, setTypeUtilisateur] = useState<"normal" | "commercial" | "support" | "comptabilite">(
    "normal"
  );
  const [erreur, setErreur] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);

  useEffect(() => {
    function preremplir() {
      if (!utilisateur) return;
      setNomComplet(utilisateur.nom_complet);
      setEmail(utilisateur.email ?? "");
      setSipId(utilisateur.sip_id ?? "");
      setStatut(utilisateur.statut);
      setTypeUtilisateur(utilisateur.type_utilisateur);
      setErreur(null);
    }
    preremplir();
  }, [utilisateur]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!utilisateur) return;
    setErreur(null);
    setChargement(true);
    try {
      await utilisateursApi.modifier(utilisateur.id, {
        nom_complet: nomComplet,
        email: email || null,
        sip_id: sipId || null,
        statut,
        type_utilisateur: typeUtilisateur,
      });
      onModifie();
      onClose();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Erreur lors de la modification";
      setErreur(message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <Modal open={utilisateur !== null} onClose={onClose} title={`Modifier ${utilisateur?.username ?? ""}`}>
      <form onSubmit={onSubmit}>
        <Field label="Nom complet">
          <Input value={nomComplet} onChange={(e) => setNomComplet(e.target.value)} required />
        </Field>
        <Field label="Email">
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label="SIP ID">
          <Input value={sipId} onChange={(e) => setSipId(e.target.value)} placeholder="1001" maxLength={10} />
        </Field>
        <Field label="Type d'utilisateur">
          <select
            value={typeUtilisateur}
            onChange={(e) => setTypeUtilisateur(e.target.value as "normal" | "commercial" | "support" | "comptabilite")}
            className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 text-sm"
          >
            <option value="normal">Client normal (2xxx)</option>
            <option value="commercial">Agent commercial (3xxx)</option>
            <option value="support">Support technique (4xxx)</option>
            <option value="comptabilite">Comptabilité (5xxx)</option>
          </select>
        </Field>
        <Field label="Statut">
          <select
            value={statut}
            onChange={(e) => setStatut(e.target.value as StatutUtilisateur)}
            className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 text-sm"
          >
            <option value="actif">Actif</option>
            <option value="inactif">Inactif</option>
            <option value="suspendu">Suspendu</option>
          </select>
        </Field>

        {erreur && <p className="mb-3 text-sm text-critical">{erreur}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={chargement}>
            {chargement ? "Enregistrement..." : "Enregistrer"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
