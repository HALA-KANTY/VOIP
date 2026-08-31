Parfait ! Voici le cahier des charges complet des dernières fonctionnalités avec tous les détails techniques.

---

# Nouvelles Fonctionnalités — Spécifications pour l'Agent IA

## 1. Synchronisation centralisée Asterisk via AMI

### Contexte
Remplacer les scripts shell externes par une synchronisation directe via AMI depuis le backend.

### Fichiers à créer/modifier

| Fichier | Action |
|---------|--------|
| `backend/app/services/synchronisation.py` | Créer |
| `backend/app/api/utilisateurs.py` | Modifier |
| `backend/app/services/gestion_queues.py` | Déjà créé |
| `backend/app/services/gestion_voicemail.py` | Créer |

### Détails

**`synchronisation.py`** — Service centralisé :

```python
async def recharger_asterisk(module: str) -> bool:
    """Envoie une commande de rechargement à Asterisk via AMI."""
    # module: "pjsip", "voicemail", "queue"
    # Connexion TCP brute à Asterisk
    # Login AMI → Command → Logoff
    # Retourne True/False

async def ecrire_et_recharger(chemin: Path, contenu: str, module: str) -> tuple[bool, str]:
    """Écrit un fichier et recharge le module Asterisk associé."""
```

**`gestion_voicemail.py`** — Génère `voicemail.conf` :

```python
async def generer_voicemail_conf(db: AsyncSession) -> str:
    """Génère le fichier voicemail.conf avec les boîtes vocales."""
    # Format : sip_id => PIN,nom_complet,email
    # PIN par défaut : 4 derniers chiffres du sip_id

async def ecrire_voicemail(db: AsyncSession) -> None:
    """Écrit le fichier voicemail.conf sur le disque."""
```

**`utilisateurs.py`** — Après chaque CRUD :

```python
async def _synchroniser_asterisk(db: AsyncSession) -> None:
    """Synchronise PJSIP, les files d'attente et la messagerie vocale."""
    # 1. Générer extensions_ivr.conf
    # 2. Générer pjsip_users.conf → recharger pjsip
    # 3. Générer queues.conf → recharger queue
    # 4. Générer voicemail.conf → recharger voicemail
```

---

## 2. Appels vers les services IVR — GRATUITS

### Règle métier
Les appels vers les services IVR (`1001#`, `1002#`, `1003#`, `1004*`) **ne débitent pas** le solde de l'appelant. Le CDR est enregistré avec `cout = 0`.

### Modification dans `enregistrer_appel.py`

```python
# Si la destination est un service IVR (commence par "100"), ne pas débiter
if destination.startswith("100"):
    cout_facture = 0
else:
    cout_facture = min(cout_calcule, utilisateur.solde)
```

### Modification dans `ami_endpoints.py` — `end_call`

Ajouter la logique :

```python
# Si la destination est un service IVR, le coût est 0
EST_SERVICE_IVR = payload.destination.startswith("100")
if EST_SERVICE_IVR:
    cout_facture = Decimal("0")
else:
    cout_facture = min(cout_calcule, utilisateur.solde)
```

---

## 3. Messagerie vocale automatique

### Comportement

| Scénario | Action |
|----------|--------|
| Appel poste à poste (_2XXX) → pas de réponse | → Message + bip → enregistrement |
| Appel service IVR (queue) → agent non joignable | → Message + bip → enregistrement |
| Menu IVR (100) → touche "écouter messages" | → VoicemailMain |

### Fichiers audio à générer (ElevenLabs)

| Fichier | Texte |
|---------|-------|
| `message-bip.wav` | « La personne est injoignable. Veuillez laisser un message après le bip sonore. » |
| `agent-occupe.wav` | « Tous nos agents sont actuellement occupés. Veuillez laisser un message après le bip sonore. » |

### Dialplan à modifier

