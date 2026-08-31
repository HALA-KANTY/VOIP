# Cahier des Charges — Backend API & Interface d'Administration

## Plateforme VoIP avec Billing Prépayé

---

## 1. Contexte du Projet

Développement d'une plateforme VoIP complète avec :
- **Serveur VoIP** : Asterisk (géré séparément)
- **Client SIP** : Linphone (application externe)
- **Backend API** : FastAPI (à développer)
- **Base de données** : PostgreSQL (déjà configurée)
- **Interface d'administration** : Application Web (à développer)

---

## 2. Architecture Générale

```
┌─────────────────────────────────────────────────────────────────┐
│                    UTILISATEUR (Linphone)                       │
└──────────────────────────┬───────────────────────────────────────┘
                         │ SIP
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVEUR ASTERISK                             │
│                    (déjà configuré)                             │
└──────────────────────────┬───────────────────────────────────────┘
                         │ AMI (Asterisk Manager Interface)
                         │ Événements en temps réel
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API BACKEND (FastAPI)                        │
│                    (à développer)                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Domain      │  │  Infra: AMI  │  │  Infra: DB   │          │
│  │  (billing,   │  │  (AMI client,│  │  (SQLAlchemy,│          │
│  │  compteur)   │  │  actions)    │  │  session)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  API         │  │  Schémas     │                            │
│  │  (Routers)   │  │  Pydantic    │                            │
│  └──────────────┘  └──────────────┘                            │
└──────────────────────────┬───────────────────────────────────────┘
                         │ SQLAlchemy
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BASE DE DONNÉES (PostgreSQL)                 │
│                    (déjà configurée)                             │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTERFACE ADMIN (Web)                        │
│                    (à développer)                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │  Utilisateurs│  │  Tokens      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CDR         │  │  Statistiques│  │  Export      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Technologies Requises

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Backend API** | FastAPI | ≥ 0.104 |
| **ORM** | SQLAlchemy | ≥ 2.0 |
| **Base de données** | PostgreSQL | 15 |
| **Driver PostgreSQL** | asyncpg | ≥ 0.29 |
| **Validation** | Pydantic | ≥ 2.5 |
| **Client AMI** | asterisk-ami | ≥ 0.1 |
| **Frontend** | Next.js (App Router) | ≥ 14 |
| **UI** | React | ≥ 18 |
| **Styles** | Tailwind CSS | ≥ 3.4 |
| **Graphiques** | Recharts | ≥ 2.10 |
| **HTTP Client** | Axios | ≥ 1.6 |
| **Langage** | Python | 3.11 |
| **Langage Frontend** | TypeScript | ≥ 5 |

---

## 4. Structure du Projet Backend

L'architecture backend est organisée en **quatre couches clairement séparées**, afin que la logique métier (billing, compteur) reste testable indépendamment de l'infrastructure (base de données, AMI) :

- **`api/`** — Routers FastAPI : uniquement les préoccupations HTTP (requêtes/réponses, codes de statut, injection de dépendances). Ne contient aucune logique métier.
- **`domain/`** — Logique métier pure (calcul de facturation, règles du compteur temps réel). Aucune dépendance vers SQLAlchemy ou le client AMI : testable unitairement avec de simples mocks.
- **`infrastructure/`** — Intégrations externes : le client AMI (connexion, écoute d'événements, reconnexion, actions comme Hangup) et la persistance (SQLAlchemy : session, modèles). Si le protocole Asterisk change, seul ce dossier est impacté.
- **`schemas/`** — DTOs Pydantic (validation des entrées/sorties de l'API).

```
backend/
├── Dockerfile
├── requirements.txt
├── .env.example
├── main.py                          # Point d'entrée FastAPI
│
├── app/
│   ├── __init__.py
│   ├── config.py                    # Configuration (DB, AMI, JWT, etc.)
│   ├── security.py                  # Auth JWT, hachage bcrypt, dépendances FastAPI
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                  # Dépendances communes (DB session, current_user)
│   │   ├── auth.py                  # Login admin
│   │   ├── utilisateurs.py          # CRUD utilisateurs
│   │   ├── cdr.py                   # Journal d'appels
│   │   ├── tokens.py                # Génération de tokens
│   │   ├── rechargements.py         # Rechargement par token
│   │   ├── statistiques.py          # Statistiques
│   │   └── ami_endpoints.py         # Endpoints appelés par Asterisk (check_balance, end_call)
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── billing.py               # Calcul de coût, débit/crédit (logique pure)
│   │   └── compteur.py              # Gestionnaire de compteurs temps réel
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── ami/
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # Connexion AMI, écoute d'événements, reconnexion
│   │   │   └── actions.py           # Actions AMI (Hangup, etc.)
│   │   └── database/
│   │       ├── __init__.py
│   │       ├── session.py           # Connexion PostgreSQL (async)
│   │       └── models.py            # Modèles SQLAlchemy
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── utilisateur.py           # Schémas Pydantic
│       ├── cdr.py
│       ├── token.py
│       ├── rechargement.py
│       ├── statistique.py
│       └── auth.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_utilisateurs.py
    ├── test_billing.py
    ├── test_tokens.py
    ├── test_compteur.py
    └── test_ami.py
