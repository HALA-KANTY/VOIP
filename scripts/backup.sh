#!/usr/bin/env bash
# ==========================================
# Sauvegarde automatique PostgreSQL
# ==========================================

set -euo pipefail

REPERTOIRE_BACKUP="/opt/voip-platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FICHIER_BACKUP="$REPERTOIRE_BACKUP/backup_${DATE}.sql.gz"
NOMBRE_MAX_SAUVEGARDES=7  # Garder les 7 dernières sauvegardes

# Créer le répertoire si nécessaire
mkdir -p "$REPERTOIRE_BACKUP"

echo "=========================================="
echo "SAUVEGARDE PostgreSQL"
echo "Date : $(date)"
echo "=========================================="

# Sauvegarde de la base de données
docker compose -f /opt/voip-platform/docker-compose.yml exec -T postgres \
    pg_dump -U voip_user -d voip_billing | gzip > "$FICHIER_BACKUP"

# Vérifier que la sauvegarde a réussi
if [ -s "$FICHIER_BACKUP" ]; then
    echo "✅ Sauvegarde créée : $FICHIER_BACKUP"
    ls -lh "$FICHIER_BACKUP"
else
    echo "❌ Erreur : la sauvegarde est vide"
    rm -f "$FICHIER_BACKUP"
    exit 1
fi

# Rotation : supprimer les anciennes sauvegardes
echo ""
echo "Rotation des sauvegardes (garder les $NOMBRE_MAX_SAUVEGARDES dernières)..."
ls -t "$REPERTOIRE_BACKUP"/backup_*.sql.gz 2>/dev/null | \
    tail -n +$((NOMBRE_MAX_SAUVEGARDES + 1)) | \
    while read -r ancien; do
    echo "Suppression de l'ancienne sauvegarde : $ancien"
    rm -f "$ancien"
done

echo ""
echo "=========================================="
echo "SAUVEGARDE TERMINÉE"
echo "=========================================="
