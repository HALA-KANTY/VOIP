"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { CDRFiltres } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { IconDownload } from "@/components/ui/icons";

export function ExportButton({ filtres }: { filtres: CDRFiltres }) {
  const [enCours, setEnCours] = useState(false);

  async function exporter() {
    setEnCours(true);
    try {
      const reponse = await api.get("/api/cdr/export", {
        params: filtres,
        responseType: "blob",
      });
      const url = URL.createObjectURL(reponse.data);
      const lien = document.createElement("a");
      lien.href = url;
      lien.download = "cdr_export.csv";
      lien.click();
      URL.revokeObjectURL(url);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <Button variant="secondary" onClick={exporter} disabled={enCours}>
      <IconDownload /> {enCours ? "Export..." : "Exporter CSV"}
    </Button>
  );
}