```

---

## 5. Structure du Projet Frontend (Admin)

Interface construite avec **Next.js (App Router) + TypeScript + Tailwind CSS**, thème sombre "industriel" (fond quasi noir, cartes gris foncé, accent orange), inspiré de la maquette fournie dans `image/`. Les pages sous `(dashboard)/` sont protégées par un contrôle du token JWT côté client (le backend expose un JWT bearer, pas un cookie de session) ; elles appellent directement l'API FastAPI via Axios (CORS déjà configuré côté backend).

```
admin_web/
├── Dockerfile
├── package.json
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── .env.local.example             # NEXT_PUBLIC_API_URL
│
└── src/
    ├── app/
    │   ├── layout.tsx              # Layout racine (police, thème)
    │   ├── globals.css             # Design tokens (couleurs, dark theme)
    │   ├── login/page.tsx          # Authentification admin
    │   └── (dashboard)/
    │       ├── layout.tsx          # Sidebar + Header + garde d'authentification
    │       ├── page.tsx            # Dashboard
    │       ├── utilisateurs/page.tsx
    │       ├── tokens/page.tsx
    │       ├── cdr/page.tsx
    │       └── statistiques/page.tsx
    │
    ├── components/
    │   ├── layout/                 # Sidebar, Header
    │   ├── ui/                     # KpiCard, Badge, Card, Modal, DataTable
    │   ├── charts/                 # Graphiques Recharts (revenus, destinations)
    │   ├── users/                  # Table + formulaire utilisateurs
    │   ├── tokens/                 # Table + génération de tokens
    │   └── cdr/                    # Table, filtres, export CSV
    │
    ├── context/
    │   └── AuthContext.tsx         # Etat d'authentification (token JWT)
    │
    └── lib/
        ├── api.ts                  # Client Axios + intercepteur JWT
        └── types.ts                # Types TS miroir des schémas Pydantic
```

---

## 6. Modèles de Données (SQLAlchemy)

### 6.1 Table `Utilisateur`

```python
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nom_complet = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    solde = Column(Numeric(10,2), default=0)
    statut = Column(String(20), default="actif")  # actif, inactif, suspendu
    sip_id = Column(String(10), unique=True)  # 1001, 1002, etc.
    sip_secret = Column(String(64))  # mot de passe SIP (Linphone), genere automatiquement
    date_creation = Column(DateTime, default=datetime.now)
```

`sip_secret` est généré automatiquement dès qu'un `sip_id` est renseigné (si non
fourni explicitement), et exposé par l'API à l'admin (pas à l'utilisateur
final) pour configurer Linphone. Distinct de `password_hash`, qui sert
uniquement à l'authentification sur l'interface admin. Voir
`asterisk-integration/README.md` et `GET /api/pjsip_export` (§7.6) pour la
synchronisation vers Asterisk.

### 6.2 Table `CDR`

```python
class CDR(Base):
    __tablename__ = "cdr"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    date_appel = Column(DateTime, nullable=False, default=datetime.now)
    duree = Column(Integer, nullable=False)  # en secondes
    destination = Column(String(50), nullable=False)  # numéro ou service
    cout = Column(Numeric(10,2), nullable=False)
    statut = Column(String(20), default="termine")  # termine, echoue, coupe
    type_connexion = Column(String(20), default="sip")  # sip, webrtc
```

### 6.3 Table `Token`

```python
class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    montant = Column(Numeric(10,2), nullable=False)
    statut = Column(String(20), default="non_utilise")  # non_utilise, utilise
    date_creation = Column(DateTime, default=datetime.now)
    date_utilisation = Column(DateTime)
```

### 6.4 Table `Rechargement`

```python
class Rechargement(Base):
    __tablename__ = "rechargements"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    token_id = Column(Integer, ForeignKey("tokens.id"))
    montant = Column(Numeric(10,2), nullable=False)
    date_rechargement = Column(DateTime, default=datetime.now)
```

### 6.5 Table `Tarif`

```python
class Tarif(Base):
    __tablename__ = "tarifs"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(100))
    montant_par_seconde = Column(Numeric(10,2), default=1.0)
    actif = Column(Boolean, default=True)
