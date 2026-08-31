#!/usr/bin/env bash
# Synchronise les postes SIP depuis l'interface admin (source de verite) vers
# Asterisk : recupere GET /api/pjsip_export et recharge pjsip si le contenu a
# change. A executer SUR le serveur Asterisk, en cron (toutes les 5 minutes
# par exemple -- voir DEPLOYMENT.md).
#
# Usage : sudo ./sync_pjsip.sh
# Config : /etc/asterisk/voip-billing.conf (api_base, ami_endpoints_secret)

set -euo pipefail

CONFIG_FILE="/etc/asterisk/voip-billing.conf"
DEST_FILE="/etc/asterisk/pjsip_users.conf"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Erreur : $CONFIG_FILE introuvable (voir voip-billing.conf.example)." >&2
  exit 1
fi

api_base=$(grep -E '^\s*api_base\s*=' "$CONFIG_FILE" | head -1 | cut -d= -f2- | xargs)
secret=$(grep -E '^\s*ami_endpoints_secret\s*=' "$CONFIG_FILE" | head -1 | cut -d= -f2- | xargs)

if [ -z "$api_base" ] || [ -z "$secret" ]; then
  echo "Erreur : api_base ou ami_endpoints_secret manquant dans $CONFIG_FILE." >&2
  exit 1
fi

TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

code_http=$(curl -sS -o "$TMP_FILE" -w "%{http_code}" \
  -H "X-AMI-Secret: $secret" \
  "${api_base%/}/api/pjsip_export")

if [ "$code_http" != "200" ]; then
  echo "Erreur : l'API a repondu $code_http (verifier api_base/secret/reseau)." >&2
  cat "$TMP_FILE" >&2
  exit 1
fi

if [ -f "$DEST_FILE" ] && cmp -s "$TMP_FILE" "$DEST_FILE"; then
  exit 0   # rien de change, pas besoin de recharger
fi

cp "$TMP_FILE" "$DEST_FILE"

if command -v asterisk >/dev/null 2>&1; then
  asterisk -rx "pjsip reload" > /dev/null
  echo "$(date -Iseconds) : pjsip_users.conf mis a jour et pjsip recharge."
else
  echo "$(date -Iseconds) : pjsip_users.conf mis a jour (commande asterisk introuvable, reload manuel requis)."
fi
