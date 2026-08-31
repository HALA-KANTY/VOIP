"use client";

import { useCallback, useEffect, useState } from "react";
import { servicesIvrApi } from "@/lib/api";
import type { ServiceIVR, ServiceIVRCreate } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { IconPlus } from "@/components/ui/icons";

const TYPES_LABELS: Record<string, string> = {
  queue: "File d'attente",
  dial: "Poste",
  conf: "Conférence",
  playback: "Message",
};

const FORM_VIDE: ServiceIVRCreate = {
  nom: "",
  code: "",
  type: "queue",
  destination: "",
  description: "",
};

export default function ServicesIVRPage() {
  const [services, setServices] = useState<ServiceIVR[]>([]);
  const [chargement, setChargement] = useState(true);
  const [formVisible, setFormVisible] = useState(false);
  const [serviceEnEdition, setServiceEnEdition] = useState<ServiceIVR | null>(null);
  const [form, setForm] = useState<ServiceIVRCreate>(FORM_VIDE);

  const recharger = useCallback(() => {
    setChargement(true);
    servicesIvrApi
      .lister()
      .then(setServices)
      .finally(() => setChargement(false));
  }, []);

  useEffect(() => {
    function chargerInitial() {
      recharger();
    }
    chargerInitial();
  }, [recharger]);

  function ouvrirCreation() {
    setServiceEnEdition(null);
    setForm(FORM_VIDE);
    setFormVisible(true);
  }

  function ouvrirEdition(service: ServiceIVR) {
    setServiceEnEdition(service);
    setForm({
      nom: service.nom,
      code: service.code,
      type: service.type,
      destination: service.destination,
      description: service.description ?? "",
    });
    setFormVisible(true);
  }

  function fermerForm() {
    setServiceEnEdition(null);
    setForm(FORM_VIDE);
    setFormVisible(false);
  }

  async function valider(e: React.FormEvent) {
    e.preventDefault();
    if (serviceEnEdition) {
      await servicesIvrApi.modifier(serviceEnEdition.id, form);
    } else {
      await servicesIvrApi.creer(form);
    }
    fermerForm();
    recharger();
  }

  async function basculerActif(service: ServiceIVR) {
    await servicesIvrApi.modifier(service.id, { actif: !service.actif });
    recharger();
  }

  async function supprimer(id: number) {
    if (confirm("Supprimer ce service IVR ?")) {
      await servicesIvrApi.supprimer(id);
      recharger();
    }
  }

  return (
    <div>
      <PageHeader
        title="Services IVR"
        subtitle="Gestion des services accessibles depuis le menu vocal"
        action={
          <Button onClick={() => (formVisible ? fermerForm() : ouvrirCreation())}>
            <IconPlus /> {formVisible ? "Annuler" : "Nouveau service"}
          </Button>
        }
      />

      {formVisible && (
        <Card className="mb-6">
          <form onSubmit={valider} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm text-ink-secondary">Nom du service</label>
                <input
                  value={form.nom}
                  onChange={(e) => setForm({ ...form, nom: e.target.value })}
                  className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 text-sm"
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-ink-secondary">Code (ex: 1001#)</label>
                <input
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 font-mono text-sm"
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm text-ink-secondary">Type</label>
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value })}
                  className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 text-sm"
                >
                  <option value="queue">File d&apos;attente (Queue)</option>
                  <option value="dial">Poste (Dial)</option>
                  <option value="conf">Conférence (ConfBridge)</option>
                  <option value="playback">Message (Playback)</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm text-ink-secondary">Destination</label>
                <input
                  value={form.destination}
                  onChange={(e) => setForm({ ...form, destination: e.target.value })}
                  placeholder="commercial_queue, PJSIP/2001, 1234..."
                  className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 font-mono text-sm"
                  required
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm text-ink-secondary">Description (optionnel)</label>
              <input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 text-sm"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={fermerForm}>
                Annuler
              </Button>
              <Button type="submit">{serviceEnEdition ? "Enregistrer" : "Créer le service"}</Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {chargement ? (
          <p className="py-12 text-center text-sm text-ink-muted">Chargement...</p>
        ) : services.length === 0 ? (
          <p className="py-12 text-center text-sm text-ink-muted">
            Aucun service IVR. Cliquez sur « Nouveau service » pour en créer un.
          </p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-3 text-left text-xs text-ink-muted">
                <th className="px-4 py-3 font-medium">Nom</th>
                <th className="px-4 py-3 font-medium">Code</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Destination</th>
                <th className="px-4 py-3 font-medium">État</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {services.map((service) => (
                <tr key={service.id} className="border-b border-surface-3 last:border-0 hover:bg-surface-2/50">
                  <td className="px-4 py-3 text-sm">{service.nom}</td>
                  <td className="px-4 py-3 font-mono text-sm text-accent">{service.code}</td>
                  <td className="px-4 py-3 text-sm">{TYPES_LABELS[service.type] ?? service.type}</td>
                  <td className="px-4 py-3 font-mono text-sm">{service.destination}</td>
                  <td className="px-4 py-3">
                    {service.actif ? (
                      <Badge tone="good">Actif</Badge>
                    ) : (
                      <Badge tone="neutral">Inactif</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => ouvrirEdition(service)}
                        className="rounded-lg px-3 py-1 text-xs text-ink-secondary hover:bg-surface-2"
                      >
                        Modifier
                      </button>
                      <button
                        onClick={() => basculerActif(service)}
                        className="rounded-lg px-3 py-1 text-xs text-ink-secondary hover:bg-surface-2"
                      >
                        {service.actif ? "Désactiver" : "Activer"}
                      </button>
                      <button
                        onClick={() => supprimer(service.id)}
                        className="rounded-lg px-3 py-1 text-xs text-red-500 hover:bg-red-50"
                      >
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