```

---

## 7. API REST — Endpoints

### 7.1 Utilisateurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/utilisateurs` | Liste tous les utilisateurs |
| GET | `/api/utilisateurs/{id}` | Détails d'un utilisateur |
| POST | `/api/utilisateurs` | Créer un utilisateur |
| PUT | `/api/utilisateurs/{id}` | Modifier un utilisateur |
| DELETE | `/api/utilisateurs/{id}` | Supprimer un utilisateur |
| GET | `/api/utilisateurs/{id}/solde` | Consulter le solde |
| POST | `/api/utilisateurs/{id}/crediter` | Créditer le solde |
| POST | `/api/utilisateurs/{id}/debiter` | Débiter le solde |

### 7.2 CDR

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/cdr` | Liste des appels (avec filtres) |
| GET | `/api/cdr/{id}` | Détails d'un appel |
| GET | `/api/cdr/export` | Export CSV/PDF |

**Paramètres de filtre pour GET `/api/cdr` :**
- `date_debut` : Date de début
- `date_fin` : Date de fin
- `utilisateur_id` : Filtre par utilisateur
- `destination` : Filtre par destination
- `duree_min` : Durée minimale
- `duree_max` : Durée maximale
- `cout_min` : Coût minimal
- `cout_max` : Coût maximal

### 7.3 Tokens

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/tokens` | Liste des tokens |
| POST | `/api/tokens/generer` | Générer un token |
| GET | `/api/tokens/{code}` | Vérifier un token |
| POST | `/api/tokens/valider` | Valider et utiliser un token |

### 7.4 Rechargements

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/rechargements` | Liste des rechargements |
| POST | `/api/rechargements` | Effectuer un rechargement |

### 7.5 Statistiques

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/statistiques/appels` | Statistiques des appels |
| GET | `/api/statistiques/revenus` | Revenus par période |
| GET | `/api/statistiques/utilisateurs` | Statistiques des utilisateurs |
| GET | `/api/statistiques/destinations` | Top destinations |

### 7.6 Endpoints AMI (appelés par Asterisk)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/check_balance?sip_id={sip_id}` | Vérifier le solde avant appel |
| POST | `/api/end_call` | Fin d'appel (durée, coût) |
| GET | `/api/pjsip_export` | Export texte (format pjsip.conf) des postes actifs, pour synchronisation vers Asterisk |

