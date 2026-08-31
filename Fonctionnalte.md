Parfait. Faisons un **inventaire exhaustif et structuré** de toutes les fonctionnalités de la plateforme, pour servir de référence unique.

---

# Inventaire complet des fonctionnalités

## 1. Fonctionnalités Utilisateur (Linphone)

| # | Fonctionnalité | Description | Statut |
|---|----------------|-------------|--------|
| 1 | **Se connecter au serveur SIP** | L'utilisateur configure Linphone avec ses identifiants SIP (1001, 1002...) | ⚠️ Configuré mais à tester |
| 2 | **Appeler le menu principal** | Composer `100` pour accéder au menu vocal | ❌ À configurer |
| 3 | **Naviguer dans le menu IVR** | Écouter les options et choisir avec les touches (1-4) | ❌ À configurer |
| 4 | **Service Commercial** | Composer `200` ou choisir l'option 1 | ❌ À configurer |
| 5 | **Support Technique** | Composer `300` ou choisir l'option 2 | ❌ À configurer |
| 6 | **Service Compatibilité** | Composer `400` ou choisir l'option 3 | ❌ À configurer |
| 7 | **Consulter son solde** | Composer `600` — le solde est annoncé vocalement | ❌ À configurer |
| 8 | **Recharger son crédit** | Composer `700` — saisir un token pour créditer le compte | ❌ À configurer |
| 9 | **Participer à une conférence** | Composer `500` — rejoindre une salle MeetMe | ❌ À configurer |
| 10 | **Être facturé en temps réel** | Le compteur décompte chaque seconde et débite le solde | ✅ Backend prêt |
| 11 | **Être coupé si solde épuisé** | Le backend envoie un Hangup via AMI | ✅ Backend prêt |

## 2. Fonctionnalités Administrateur (Interface Web)

| # | Fonctionnalité | Description | Statut |
|---|----------------|-------------|--------|
| 12 | **Se connecter** | Authentification admin (JWT) | ✅ Prêt |
| 13 | **Voir le tableau de bord** | Indicateurs clés (appels, revenus, utilisateurs) | ✅ Prêt |
| 14 | **Gérer les utilisateurs** | Créer, modifier, supprimer des utilisateurs | ✅ Prêt |
| 15 | **Attribuer un sip_id** | Lier l'utilisateur à son extension Asterisk (1001, etc.) | ✅ Prêt |
| 16 | **Consulter les soldes** | Voir le solde de chaque utilisateur | ✅ Prêt |
| 17 | **Générer des tokens** | Créer des codes de recharge (1000, 2000, 5000 AR) | ✅ Prêt |
| 18 | **Voir les tokens** | Liste des tokens avec leur statut | ✅ Prêt |
| 19 | **Consulter les CDR** | Journal d'appels avec filtres | ✅ Prêt |
| 20 | **Exporter les CDR** | Export CSV | ✅ Prêt |
| 21 | **Voir les statistiques** | Graphiques (appels par jour, revenus, top destinations) | ✅ Prêt |
| 22 | **Filtrer par service** | Filtrer les CDR par destination (commercial, support...) | ⚠️ Partiel |

## 3. Fonctionnalités du Backend (API)

| # | Fonctionnalité | Description | Statut |
|---|----------------|-------------|--------|
| 23 | **API REST complète** | Endpoints pour utilisateurs, tokens, CDR, stats | ✅ Prêt |
| 24 | **Connexion AMI** | Écoute des événements Asterisk en temps réel | ✅ Fonctionnel |
| 25 | **Compteur temps réel** | Incrémente chaque seconde par appel actif | ✅ Prêt |
| 26 | **Vérification de solde avant appel** | Endpoint `/api/check_balance` appelé par AGI | ✅ Prêt |
| 27 | **Enregistrement CDR en fin d'appel** | Endpoint `/api/end_call` appelé par AGI | ✅ Prêt |
| 28 | **Coupure automatique** | Hangup via AMI si le solde est épuisé | ✅ Prêt |
| 29 | **Bootstrap admin/tarif** | Création auto de l'admin et du tarif par défaut | ✅ Prêt |

## 4. Fonctionnalités Système (Asterisk)

| # | Fonctionnalité | Description | Statut |
|---|----------------|-------------|--------|
| 30 | **Transport PJSIP** | Écoute sur le port 5060/UDP | ✅ Configuré |
| 31 | **Extensions SIP** | Comptes 1001-1004 pour Linphone | ⚠️ Configuré mais à vérifier |
| 32 | **Dialplan IVR** | Menu principal + services + conférence | ❌ À configurer |
| 33 | **Scripts AGI** | Vérification solde + enregistrement CDR | ✅ Installés |
| 34 | **AMI Manager** | Connexion avec le backend | ✅ Fonctionnel |
| 35 | **Fichiers audio** | Messages vocaux pour l'IVR | ❌ À créer |
| 36 | **Files d'attente (Queues)** | Gestion des appels commerciaux/support | ❌ À configurer |

## 5. Fonctionnalités de Déploiement

| # | Fonctionnalité | Description | Statut |
|---|----------------|-------------|--------|
| 37 | **Docker Compose** | Stack conteneurisée (PostgreSQL, API, Admin, Nginx) | ✅ Opérationnel |
| 38 | **Reverse proxy Nginx** | Routage par chemin vers API et Admin | ✅ Opérationnel |
| 39 | **Certbot (TLS)** | Prêt pour HTTPS plus tard | ✅ Configuré |
| 40 | **Pare-feu UFW** | Ports 80, 443, 4422, 5038 ouverts | ✅ Configuré |
| 41 | **Sauvegardes PostgreSQL** | Scripts de backup | ⚠️ À automatiser |

---

## Ce qui reste à faire (priorités)

| Priorité | Fonctionnalités | Complexité |
|----------|-----------------|------------|
| 🔴 Haute | Configuration du dialplan IVR (100, 200, 300, 400, 500, 600, 700) | Moyenne |
| 🔴 Haute | Tester les extensions PJSIP (voir pourquoi `pjsip show endpoints` est vide) | Simple |
| 🟡 Moyenne | Créer les fichiers audio du menu vocal | Simple |
| 🟡 Moyenne | Configurer les files d'attente (Queues) | Moyenne |
| 🟢 Basse | Tester avec Linphone | Simple |

---