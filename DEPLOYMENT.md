# Déploiement — Plateforme VoIP Billing

Guide de déploiement de la stack **backend + interface admin + PostgreSQL +
nginx** (conteneurisée avec Docker) sur un serveur **Debian 13**, ainsi que
des étapes à effectuer côté **Asterisk** (géré séparément) et côté
**Linphone** (client externe).

---

## 1. Architecture de déploiement

```
                    Internet
                       │
                       │ 80/443
                       ▼
              ┌──────────────────┐
              │   nginx (Docker) │  reverse proxy + TLS
              └────────┬─────────┘
                       │ réseau Docker interne
          ┌────────────┼────────────┐
          ▼                         ▼
  ┌───────────────┐        ┌───────────────┐
  │  admin_web     │        │   backend     │
  │  (Next.js)     │        │  (FastAPI)    │
  └───────────────┘        └───────┬───────┘
                                    │
                       ┌────────────┼────────────┐
                       ▼                         ▼
              ┌────────────────┐      AMI (5038)  serveur Asterisk
              │   postgres      │      TCP sortant  (géré séparément,
              │   (Docker)      │◄─────────────────  potentiellement
              └────────────────┘                     un autre serveur)
```

Tout tourne sur **un seul serveur Debian 13** via Docker Compose (postgres,
backend, admin_web, nginx). Asterisk reste géré séparément (autre serveur ou
autre équipe) : le backend s'y connecte en sortant vers le port AMI 5038.

**Contrainte importante** : le backend maintient en mémoire la connexion AMI
et les compteurs d'appels en temps réel. Il doit tourner en **un seul
conteneur/processus** — ne jamais le scaler horizontalement (`--scale
backend=2`, plusieurs workers uvicorn, etc.) sans redesigner cet état pour
qu'il soit partagé (Redis ou équivalent).

---

## 2. Prérequis

- Un serveur Debian 13 avec accès root/sudo, IP publique.
- Un nom de domaine dont l'enregistrement DNS `A` pointe vers l'IP du serveur
  (ex. `voip.example.com`) — nécessaire pour le TLS.
- Accès réseau sortant du serveur backend vers le port AMI (5038) du serveur
  Asterisk (même réseau privé, VPN, ou règle de pare-feu explicite côté
  Asterisk — voir §7).

---

## 3. Installation de Docker sur Debian 13

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Utiliser docker sans sudo (se reconnecter apres cette commande)
sudo usermod -aG docker $USER
```

Vérifier :

```bash
docker --version
docker compose version
```

---

## 4. Pare-feu (ufw)

```bash
sudo apt-get install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Le port 5038 (AMI) et les ports SIP/RTP ne concernent **pas** ce serveur : ils
sont ouverts côté serveur Asterisk (voir §7), pas ici. Aucun autre port
(postgres, backend, admin_web) ne doit être exposé publiquement — ils ne sont
même pas publiés sur l'hôte dans `docker-compose.yml`, seul nginx l'est.

---

## 5. Récupération du code et configuration

```bash
sudo mkdir -p /opt/voip-billing
sudo chown $USER:$USER /opt/voip-billing
cd /opt/voip-billing
git clone <URL_DU_DEPOT> .
# ou : scp -r le projet depuis votre machine

cp .env.example .env
nano .env   # renseigner TOUTES les valeurs, notamment :
            #   - mots de passe (POSTGRES_PASSWORD, ADMIN_PASSWORD)
            #   - JWT_SECRET_KEY (ex: openssl rand -hex 32)
            #   - ASTERISK_AMI_HOST/SECRET (coordonnees avec l'admin Asterisk)
            #   - AMI_ENDPOINTS_SECRET (le meme cote Asterisk, voir §7)
            #   - DOMAIN, CORS_ORIGINS, NEXT_PUBLIC_API_URL = https://<domaine>
```

Générer un secret JWT solide :

```bash
openssl rand -hex 32
```

---

## 6. Premier lancement (phase 1 — HTTP)

`nginx/conf.d/default.conf` est prêt à l'emploi tel quel (HTTP simple,
`server_name _`) : il fonctionne avant même d'avoir un certificat, ce qui est
nécessaire pour l'étape TLS suivante (challenge ACME).

```bash
cd /opt/voip-billing
docker compose build
docker compose up -d
docker compose ps        # tout doit etre "healthy" / "Up"
```

Vérifications :

