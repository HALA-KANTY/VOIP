import random
import string
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verifier_secret_ami
from app.config import settings
from app.domain.billing import calculer_cout, secondes_avant_epuisement, crediter
from app.infrastructure.database.models import CDR, ServiceIVR, Tarif, Utilisateur, Rechargement, Token
from app.services.synchronisation import recharger_asterisk


router = APIRouter(prefix="/api", tags=["ami"], dependencies=[Depends(verifier_secret_ami)])

class CheckBalanceResponse(BaseModel):
    utilisateur_id: int
    sip_id: str | None
    solde: Decimal
    tarif_par_seconde: Decimal
    secondes_disponibles: int
    autorise: bool


class EndCallRequest(BaseModel):
    channel: str
    sip_id: str
    duree: int
    destination: str
    statut: str = "termine"
    type_connexion: str = "sip"


class EndCallResponse(BaseModel):
    cdr_id: int
    cout_facture: Decimal
    solde_restant: Decimal

class RechargeRequest(BaseModel):
    sip_id: str
    token: str


class RechargeResponse(BaseModel):
    succes: bool
    message: str
    nouveau_solde: Decimal

class PjsipSyncResponse(BaseModel):
    succes: bool
    message: str
    utilisateurs_exportes: int


class AchatCreditRequest(BaseModel):
    sip_id: str
    montant: Decimal


class AchatCreditResponse(BaseModel):
    code_token: str
    montant: Decimal
    message: str

async def _tarif_actif(db: AsyncSession) -> Decimal:
    result = await db.execute(select(Tarif).where(Tarif.actif.is_(True)))
    tarif = result.scalars().first()
    return tarif.montant_par_seconde if tarif is not None else settings.TARIF_DEFAUT


async def _utilisateur_par_sip_id(sip_id: str, db: AsyncSession) -> Utilisateur:
    """Asterisk ne connait que l'extension SIP appelante (CALLERID(num)), pas notre id interne."""
    result = await db.execute(select(Utilisateur).where(Utilisateur.sip_id == sip_id))
    utilisateur = result.scalar_one_or_none()
    if utilisateur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable pour ce sip_id")
    return utilisateur


# Destinations utilitaires (extensions-billing.conf : *600# et 700+code#) :
# operations administratives sur son propre compte, jamais des appels a
# valeur ajoutee -- les facturer n'aurait aucun sens (payer pour recharger
# son solde, ou pour verifier combien il en reste).
_DESTINATIONS_UTILITAIRES_GRATUITES = {"SOLDE-600", "RECHARGE-700"}


async def _est_appel_gratuit(destination: str, db: AsyncSession) -> bool:
    """
    Tout appel vers le menu IVR (destination commencant par "100" : 1001#,
    1002#, 1003#, 1004*), y compris le transfert vers un agent, est gratuit --
    sauf la conference (type "conf"), qui reste facturee. Seuls les appels
    poste a poste (_2XXX) et la conference sont factures.
    """
    if destination in _DESTINATIONS_UTILITAIRES_GRATUITES:
        return True
    if not destination.startswith("100"):
        return False
    result = await db.execute(select(ServiceIVR).where(ServiceIVR.code == destination))
    service = result.scalar_one_or_none()
    return service is None or service.type != "conf"


@router.get("/check_balance", response_model=CheckBalanceResponse)
async def check_balance(sip_id: str, db: AsyncSession = Depends(get_db)) -> CheckBalanceResponse:
    utilisateur = await _utilisateur_par_sip_id(sip_id, db)

    tarif = await _tarif_actif(db)
    autorise = utilisateur.statut == "actif" and utilisateur.solde >= tarif

    return CheckBalanceResponse(
        utilisateur_id=utilisateur.id,
        sip_id=utilisateur.sip_id,
        solde=utilisateur.solde,
        tarif_par_seconde=tarif,
        secondes_disponibles=secondes_avant_epuisement(utilisateur.solde, tarif) if tarif > 0 else 0,
        autorise=autorise,
    )


@router.post("/end_call", response_model=EndCallResponse)
async def end_call(payload: EndCallRequest, db: AsyncSession = Depends(get_db)) -> EndCallResponse:
    """
    Enregistre le CDR et debite le solde de facon atomique. Le cout facture est
    plafonne au solde disponible : le CompteurManager est charge de couper l'appel
    avant depassement, mais on se protege ici contre tout ecart de duree remonte
    par Asterisk pour ne jamais faire passer un solde sous zero.
    """
    utilisateur = await _utilisateur_par_sip_id(payload.sip_id, db)

    if await _est_appel_gratuit(payload.destination, db):
        cout_facture = Decimal("0")
    else:
        tarif = await _tarif_actif(db)
        cout_calcule = calculer_cout(payload.duree, tarif)
        cout_facture = min(cout_calcule, utilisateur.solde)

    utilisateur.solde -= cout_facture
    cdr = CDR(
        utilisateur_id=utilisateur.id,
        duree=payload.duree,
        destination=payload.destination,
        cout=cout_facture,
        statut=payload.statut,
        type_connexion=payload.type_connexion,
    )
    db.add(cdr)
    await db.commit()
    await db.refresh(cdr)

    return EndCallResponse(cdr_id=cdr.id, cout_facture=cout_facture, solde_restant=utilisateur.solde)


def _nettoyer_pour_conf(valeur: str) -> str:
    """Empeche une valeur admin (nom complet) de casser la syntaxe pjsip.conf."""
    return valeur.replace('"', "").replace("\r", "").replace("\n", "")


