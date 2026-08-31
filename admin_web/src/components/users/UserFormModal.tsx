"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Field, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { utilisateursApi } from "@/lib/api";
import type { Utilisateur } from "@/lib/types";

export function UserFormModal({
  open,
  onClose,
  onCree,
}: {
  open: boolean;
  onClose: () => void;
  onCree: () => void;
}) {
  const [username, setUsername] = useState("");
  const [nomComplet, setNomComplet] = useState("");
  const [email, setEmail] = useState("");
  const [sipId, setSipId] = useState("");
  const [password, setPassword] = useState("");
  const [typeUtilisateur, setTypeUtilisateur] = useState<"normal" | "commercial" | "support" | "comptabilite">("normal");
  const [erreur, setErreur] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);
  const [cree, setCree] = useState<Utilisateur | null>(null);

  function reinitialiser() {
    setUsername("");
    setNomComplet("");
    setEmail("");
    setSipId("");
    setPassword("");
    setTypeUtilisateur("normal");
    setErreur(null);
    setCree(null);
  }

  function fermer() {
    reinitialiser();
    onClose();
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setErreur(null);
    setChargement(true);
    try {
      const utilisateur = await utilisateursApi.creer({
        username,
        nom_complet: nomComplet,
        email: email || null,
        sip_id: sipId || null,
        password,
        type_utilisateur: typeUtilisateur,
      });
      onCree();
      if (utilisateur.sip_id) {
        // Le secret SIP genere n'est affiche qu'ici : on laisse l'admin le copier
        // avant de fermer plutot que de fermer immediatement comme sans sip_id.
        setCree(utilisateur);
      } else {
        fermer();
      }
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Erreur lors de la creation";
      setErreur(message);
    } finally {
      setChargement(false);
    }
  }

  if (cree) {
    return (
      <Modal open={open} onClose={fermer} title="Utilisateur cree">
        <p className="mb-3 text-sm text-ink-secondary">
          Identifiants SIP pour configurer Linphone (a communiquer a l&apos;utilisateur) :
        </p>
        <div className="mb-4 space-y-2 rounded-lg bg-surface-2 px-4 py-3 font-mono text-sm">
          <p>
            <span className="text-ink-muted">Nom d&apos;utilisateur : </span>
            <span className="text-accent">{cree.sip_id}</span>
          </p>
          <p>
            <span className="text-ink-muted">Mot de passe : </span>
            <span className="text-accent">{cree.sip_secret}</span>
          </p>
        </div>
        <p className="mb-4 text-xs text-ink-muted">
          Ce poste apparaîtra sur Asterisk après la prochaine synchronisation (quelques
          minutes). Ce secret reste consultable plus tard via l&apos;action « SIP » sur cet
          utilisateur.
        </p>
        <div className="flex justify-end">
          <Button onClick={fermer}>Fermer</Button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal open={open} onClose={fermer} title="Nouvel utilisateur">
      <form onSubmit={onSubmit}>
        <Field label="Nom d'utilisateur">
          <Input value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
        </Field>
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
        <Field label="Mot de passe">
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </Field>

        {erreur && <p className="mb-3 text-sm text-critical">{erreur}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={fermer}>
            Annuler
          </Button>
          <Button type="submit" disabled={chargement}>
            {chargement ? "Creation..." : "Creer"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