```bash
curl -s http://localhost/health                 # {"status":"ok"}
curl -s http://localhost/docs -o /dev/null -w "%{http_code}\n"   # 200
curl -s http://<IP_OU_DOMAINE>/                  # doit renvoyer le HTML de la page de connexion
```

Un compte admin par défaut est créé automatiquement au premier démarrage à
partir de `ADMIN_USERNAME`/`ADMIN_PASSWORD` — **connectez-vous une fois puis
changez ce mot de passe** (pas d'endpoint dédié pour l'instant : le
réinitialiser directement en base, ou recréer l'admin, est acceptable pour un
déploiement initial).

---

## 7. TLS avec Let's Encrypt (phase 2)

DNS doit déjà pointer vers le serveur (`dig +short <domaine>` doit renvoyer
son IP) avant de continuer.

```bash
cd /opt/voip-billing

# Obtenir le certificat (webroot servi par le nginx deja en marche, phase 1)
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d <VOTRE_DOMAINE> \
  --email <VOTRE_EMAIL> --agree-tos --no-eff-email

# Activer la configuration HTTPS
cp nginx/conf.d/default.conf nginx/conf.d/default.conf.bak
cp nginx/conf.d/ssl.conf.example nginx/conf.d/default.conf
sed -i "s/<VOTRE_DOMAINE>/<VOTRE_DOMAINE>/g" nginx/conf.d/default.conf   # remplacer par le vrai domaine

docker compose exec nginx nginx -t     # verifie la syntaxe avant de recharger
docker compose exec nginx nginx -s reload
```

Vérifier : `https://<domaine>/health` doit répondre `{"status":"ok"}` avec un
certificat valide.

**Renouvellement automatique** (les certificats Let's Encrypt expirent tous
les 90 jours) — ajouter au crontab root (`sudo crontab -e`) :

```cron
0 3 * * 1 cd /opt/voip-billing && docker compose run --rm certbot renew --webroot -w /var/www/certbot -q && docker compose exec nginx nginx -s reload
```

---

## 8. Intégration Asterisk

Contexte de ce déploiement : Asterisk tourne dans une VM KVM séparée à
**192.168.100.11**, sur le même réseau interne que le serveur Docker.
Système interne à l'entreprise, **sans trunk PSTN** — les appels se font
entre extensions internes uniquement. Comme tout est sur le même réseau,
**aucune configuration NAT** (`external_media_address`, etc.) n'est
nécessaire. Les fichiers prêts à l'emploi sont dans
[`asterisk-integration/`](asterisk-integration/) — à copier **sur la VM
Asterisk**, pas dans Docker.

### 8.1 Postes SIP (pjsip.conf) — synchronisés depuis l'interface admin

L'interface admin est la **seule source de vérité** : créer un utilisateur
avec un `sip_id` y génère automatiquement un secret SIP (endpoint
`POST /api/utilisateurs`, champ `sip_secret` dans la réponse). Rien à saisir
manuellement côté Asterisk pour chaque poste.

```bash
# Gabarits + transport (une seule fois)
sudo cp asterisk-integration/pjsip.conf /etc/asterisk/pjsip.conf
sudo touch /etc/asterisk/pjsip_users.conf   # fichier genere, vide au depart

# Script de synchronisation (une seule fois)
sudo cp asterisk-integration/sync_pjsip.sh /opt/sync_pjsip.sh
sudo chmod +x /opt/sync_pjsip.sh
sudo cp asterisk-integration/voip-billing.conf.example /etc/asterisk/voip-billing.conf
sudo nano /etc/asterisk/voip-billing.conf   # api_base = http://<IP_SERVEUR_DOCKER>, ami_endpoints_secret = ...
sudo chmod 640 /etc/asterisk/voip-billing.conf

# Premiere synchronisation manuelle
sudo /opt/sync_pjsip.sh
asterisk -rx "pjsip reload"
asterisk -rx "pjsip show endpoints"   # doit lister les utilisateurs deja crees avec un sip_id

# Automatiser (toutes les 5 minutes)
echo "*/5 * * * * root /opt/sync_pjsip.sh >> /var/log/sync_pjsip.log 2>&1" | sudo tee /etc/cron.d/sync-pjsip
```

