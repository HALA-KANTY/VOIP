#!/bin/bash
# /etc/asterisk est un volume partage avec le conteneur backend. A la
# creation du volume (premier demarrage), Docker copie automatiquement tout
# le contenu image de /etc/asterisk -- y compris les configs par defaut du
# paquet Debian -- AVANT que ce script ne s'execute. On force donc l'ecrasement
# de nos fichiers statiques a chaque demarrage (idempotent), et on ne cree que
# si absents les fichiers dynamiques que le backend genere depuis la base
# (pjsip_users.conf, extensions_ivr.conf, voicemail.conf) pour ne jamais
# effacer de vraies donnees au redemarrage du conteneur Asterisk.
set -e

mkdir -p /etc/asterisk

FICHIERS_STATIQUES="pjsip.conf extensions.conf extensions-billing.conf manager.conf confbridge.conf queues.conf voip-billing.conf rtp.conf"
for name in $FICHIERS_STATIQUES; do
  cp "/etc/asterisk-defaults/$name" "/etc/asterisk/$name"
done

FICHIERS_DYNAMIQUES="pjsip_users.conf extensions_ivr.conf voicemail.conf"
for name in $FICHIERS_DYNAMIQUES; do
  [ -e "/etc/asterisk/$name" ] || cp "/etc/asterisk-defaults/$name" "/etc/asterisk/$name"
done

# Le conteneur backend ecrit directement dans ce volume partage sous un autre
# utilisateur (uid different de celui d'Asterisk) -- dev local uniquement,
# jamais expose hors du volume Docker.
chmod -R a+rwX /etc/asterisk

exec asterisk -f -vvv
