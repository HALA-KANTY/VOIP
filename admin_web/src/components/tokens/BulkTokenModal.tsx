"use client";

import { useState, type FormEvent } from "react";
import { jsPDF } from "jspdf";
import { Modal } from "@/components/ui/Modal";
import { Field, Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { tokensApi } from "@/lib/api";

export function BulkTokenModal({
  open,
  onClose,
  onEffectue,
}: {
  open: boolean;
  onClose: () => void;
  onEffectue: () => void;
}) {
  const [montant, setMontant] = useState("");
  const [quantite, setQuantite] = useState("10");
  const [erreur, setErreur] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);

  function telechargerPdf(codes: string[], montant: string) {
    const doc = new jsPDF({ unit: "mm", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();

    doc.setFillColor(245, 247, 250);
    doc.rect(0, 0, pageWidth, 40, "F");
    doc.setFontSize(18);
    doc.setTextColor(30, 41, 59);
    doc.text("Lot de crédit token", 14, 20);
    doc.setFontSize(11);
    doc.setTextColor(71, 85, 105);
    doc.text(`Montant unitaire: ${montant} AR`, 14, 30);
    doc.text(`Quantité: ${codes.length} codes`, 14, 36);

    let y = 52;
    const colX = [14, 80, 146];
    doc.setDrawColor(203, 213, 225);
    doc.setLineWidth(0.3);
    doc.roundedRect(10, 48, pageWidth - 20, 200, 3, 3, "S");

    doc.setFontSize(10);
    doc.setTextColor(15, 23, 42);
    doc.text("N°", colX[0], y);
    doc.text("Code", colX[1], y);
    doc.text("Montant", colX[2], y);
    y += 8;

    codes.forEach((code, index) => {
      if (y > 220) {
        doc.addPage();
        y = 18;
      }

      doc.setTextColor(15, 23, 42);
      doc.text(String(index + 1), colX[0], y);
      doc.text(code, colX[1], y);
      doc.text(`${montant} AR`, colX[2], y);
      y += 7;
    });

    doc.save(`lot-tokens-${Date.now()}.pdf`);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setErreur(null);
    setChargement(true);

    try {
      const resultat = await tokensApi.genererLot({
        montant: montant,
        quantite: parseInt(quantite, 10),
      });

      const codes = resultat.codes ?? [];
      telechargerPdf(codes, resultat.montant);

      setMontant("");
      setQuantite("10");
      onEffectue();
      onClose();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Impossible de générer le lot de tokens";
      setErreur(message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Générer des tokens en lot (Bulk)"
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Montant unitaire (AR)">
          <Input
            type="number"
            step="1"
            min="100"
            placeholder="Ex: 1000"
            value={montant}
            onChange={(e) => setMontant(e.target.value)}
            required
            autoFocus
          />
        </Field>

        <Field label="Quantité à générer">
          <select
            value={quantite}
            onChange={(e) => setQuantite(e.target.value)}
            className="w-full rounded-lg border border-surface-3 bg-surface-1 px-3 py-2 text-sm text-ink-primary"
          >
            <option value="10">10 tickets</option>
            <option value="50">50 tickets</option>
            <option value="100">100 tickets</option>
            <option value="500">500 tickets</option>
          </select>
        </Field>

        {erreur && <p className="text-sm text-critical font-medium">{erreur}</p>}

        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" disabled={chargement}>
            {chargement ? "Génération en cours..." : "Générer le lot"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