**Poste à poste (_2XXX)** :
```asterisk
 same => n,Dial(PJSIP/${EXTEN},60)
 same => n,GotoIf($["${DIALSTATUS}" = "NOANSWER"]?voicemail:fin)
 same => n(voicemail),Playback(custom/message-bip)
 same => n,Voicemail(${EXTEN}@voip-billing)
 same => n,Hangup()
```

**Services IVR (générateur)** :
```asterisk
 same => n(autorise),Queue(commercial_queue)
 same => n,GotoIf($["${QUEUESTATUS}" = "TIMEOUT"]?voicemail:fin)
 same => n(voicemail),Playback(custom/agent-occupe)
 same => n,Voicemail(commercial@voip-billing)
```

**Menu IVR (100)** :
```asterisk
; Ajouter l'option 5 pour écouter les messages
exten => 5,1,VoicemailMain(${CALLERID(num)}@voip-billing)
```

---

## 4. Sous-menu IVR Commercial — Achat de crédit

### Nouveau flux

```
Client compose 1001# (Service Commercial)
    ↓
"Tapez 1 pour acheter du crédit"
"Tapez 2 pour parler à un agent"
"Tapez 3 pour revenir au menu principal"
    ↓
Si Tape 1 (Achat)
    ↓
"Tapez 1 pour 500 AR"
"Tapez 2 pour 1000 AR"
"Tapez 3 pour 2000 AR"
"Tapez 4 pour 5000 AR"
    ↓
Le client choisit un montant
    ↓
Le backend génère un token du montant
    ↓
Le code est lu vocalement
"Votre code de recharge est : 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6"
```

### Fichiers audio à générer (ElevenLabs)

| Fichier | Texte |
|---------|-------|
| `menu-commercial.wav` | « Bienvenue au service commercial. Tapez 1 pour acheter du crédit, Tapez 2 pour parler à un agent. » |
| `choisir-montant.wav` | « Choisissez votre montant : Tapez 1 pour 500 Ariary, Tapez 2 pour 1000 Ariary, Tapez 3 pour 2000 Ariary, Tapez 4 pour 5000 Ariary. » |
| `votre-code.wav` | « Votre code de recharge est : » |

### Backend — Nouvel endpoint

`POST /api/ivr/acheter_credit` :

```python
class AchatCreditRequest(BaseModel):
    sip_id: str
    montant: Decimal

class AchatCreditResponse(BaseModel):
    code_token: str
    montant: Decimal
    message: str
```

**Logique** :
1. Vérifier que l'utilisateur existe et est actif
2. Générer un token numérique à 16 chiffres
3. Sauvegarder le token en base (statut `non_utilise`)
4. Retourner le code pour lecture vocale
5. **Ne PAS créditer le solde** — le client devra composer `700CODE#` pour recharger

---

## 5. Affichage du type d'utilisateur dans la liste

### Frontend — `UserTable.tsx`

Ajouter une colonne "Type" avec badge coloré :

```tsx
{/* Badge type */}
<td className="py-3 pr-4">
  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
    u.type_utilisateur === "commercial" ? "bg-blue-500/10 text-blue-400" :
    u.type_utilisateur === "support" ? "bg-green-500/10 text-green-400" :
    u.type_utilisateur === "comptabilite" ? "bg-yellow-500/10 text-yellow-400" :
    "bg-gray-500/10 text-gray-400"
  }`}>
    {u.type_utilisateur}
  </span>
</td>
```

---

## Résume

| # | Fonctionnalité | Fichiers à modifier |
|---|----------------|---------------------|
| 1 | Synchronisation AMI centralisée | `synchronisation.py`, `utilisateurs.py` |
| 2 | Appels services gratuits | `enregistrer_appel.py`, `ami_endpoints.py` |
| 3 | Messagerie vocale auto | `gestion_voicemail.py`, `generateur_dialplan.py`, `extensions.conf` |
| 4 | Sous-menu IVR Commercial | `generateur_dialplan.py`, nouvel endpoint |
| 5 | Type utilisateur dans liste | `UserTable.tsx` |

---