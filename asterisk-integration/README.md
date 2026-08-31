# Intégration Asterisk ↔ Backend VoIP Billing

Ces fichiers vont sur le **serveur Asterisk** (VM séparée, 192.168.100.11),
pas dans un conteneur Docker. Installation détaillée : voir la section
« Intégration Asterisk » de [`../DEPLOYMENT.md`](../DEPLOYMENT.md).

Système interne à l'entreprise : pas de trunk PSTN, tous les postes
(Linphone) et la VM Asterisk sont sur le même réseau (192.168.100.0/24) —
aucune configuration NAT/traversée nécessaire.

**L'interface admin est la seule source de vérité** pour les postes SIP :
créer un utilisateur avec un `sip_id` y génère automatiquement un secret SIP.
`sync_pjsip.sh`, exécuté en cron sur la VM Asterisk, récupère cette liste via
l'API et la reflète dans `pjsip.conf` — rien à éditer à la main pour ajouter,
modifier ou désactiver un poste.

| Fichier | Destination sur le serveur Asterisk |
|---|---|
| `pjsip.conf` | À fusionner dans `/etc/asterisk/pjsip.conf` — transport + gabarits + inclusion des postes générés |
| `sync_pjsip.sh` | Script de synchronisation (à mettre en cron) : tire les postes depuis l'API |
| `manager-fastapi.conf` | À fusionner dans `/etc/asterisk/manager.conf` |
| `extensions-billing.conf` | À fusionner dans `/etc/asterisk/extensions.conf` |
| `voip-billing.conf.example` | À copier vers `/etc/asterisk/voip-billing.conf` (renseigner les vraies valeurs) |
| `agi-bin/*.py` | À copier vers `/var/lib/asterisk/agi-bin/` (`chmod +x`) |

## Créer un nouvel utilisateur (poste + facturation)

Un seul endroit à remplir :

1. Dans l'**interface admin**, créer l'utilisateur avec un `sip_id` (ex.
   `1004`). Un secret SIP est généré automatiquement — visible dans la
   réponse de création, et récupérable ensuite via le bouton dédié dans la
   table des utilisateurs.
2. Dans les **5 minutes suivantes** (fréquence du cron `sync_pjsip.sh`), le
   poste apparaît automatiquement dans `pjsip.conf` sur la VM Asterisk. Pour
   forcer la synchronisation immédiatement : `sudo /opt/sync_pjsip.sh`.
3. Configurer **Linphone** avec le `sip_id` comme nom d'utilisateur et le
   secret SIP généré à l'étape 1 (voir `../DEPLOYMENT.md` §9).

Suspendre un utilisateur (`statut = suspendu`) dans l'interface admin
désactive automatiquement son poste SIP au prochain sync — aucune action
supplémentaire côté Asterisk.

Les scripts AGI et `sync_pjsip.sh` n'ont aucune dépendance externe (stdlib
Python 3 / `curl` uniquement) et ont été testés contre le backend réel.