@router.post("/recharge", response_model=RechargeResponse)
async def recharger_solde(payload: RechargeRequest, db: AsyncSession = Depends(get_db)) -> RechargeResponse:
    """
    Recharge le solde d'un utilisateur via un token saisi au telephone (DTMF).
    Appelé par le script AGI recharger_solde.py côté Asterisk.
    """
    utilisateur = await _utilisateur_par_sip_id(payload.sip_id, db)

    result = await db.execute(select(Token).where(Token.code == payload.token))
    token = result.scalar_one_or_none()
    if token is None:
        return RechargeResponse(succes=False, message="Token introuvable", nouveau_solde=utilisateur.solde)
    if token.statut == "utilise":
        return RechargeResponse(succes=False, message="Ce token a deja ete utilise", nouveau_solde=utilisateur.solde)

    utilisateur.solde = crediter(utilisateur.solde, token.montant)
    token.statut = "utilise"
    token.date_utilisation = datetime.now(timezone.utc).replace(tzinfo=None)

    rechargement = Rechargement(utilisateur_id=utilisateur.id, token_id=token.id, montant=token.montant)
    db.add(rechargement)
    await db.commit()

    return RechargeResponse(succes=True, message="Recharge effectuee", nouveau_solde=utilisateur.solde)


def _generer_code_token() -> str:
    generateur = random.SystemRandom()
    return "".join(generateur.choice(string.digits) for _ in range(12))


@router.post("/ivr/acheter_credit", response_model=AchatCreditResponse)
async def acheter_credit(payload: AchatCreditRequest, db: AsyncSession = Depends(get_db)) -> AchatCreditResponse:
    """
    Genere un token de recharge depuis le sous-menu IVR commercial (voir
    asterisk-integration/agi-bin/acheter_credit.py). Le solde n'est PAS
    credite ici : le client doit composer 700+CODE# pour recharger, comme
    pour un token achete par un autre canal.
    """
    utilisateur = await _utilisateur_par_sip_id(payload.sip_id, db)
    if utilisateur.statut != "actif":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte inactif")

    code = _generer_code_token()
    while (await db.execute(select(Token).where(Token.code == code))).scalar_one_or_none() is not None:
        code = _generer_code_token()

    token = Token(code=code, montant=payload.montant)
    db.add(token)
    await db.commit()
    await db.refresh(token)

    return AchatCreditResponse(
        code_token=code,
        montant=token.montant,
        message=f"Token de {token.montant} Ar genere pour {payload.sip_id}",
    )


@router.get("/pjsip_export", response_class=PlainTextResponse)
async def exporter_pjsip(db: AsyncSession = Depends(get_db)) -> str:
    """
    Genere les blocs pjsip.conf (endpoint/auth/aor) pour tous les utilisateurs
    actifs ayant un sip_id + sip_secret. A appeler depuis un script cote
    Asterisk (voir asterisk-integration/sync_pjsip.sh) qui ecrit le resultat
    dans un fichier inclus par pjsip.conf, puis recharge.

    Un utilisateur suspendu/inactif disparait de cet export : son poste SIP
    est desactive au prochain sync, sans action manuelle cote Asterisk.
    """
    result = await db.execute(
        select(Utilisateur)
        .where(Utilisateur.sip_id.is_not(None))
        .where(Utilisateur.sip_secret.is_not(None))
        .where(Utilisateur.statut == "actif")
        .order_by(Utilisateur.sip_id)
    )
    utilisateurs = result.scalars().all()

    blocs = [
        "; Fichier genere automatiquement par GET /api/pjsip_export -- ne pas editer a la main.\n"
        "; Source de verite : l'interface admin (utilisateurs avec un sip_id).\n"
    ]
    for utilisateur in utilisateurs:
        nom = _nettoyer_pour_conf(utilisateur.nom_complet)
        blocs.append(
            f"[{utilisateur.sip_id}](endpoint-template)\n"
            f"auth = {utilisateur.sip_id}\n"
            f"aors = {utilisateur.sip_id}\n"
            f'callerid = "{nom}" <{utilisateur.sip_id}>\n'
            # MWI : Linphone affiche un indicateur (icone/tonalite) des qu'un
            # message vocal arrive dans cette boite, sans avoir a composer le 100.
            f"mailboxes = {utilisateur.sip_id}@voip-billing\n\n"
            f"[{utilisateur.sip_id}](auth-template)\n"
            f"username = {utilisateur.sip_id}\n"
            f"password = {utilisateur.sip_secret}\n\n"
            f"[{utilisateur.sip_id}](aor-template)\n"
        )
    return "\n".join(blocs)


@router.post("/pjsip_sync", response_model=PjsipSyncResponse)
async def synchroniser_pjsip(db: AsyncSession = Depends(get_db)) -> PjsipSyncResponse:
    """
    Génère pjsip_users.conf et force Asterisk à recharger sa configuration
    instantanément, en reutilisant la connexion AMI standard (memes
    identifiants que le reste de l'application, cf ASTERISK_AMI_USER).
    """
    contenu = await exporter_pjsip(db)
    chemin = Path(settings.ASTERISK_CONFIG_DIR) / "pjsip_users.conf"

    try:
        chemin.write_text(contenu, encoding="utf-8")
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impossible d'écrire le fichier sur le disque partagé : {e}",
        )

    succes = await recharger_asterisk("pjsip")
    message = (
        "Fichier synchronisé et module PJSIP rechargé avec succès via AMI"
        if succes
        else "Fichier écrit, mais échec du rechargement automatique Asterisk (verifier la connexion AMI)"
    )

    total_utilisateurs = len(contenu.split("[")) - 1

    return PjsipSyncResponse(succes=succes, message=message, utilisateurs_exportes=total_utilisateurs)