À partir de là : créer un utilisateur avec un `sip_id` dans l'interface admin
suffit — il apparaît sur Asterisk au plus tard 5 minutes après (ou
immédiatement avec `sudo /opt/sync_pjsip.sh`). Suspendre l'utilisateur
désactive son poste au sync suivant. Procédure détaillée :
[`asterisk-integration/README.md`](asterisk-integration/README.md), section
« Créer un nouvel utilisateur ».

### 8.2 Compte AMI

Ajouter dans `/etc/asterisk/manager.conf` sur la VM Asterisk (adapter
depuis [`asterisk-integration/manager-fastapi.conf`](asterisk-integration/manager-fastapi.conf)) :

```ini
[fastapi]
secret = <meme valeur que ASTERISK_AMI_SECRET dans .env>
deny = 0.0.0.0/0.0.0.0
permit = 192.168.100.0/255.255.255.0
read = call,cdr,dialplan
write = call,originate
```

Puis `asterisk -rx "manager reload"`. Le sous-réseau entier est autorisé le
temps de confirmer l'IP exacte du serveur Docker (`hostname -I` sur ce
serveur) ; resserrer ensuite `permit` à cette seule IP en `/255.255.255.255`.

### 8.3 Scripts AGI (vérification de solde + CDR)

```bash
sudo cp asterisk-integration/agi-bin/*.py /var/lib/asterisk/agi-bin/
sudo chmod +x /var/lib/asterisk/agi-bin/*.py

sudo cp asterisk-integration/voip-billing.conf.example /etc/asterisk/voip-billing.conf
sudo nano /etc/asterisk/voip-billing.conf   # api_base = http://192.168.100.X (IP du serveur Docker), ami_endpoints_secret = ...
sudo chmod 640 /etc/asterisk/voip-billing.conf
```

### 8.4 Dialplan

Copier [`asterisk-integration/extensions-billing.conf`](asterisk-integration/extensions-billing.conf)
dans `/etc/asterisk/extensions.conf` (adapter le pattern `_1XXX` si votre
plan de numérotation diffère), puis `asterisk -rx "dialplan reload"`.

Ce dialplan :
1. Appelle `verifier_solde.py` **avant** de composer — refuse l'appel si le
   solde est insuffisant (fail-closed si l'API est injoignable).
2. Compose en interne via `PJSIP/${EXTEN}` (l'extension appelée = un autre
   poste défini dans `pjsip.conf`).
3. Appelle `enregistrer_appel.py` à la fin de **chaque** appel (extension
   `h`) — enregistre le CDR définitif et débite le solde.

Le compteur temps réel qui **coupe un appel en cours** si le solde s'épuise
pendant la conversation est déjà géré côté backend via les événements AMI
(`BridgeEnter`/`Hangup`) — rien à faire côté dialplan pour ça, c'est un
second filet de sécurité indépendant.

### 8.5 Vérification

```bash
# Depuis la VM Asterisk : verifier que le backend est joignable
curl -s "http://<IP_SERVEUR_DOCKER>/api/check_balance?sip_id=1001" -H "X-AMI-Secret: <AMI_ENDPOINTS_SECRET>"

# Depuis le serveur backend (Docker) : verifier la connexion AMI
docker compose logs backend | grep -i "ami"
# doit finir par "Connexion AMI etablie sur 192.168.100.11:5038" et non des "Connexion AMI perdue" en boucle
```

---

## 9. Configuration Linphone

Linphone n'est pas géré par cette stack — c'est un client SIP standard qui se
connecte **directement à Asterisk** (192.168.100.11), pas au backend. Les
identifiants SIP (utilisateur/mot de passe) sont le `sip_id` et le
`sip_secret` **générés automatiquement à la création de l'utilisateur dans
l'interface admin** (§8.1), **pas** le mot de passe de connexion à
l'interface admin — deux systèmes d'authentification distincts.

Tous les postes étant sur le même réseau interne que la VM Asterisk, la
configuration est simple : pas de STUN, pas de TLS, transport UDP standard.

Dans Linphone → *Paramètres* → *Comptes* → *Ajouter un compte SIP* →
*Utiliser un compte SIP existant* :

| Champ | Valeur |
|---|---|
| Nom d'utilisateur | le numéro de poste (ex. `1004`) |
| Mot de passe | le `sip_secret` affiché dans l'interface admin pour cet utilisateur |
| Domaine / serveur SIP | `192.168.100.11` |
| Transport | UDP |
| Port | `5060` |

Après validation, l'état du compte doit passer à **« Connecté »** (point
vert). Test rapide : depuis le poste `1004`, appeler `1001` — l'appel doit
sonner sur l'autre poste, et un CDR doit apparaître dans l'interface admin
(page *Journal d'appels*) une fois l'appel terminé.

**Dépannage Linphone courant :**
- *Échec d'enregistrement (403/401)* : mot de passe SIP incorrect, ou
  `asterisk -rx "pjsip show endpoints"` ne liste pas ce poste (relire §8.1).
- *Enregistré mais l'appel ne sonne pas* : vérifier `_1XXX` dans le dialplan
  correspond bien au numéro composé, et `asterisk -rx "dialplan show voip-billing"`.
- *Ça sonne mais pas de son* : peu probable ici (même réseau, pas de NAT) —
  si ça arrive quand même, vérifier qu'aucun pare-feu local (`ufw` sur la VM
  Asterisk) ne bloque la plage RTP (par défaut UDP 10000-20000, voir
  `rtp.conf`).

