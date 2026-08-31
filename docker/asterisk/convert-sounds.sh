#!/bin/bash
# Convertit les prompts MP3 du projet (audio/) en WAV PCM 8kHz mono --
# Asterisk n'inclut pas de decodeur mp3 par defaut -- et les place sous
# /var/lib/asterisk/sounds/custom/<nom>.wav avec les noms attendus par le
# dialplan (Playback(custom/<nom>)).
#
# Certains prompts references dans le dialplan (token-invalide,
# votre-solde-est) n'ont pas de fichier source correspondant dans audio/ :
# ils sont laisses absents. Asterisk journalise un WARNING et poursuit sans
# jouer le son -- non bloquant pour la facturation/le routage des appels.
set -euo pipefail

SRC=/audio-src
# astdatadir = /usr/share/asterisk sur ce paquet Debian (pas /var/lib/asterisk,
# malgre le nom -- voir [directories] dans asterisk.conf).
DEST=/usr/share/asterisk/sounds/custom
mkdir -p "$DEST"

convertir() {
  ffmpeg -y -loglevel error -i "$1" -ar 8000 -ac 1 -c:a pcm_s16le "$DEST/$2.wav"
}

convertir "$SRC/sous-Menu-IVR-commercial/agent-occupe.mp3"            agent-occupe
convertir "$SRC/ariary.mp3"                                            ariary
convertir "$SRC/sous-Menu-IVR-commercial/aucun-nouveau-message.mp3"   aucun-nouveau-message
convertir "$SRC/bienvenue.mp3"                                         bienvenue-ivr
convertir "$SRC/au_revoir.mp3"                                         bye
convertir "$SRC/sous-Menu-IVR-commercial/choisir-montant.mp3"         choisir-montant
convertir "$SRC/sous-Menu-IVR-commercial/entrez-code-sip.mp3"         entrez-code-sip
convertir "$SRC/sous-Menu-IVR-commercial/menu-commercial.mp3"         menu-commercial
convertir "$SRC/sous-Menu-IVR-commercial/message-bip.mp3"             message-bip
convertir "$SRC/sous-Menu-IVR-commercial/nouveau-message-vocal.mp3"   nouveau-message-vocal
convertir "$SRC/recharge_success.mp3"                                  recharge-succes
convertir "$SRC/sous-Menu-IVR-commercial/recharger-succes.mp3"        recharger-succes
convertir "$SRC/sous-Menu-IVR-commercial/reccharge immediat.mp3"      recharger-maintenant
convertir "$SRC/sous-Menu-IVR-commercial/retour-menu.mp3"             retour-menu
convertir "$SRC/solde_insufisant.mp3"                                  solde-insuffisant
convertir "$SRC/sous-Menu-IVR-commercial/votre-code.mp3"               votre-code
convertir "$SRC/sous-Menu-IVR-commercial/vous-avez.mp3"               vous-avez

chmod -R a+rX "$DEST"

# Musique d'attente (Queue()) : musiconhold.conf pointe vers astdatadir/moh
# (/usr/share/asterisk/moh), vide par defaut sur ce paquet -- sans fichier
# dedans, la classe "default" ne joue rien et Queue() echoue immediatement
# ("no musiconhold loaded"). On y met un des prompts existants en boucle,
# a defaut d'une vraie musique d'attente.
mkdir -p /usr/share/asterisk/moh
cp "$DEST/menu-commercial.wav" /usr/share/asterisk/moh/attente.wav
