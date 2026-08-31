import logging
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.api.monitoring import router as monitoring_router
from app.api.ami_endpoints import router as ami_router
from app.api.auth import router as auth_router
from app.api.cdr import router as cdr_router
from app.api.rechargements import router as rechargements_router
from app.api.statistiques import router as statistiques_router
from app.api.tokens import router as tokens_router
from app.api.utilisateurs import router as utilisateurs_router
from app.config import settings
from app.domain.compteur import CompteurManager
from app.infrastructure.ami.actions import raccrocher_canal
from app.infrastructure.ami.client import AMIClient
from app.infrastructure.database.models import Admin, Tarif, Utilisateur
from app.infrastructure.database.session import AsyncSessionLocal, init_db
from app.security import hash_password
from app.api.services_ivr import router as services_ivr_router
from app.api.tarifs import router as tarifs_router
from app.services.synchronisation import synchroniser_asterisk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


async def _bootstrap_donnees() -> None:
    """Cree l'admin par defaut et le tarif par defaut s'ils n'existent pas encore."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Admin).where(Admin.username == settings.ADMIN_USERNAME))
        if result.scalar_one_or_none() is None:
            db.add(Admin(username=settings.ADMIN_USERNAME, password_hash=hash_password(settings.ADMIN_PASSWORD)))
            logger.info("Admin par defaut '%s' cree", settings.ADMIN_USERNAME)

        result = await db.execute(select(Tarif).where(Tarif.actif.is_(True)))
        if result.scalars().first() is None:
            db.add(Tarif(description="Tarif par defaut", montant_par_seconde=settings.TARIF_DEFAUT, actif=True))
            logger.info("Tarif par defaut cree (%s/seconde)", settings.TARIF_DEFAUT)

        await db.commit()


async def _resynchroniser_asterisk_au_demarrage() -> None:
    """
    Regenere et pousse extensions_ivr.conf / pjsip_users.conf / queues.conf /
    voicemail.conf a chaque demarrage du backend.

    Sans cet appel, un changement de code cote generateur de dialplan (ex :
    nouvelle logique IVR) reste invisible pour Asterisk tant qu'aucune action
    admin sans rapport (creer/modifier un utilisateur ou un service IVR) ne
    declenche une resynchronisation -- le fichier reellement charge par
    Asterisk peut alors rester perime pendant des jours apres un deploiement.
    """
    async with AsyncSessionLocal() as db:
        try:
            await synchroniser_asterisk(db)
        except Exception:
            logger.exception("Echec de la resynchronisation Asterisk au demarrage")


async def _on_solde_epuise(channel_id: str, utilisateur_id: int) -> None:
    logger.warning("Solde epuise pour l'utilisateur %s, coupure du canal %s", utilisateur_id, channel_id)
    if app.state.ami_client.connecte:
        await raccrocher_canal(app.state.ami_client, channel_id)


async def _on_fin_appel(channel_id: str, utilisateur_id: int, duree: int, cout: Decimal) -> None:
    logger.info(
        "Fin d'appel channel=%s utilisateur=%s duree=%ss cout=%s", channel_id, utilisateur_id, duree, cout
    )


async def _recuperer_sip_id_appelant(channel: str) -> str | None:
    """Lit la variable de canal SIP_ID, posee par le dialplan (Set(SIP_ID=...))
    UNIQUEMENT sur le canal appelant, avant Dial()/Queue()/ConfBridge -- jamais
    propagee au(x) canal(aux) crees ensuite (agent, correspondant compose),
    puisque Set() sans prefixe underscore ne s'herite pas.

    BridgeEnter se declenche pour CHAQUE canal qui rejoint le pont (appelant
    ET appele), et CallerIDNum n'est pas fiable pour les distinguer -- sur ce
    paquet Asterisk, la jambe appelee peut se voir attribuer son propre
    sip_id comme CallerIDNum, ce qui facture/coupe alors l'appele au lieu de
    l'appelant (l'appelant PJSIP/2002 vers PJSIP/2001 avec 2001 a solde nul
    coupait l'appel apres 1s : le compteur avait demarre sur l'utilisateur
    2001 au lieu de 2002). Interroger SIP_ID via AMI Getvar est sans
    ambiguite : seul le canal appelant l'a jamais eu.
    """
    if not app.state.ami_client.connecte:
        return None
    try:
        reponse = await app.state.ami_client.envoyer_action(
            {"Action": "Getvar", "Channel": channel, "Variable": "SIP_ID"}
        )
    except (ConnectionError, TimeoutError):
        return None
    return reponse.get("Value") or None


async def _demarrer_compteur_pour_appel(channel: str, caller_id_num: str | None) -> None:
    if caller_id_num is None or app.state.compteur_manager.est_actif(channel):
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Utilisateur).where(Utilisateur.sip_id == caller_id_num))
        utilisateur = result.scalar_one_or_none()
        if utilisateur is None:
            return
        
        # Ne pas facturer les agents (ils reçoivent des appels, n'en passent pas)
        if utilisateur.type_utilisateur in ("commercial", "support", "comptabilite"):
            return
        
        result = await db.execute(select(Tarif).where(Tarif.actif.is_(True)))
        tarif = result.scalars().first()
        tarif_par_seconde = tarif.montant_par_seconde if tarif is not None else settings.TARIF_DEFAUT

    app.state.compteur_manager.demarrer_compteur(channel, utilisateur.id, utilisateur.solde, tarif_par_seconde)


async def _on_ami_event(event: dict) -> None:
    """Delegue les evenements AMI au CompteurManager selon le type d'evenement.

    Le compteur demarre a BridgeEnter (appel effectivement decroche) plutot qu'a
    Newchannel, pour ne pas facturer la sonnerie. BridgeLeave (mise en attente)
    n'est pas gere : le compteur continue de tourner tant que le canal n'a pas
    raccroche, ce qui est acceptable pour une plateforme sans transfert/attente
    complexe.
    """
    nom_evenement = event.get("Event")
    channel = event.get("Channel")
    if channel is None:
        return

    if nom_evenement == "BridgeEnter":
        sip_id_appelant = await _recuperer_sip_id_appelant(channel)
        await _demarrer_compteur_pour_appel(channel, sip_id_appelant)
    elif nom_evenement == "Hangup":
        await app.state.compteur_manager.arreter_compteur(channel)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _bootstrap_donnees()
    await _resynchroniser_asterisk_au_demarrage()

    app.state.compteur_manager = CompteurManager(
        on_solde_epuise=_on_solde_epuise, on_fin_appel=_on_fin_appel
    )
    app.state.ami_client = AMIClient(
        host=settings.ASTERISK_AMI_HOST,
        port=settings.ASTERISK_AMI_PORT,
        username=settings.ASTERISK_AMI_USER,
        secret=settings.ASTERISK_AMI_SECRET,
        on_event=_on_ami_event,
    )
    await app.state.ami_client.demarrer()

    yield

    await app.state.ami_client.arreter()


app = FastAPI(
    title="KANTYVOIP API",
    description="API de gestion de la plateforme KANTYVOIP avec billing prepaye",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(utilisateurs_router)
app.include_router(cdr_router)
app.include_router(tokens_router)
app.include_router(rechargements_router)
app.include_router(statistiques_router)
app.include_router(ami_router)
app.include_router(services_ivr_router)
app.include_router(monitoring_router)
app.include_router(tarifs_router)



@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