---

## 10. Mise à jour / redéploiement

```bash
cd /opt/voip-billing
git pull
docker compose build
docker compose up -d
docker compose ps
```

Les tables sont créées automatiquement au démarrage (`create_all`) mais il
n'y a pas encore de système de migration (Alembic) pour faire évoluer un
schéma déjà en production sans perte — à mettre en place avant le premier
changement de modèle de données en prod.

---

## 11. Sauvegardes PostgreSQL

```bash
# Sauvegarde manuelle
docker compose exec -T postgres pg_dump -U <POSTGRES_USER> <POSTGRES_DB> | gzip > backup_$(date +%F).sql.gz

# Restauration
gunzip -c backup_2026-01-01.sql.gz | docker compose exec -T postgres psql -U <POSTGRES_USER> <POSTGRES_DB>
```

À automatiser via cron (`sudo crontab -e`), avec rotation/purge des anciennes
sauvegardes et copie hors du serveur.

---

## 12. Logs et supervision

```bash
docker compose logs -f backend
docker compose logs -f nginx
docker compose ps                 # etat / healthchecks
curl -s https://<domaine>/health  # sonde simple pour un monitoring externe
```

---

## 13. Checklist sécurité avant mise en production

- [ ] `ADMIN_PASSWORD` par défaut changé
- [ ] `JWT_SECRET_KEY` généré aléatoirement (`openssl rand -hex 32`), pas la valeur d'exemple
- [ ] `POSTGRES_PASSWORD` et `ASTERISK_AMI_SECRET`/`AMI_ENDPOINTS_SECRET` forts et uniques
- [ ] `manager.conf` : `permit` restreint à l'IP exacte du serveur backend (jamais `0.0.0.0/0`)
- [ ] `CORS_ORIGINS` limité au vrai domaine (pas `*`)
- [ ] HTTPS actif (phase 2, §7), redirection HTTP→HTTPS effective
- [ ] `.env` non commité, permissions restreintes (`chmod 600 .env`)
- [ ] Sauvegardes PostgreSQL automatisées et testées (restauration vérifiée au moins une fois)
- [ ] Port 5432 (postgres) non exposé publiquement (déjà le cas par défaut dans `docker-compose.yml`)

---

## 14. Dépannage courant

| Symptôme | Piste |
|---|---|
| `docker compose ps` montre `backend` unhealthy | `docker compose logs backend` — souvent `DATABASE_URL` incorrect ou postgres pas encore prêt |
| Page admin blanche / erreurs CORS dans la console | `NEXT_PUBLIC_API_URL` doit être l'URL **publique** (https://domaine), pas `http://backend:8000` ; nécessite un rebuild (`docker compose build admin_web`) car c'est injecté au build |
| `Connexion AMI perdue` en boucle dans les logs backend | Vérifier `ASTERISK_AMI_HOST/PORT`, la règle `permit` dans `manager.conf`, et la connectivité réseau (`nc -zv <host_asterisk> 5038` depuis le conteneur backend) |
| Certbot échoue (`Failed authorization`) | Le DNS ne pointe pas encore vers le serveur, ou le port 80 n'est pas accessible depuis l'extérieur (pare-feu / autre service déjà sur le port 80) |
| Un appel n'est jamais facturé | Vérifier que le `sip_id` de l'utilisateur (interface admin) correspond exactement à l'extension Asterisk ; tester `verifier_solde.py`/`enregistrer_appel.py` manuellement (voir leurs docstrings) |
