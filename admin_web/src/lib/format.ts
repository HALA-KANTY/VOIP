export function formatMontant(valeur: string | number): string {
  const nombre = typeof valeur === "string" ? Number(valeur) : valeur;
  return `${nombre.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} AR`;
}

export function formatDate(iso: string): string {
  // Le backend stocke tout en UTC mais sans indicateur de fuseau (naive) :
  // sans le "Z", new Date() interprete la chaine comme deja en heure locale
  // du navigateur, decalant l'affichage de la difference UTC <-> fuseau reel.
  const isoAvecFuseau = iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso) ? iso : `${iso}Z`;
  return new Date(isoAvecFuseau).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDuree(secondes: number): string {
  const minutes = Math.floor(secondes / 60);
  const reste = secondes % 60;
  return `${minutes}:${reste.toString().padStart(2, "0")}`;
}
