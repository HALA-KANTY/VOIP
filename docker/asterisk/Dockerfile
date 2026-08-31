# Asterisk de test pour developpement local UNIQUEMENT.
#
# En production, Asterisk tourne sur une VM separee geree independamment
# (voir ../../DEPLOYMENT.md, ../../asterisk-integration/). Ce Dockerfile
# n'est utilise que par docker-compose.override.yml pour permettre de tester
# des appels SIP (Linphone) et le flux de facturation en local, sans VM.

# bullseye (Debian 11) : le paquet "asterisk" a ete retire des depots a
# partir de bookworm (Debian 12), faute de mainteneur.
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        asterisk asterisk-core-sounds-en-gsm asterisk-core-sounds-fr-gsm \
        python3 ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Le paquet fr-gsm installe sous sounds/fr_CA_f_June/ (nom de la voix) --
# Asterisk cherche sounds/<language>/ pour language=fr (voir pjsip.conf).
RUN ln -s fr_CA_f_June /usr/share/asterisk/sounds/fr

# Prompts vocaux custom : convertis de mp3 (non lisible nativement par
# Asterisk) vers wav PCM 8kHz mono. Voir convert-sounds.sh pour le mapping
# nom-de-fichier -> nom-de-prompt (custom/<nom> dans le dialplan).
COPY audio/ /audio-src/
COPY docker/asterisk/convert-sounds.sh /convert-sounds.sh
RUN chmod +x /convert-sounds.sh && /convert-sounds.sh && rm -rf /audio-src /convert-sounds.sh

# Snapshot des configs par defaut installees par le paquet asterisk, avant
# qu'un volume (potentiellement vide au premier demarrage) ne soit monte sur
# /etc/asterisk -- l'entrypoint s'en sert pour amorcer le volume partage avec
# le conteneur backend.
RUN cp -r /etc/asterisk /etc/asterisk-defaults

COPY docker/asterisk/pjsip.conf /etc/asterisk-defaults/pjsip.conf
COPY asterisk-integration/extensions-billing.conf /etc/asterisk-defaults/extensions-billing.conf
COPY asterisk-integration/queues.conf /etc/asterisk-defaults/queues.conf
COPY asterisk-integration/confbridge.conf /etc/asterisk-defaults/confbridge.conf
COPY asterisk-integration/agi-bin/*.py /usr/share/asterisk/agi-bin/
# Fichiers source avec fins de ligne Windows (CRLF) : casse le shebang
# "#!/usr/bin/env python3\r" (env cherche un programme nomme "python3\r").
# Python systeme sur bullseye = 3.9, qui ne supporte pas la syntaxe
# "X | None" (PEP 604, Python 3.10+) utilisee dans ces scripts : on force
# l'evaluation paresseuse des annotations pour rester compatible.
RUN sed -i 's/\r$//' /usr/share/asterisk/agi-bin/*.py \
    && for f in /usr/share/asterisk/agi-bin/*.py; do \
         if head -n1 "$f" | grep -q '^#!'; then \
           sed -i '1a from __future__ import annotations' "$f"; \
         else \
           sed -i '1i from __future__ import annotations' "$f"; \
         fi; \
       done

COPY docker/asterisk/extensions.conf /etc/asterisk-defaults/extensions.conf
COPY docker/asterisk/manager.conf /etc/asterisk-defaults/manager.conf
COPY docker/asterisk/voip-billing.conf /etc/asterisk-defaults/voip-billing.conf
COPY docker/asterisk/rtp.conf /etc/asterisk-defaults/rtp.conf
COPY docker/asterisk/entrypoint.sh /entrypoint.sh

RUN chmod +x /usr/share/asterisk/agi-bin/*.py /entrypoint.sh \
    && touch /etc/asterisk-defaults/pjsip_users.conf \
             /etc/asterisk-defaults/extensions_ivr.conf \
             /etc/asterisk-defaults/voicemail.conf

EXPOSE 5060/udp 5038/tcp 10000-10020/udp

ENTRYPOINT ["/entrypoint.sh"]
