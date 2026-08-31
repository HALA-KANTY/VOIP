#!/usr/bin/env bash
# ==========================================
# Conversion des fichiers ElevenLabs en format Asterisk
# Source : /opt/voip-platform/audio/
# Destination : /var/lib/asterisk/sounds/custom/
# ==========================================

set -euo pipefail

REPERTOIRE_SOURCE="/opt/voip-platform/audio"
REPERTOIRE_DESTINATION="/var/lib/asterisk/sounds/custom"

sudo mkdir -p "$REPERTOIRE_DESTINATION"

convertir_audio() {
    local fichier_source="$1"
    local nom_destination="$2"
    
    echo "Conversion de ${fichier_source} → ${nom_destination}.wav"
    
    # Conversion avec sudo
    sudo ffmpeg -i "$REPERTOIRE_SOURCE/$fichier_source" \
        -ar 8000 -ac 1 -sample_fmt s16 \
        -y "$REPERTOIRE_DESTINATION/${nom_destination}.wav"
    
    echo "  → OK"
}

# Conversion des fichiers ElevenLabs
convertir_audio "bienvenue.mp3" "bienvenue-ivr"
convertir_audio "solde_insufisant.mp3" "solde-insuffisant"
convertir_audio "votre_solde.mp3" "votre-solde-est"
convertir_audio "ariary.mp3" "ariary"
convertir_audio "saisir_token.mp3" "saisir-token"
convertir_audio "recharge_success.mp3" "recharge-succes"
convertir_audio "token_invalide.mp3" "token-invalide"
convertir_audio "au_revoir.mp3" "bye"
convertir_audio "ligne_occupe.mp3" "ligne-occupee"

# Sous-menu IVR commercial (achat de credit / agent)
convertir_audio "sous-Menu-IVR-commercial/menu-commercial.mp3" "menu-commercial"
convertir_audio "sous-Menu-IVR-commercial/choisir-montant.mp3" "choisir-montant"
convertir_audio "sous-Menu-IVR-commercial/votre-code.mp3" "votre-code"
convertir_audio "sous-Menu-IVR-commercial/agent-occupe.mp3" "agent-occupe"
convertir_audio "sous-Menu-IVR-commercial/retour-menu.mp3" "retour-menu"

# Messagerie vocale (poste a poste + file commerciale)
convertir_audio "sous-Menu-IVR-commercial/message-bip.mp3" "message-bip"

# Recharge immediate apres achat de credit (voir commercial-code-confirme)
convertir_audio "sous-Menu-IVR-commercial/reccharge immediat.mp3" "recharger-maintenant"
convertir_audio "sous-Menu-IVR-commercial/recharger-succes.mp3" "recharger-succes"

# Annonce des messages vocaux (menu 100, option 5)
convertir_audio "sous-Menu-IVR-commercial/vous-avez.mp3" "vous-avez"
convertir_audio "sous-Menu-IVR-commercial/nouveau-message-vocal.mp3" "nouveau-message-vocal"
convertir_audio "sous-Menu-IVR-commercial/entrez-code-sip.mp3" "entrez-code-sip"
convertir_audio "sous-Menu-IVR-commercial/aucun-nouveau-message.mp3" "aucun-nouveau-message"

echo ""
echo "=========================================="
echo "CONVERSION TERMINÉE !"
echo "=========================================="
ls -lh "$REPERTOIRE_DESTINATION"/*.wav