Identifiés par `sip_id` (l'extension, ex. `1001`) et non par l'id interne : c'est la seule information dont dispose le dialplan Asterisk au moment de l'appel (`CALLERID(num)`). Protégés par l'en-tête `X-AMI-Secret` (voir `AMI_ENDPOINTS_SECRET`), pas par JWT — voir `DEPLOYMENT.md` pour l'intégration dialplan complète.

---

## 8. Logique Métier — Billing

### 8.1 Tarification

- **Tarif par défaut** : 1 AR/seconde
- **Calcul du coût** : `coût = durée (secondes) × tarif (AR/seconde)`
- **Solde insuffisant** : L'appel est refusé ou coupé

### 8.2 Compteur Temps Réel

```python
class CompteurManager:
    """
    Gère les compteurs synchronisés avec le tarif.

    Pour chaque appel actif :
    - Un compteur incrémente chaque seconde
    - Au seuil critique (solde / tarif - 1), on vérifie le solde réel
    - Si le solde est épuisé, on coupe l'appel via AMI
    """

    compteurs_actifs = {}  # Dictionnaire des compteurs en mémoire

    async def demarrer_compteur(self, channel_id, user_id):
        """
        Démarre le compteur lors d'un nouvel appel
        """
        pass

    async def boucle_compteur(self, channel_id, user_id, solde, tarif):
        """
        Boucle asynchrone qui incrémente chaque seconde
        """
        pass

    async def arreter_compteur(self, channel_id):
        """
        Arrête le compteur et enregistre le CDR
        """
        pass
```

### 8.3 Gestionnaire AMI

```python
class AMIManager:
    """
    Gère la connexion AMI avec Asterisk.
    Écoute les événements en continu.
    """

    async def connect(self):
        """
        Établit la connexion AMI
        """
        pass

    async def listen(self):
        """
        Écoute les événements AMI en continu
        """
        pass

    async def handle_event(self, event):
        """
        Délègue l'événement au gestionnaire approprié
        """
        pass
```

### 8.4 Événements AMI à gérer

| Événement | Action |
|-----------|--------|
| `Newchannel` | Démarrer le compteur |
| `BridgeEnter` | Activer le compteur |
| `BridgeLeave` | Désactiver le compteur |
| `Hangup` | Arrêter le compteur, enregistrer CDR |

---

## 9. Interface d'Administration

### 9.1 Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Vue d'ensemble : nombre d'appels, revenus, utilisateurs actifs |
| **Utilisateurs** | CRUD complet, consultation du solde |
| **Tokens** | Génération, liste, état |
| **CDR** | Journal d'appels avec filtres |
| **Statistiques** | Graphiques et tableaux |
| **Export** | Export CSV/PDF |

### 9.2 Fonctionnalités

- Authentification admin
- Tableau de bord avec indicateurs clés
- Filtres de recherche avancés
- Graphiques (barres, lignes, camembert)
- Export CSV
- Interface responsive
- Messages de confirmation/erreur

### 9.3 Design

- **Thème** : Sombre ou clair (au choix)
- **Couleurs** : Bleu (#2563eb) pour les accents
- **Police** : Inter ou system-ui
- **Layout** : Sidebar + Header + Contenu

---

## 10. Sécurité

| Élément | Exigence |
|---------|----------|
| **Authentification API** | JWT (JSON Web Token) |
| **Authentification Admin** | Login/mot de passe avec JWT |
| **Hachage des mots de passe** | bcrypt |
| **CORS** | Configuré pour le domaine admin |
| **Validation** | Pydantic pour toutes les entrées |
| **Protection** | Rate limiting sur les endpoints sensibles |

---

## 11. Variables d'Environnement

Créez le fichier `.env.example` :

```env
# Base de données
DATABASE_URL=postgresql://voip_user:voip_password_secure@postgres:5432/voip_billing

# Asterisk AMI
ASTERISK_AMI_HOST=asterisk
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=fastapi
ASTERISK_AMI_SECRET=motdepasse_ami_fastapi

# JWT
JWT_SECRET_KEY=votre_cle_secrete
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Tarification
TARIF_DEFAUT=1.0
```

---

## 12. Tests Requis

| Test | Description |
|------|-------------|
| `test_utilisateurs.py` | CRUD utilisateurs |
| `test_billing.py` | Calcul du coût, débit/crédit |
| `test_tokens.py` | Génération et validation de tokens |
| `test_compteur.py` | Logique du compteur temps réel |
| `test_ami.py` | Gestion des événements AMI |

---

## 13. Contraintes Techniques

| Contrainte | Exigence |
|------------|----------|
| **Performance** | Temps de réponse API < 200ms |
| **Asynchrone** | Toutes les opérations DB en asynchrone |
| **Typage** | Pydantic pour tous les schémas |
| **Documentation** | Swagger UI automatique |
| **Code** | Commentaires en français ou anglais |
| **PEP 8** | Respect des conventions Python |

---

## 14. Livrables Attendus

1. **Code source complet** du backend FastAPI
2. **Code source complet** de l'interface admin React
3. **Fichiers Dockerfile** pour chaque service
4. **Fichier `requirements.txt`** avec toutes les dépendances
5. **Fichier `package.json`** avec toutes les dépendances frontend
6. **Documentation API** (Swagger UI)
7. **Tests unitaires**
8. **Fichier `.env.example`**

---

## 15. Critères de Validation

| Critère | Validation |
|---------|------------|
| **API démarre** | `uvicorn main:app --reload` fonctionne |
| **Swagger accessible** | `http://localhost:8000/docs` fonctionne |
| **CRUD utilisateurs** | Tous les endpoints fonctionnent |
| **Billing** | Le calcul du coût est correct |
| **Tokens** | La génération et validation fonctionnent |
| **Compteur** | Le compteur temps réel fonctionne |
| **AMI** | Les événements sont reçus et traités |
| **Interface admin** | Toutes les pages fonctionnent |

---

## 16. Points d'Attention

1. **Le compteur temps réel est critique** : Il doit être asynchrone et ne pas bloquer le reste de l'API.

2. **La connexion AMI doit être robuste** : Gérer la reconnexion en cas de perte.

3. **Les transactions SQL** : Le débit du solde et l'enregistrement CDR doivent être atomiques.

4. **La validation des tokens** : Un token ne peut être utilisé qu'une seule fois.

5. **Les filtres CDR** : Doivent être combinables (ET logique).

6. **L'export CSV** : Doit respecter le format UTF-8 avec BOM pour Excel.

---

## 17. Déploiement

La stack (PostgreSQL, backend, interface admin, nginx) est conteneurisée via
Docker Compose (`docker-compose.yml` à la racine) et déployée sur un serveur
Debian 13. La procédure complète — installation Docker, TLS/Let's Encrypt,
intégration Asterisk (compte AMI, scripts AGI, dialplan), configuration
Linphone côté client, sauvegardes, checklist sécurité — est documentée dans
[`DEPLOYMENT.md`](DEPLOYMENT.md). Les fichiers d'intégration Asterisk
(dialplan, scripts AGI) sont dans [`asterisk-integration/`](asterisk-integration/).

---
