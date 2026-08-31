"""Génère le fichier extensions_ivr.conf à partir des services IVR en base."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database.models import ServiceIVR
from app.services.synchronisation import recharger_asterisk

logger = logging.getLogger("asterisk_sync")


def _chemin_dialplan() -> Path:
    return Path(settings.ASTERISK_CONFIG_DIR) / "extensions_ivr.conf"


def _application_asterisk(service: ServiceIVR) -> str:
    """Retourne l'application Asterisk selon le type du service."""
    if service.type == "queue":
        return f"Queue({service.destination})"
    elif service.type == "conf":
        return f"ConfBridge({service.destination})"
    elif service.type == "dial":
        return f"Dial({service.destination},60)"
    elif service.type == "playback":
        return f"Playback({service.destination})"
    return "Hangup()"


def _est_service_commercial(service: ServiceIVR) -> bool:
    """Le service commercial a un sous-menu dedie (achat de credit / agent)
    au lieu du routage generique vers sa destination (voir _bloc_commercial_submenu)."""
    return service.destination == "commercial_queue"


def _bloc_service(service: ServiceIVR) -> list[str]:
    """
    Genere l'extension complete pour un service. Tout le menu IVR est
    gratuit -- donc accessible meme a solde 0 -- sauf la conference (type
    "conf"), seul service facture et donc seul protege par une verification
    de solde avant d'y donner acces. Meme regle metier que
    _est_appel_gratuit() dans ami_endpoints.py (facturation finale).
    """
    entete = [
        f"; {service.nom}",
        f"exten => {service.code},1,Answer()",
        " same => n,Set(SIP_ID=${CALLERID(num)})",
        f" same => n,Set(APPEL_DESTINATION={service.code})",
    ]

    if _est_service_commercial(service):
        return entete + [
            " same => n,Goto(commercial-submenu,s,1)",
            "",
        ]

    if service.type == "conf":
        return entete + [
            " same => n,AGI(verifier_solde.py)",
            ' same => n,GotoIf($["${AUTORISE}" = "1"]?autorise:refuse)',
            "",
            " same => n(refuse),Playback(custom/solde-insuffisant)",
            " same => n,Hangup(21)",
            "",
            f" same => n(autorise),{_application_asterisk(service)}",
            " same => n,Hangup()",
            "",
        ]

    if service.type == "queue":
        # QUEUESTATUS n'est renseigne par Asterisk QUE quand Queue() echoue a
        # mettre l'appelant en relation (file pleine, aucun membre, timeout...).
        # Un appel qui aboutit reellement laisse QUEUESTATUS vide : c'est ce
        # test, et non un statut precis comme "TIMEOUT", qu'il faut verifier --
        # sinon un cas comme LEAVEEMPTY (aucun agent connecte) raccroche
        # brutalement l'appelant sans aucun message.
        # La boite vocale d'equipe partage le meme nom que la queue sans son
        # suffixe "_queue" (commercial_queue -> commercial, etc, voir
        # gestion_voicemail.py) -- convention utilisee dans tout le projet.
        boite = service.destination.removesuffix("_queue")
        return entete + [
            f" same => n,Queue({service.destination},,,,45)",
            ' same => n,GotoIf($["${QUEUESTATUS}" = ""]?fin)',
            " same => n,Playback(custom/agent-occupe)",
            f" same => n,Voicemail({boite}@voip-billing)",
            " same => n,Hangup()",
            " same => n(fin),Hangup()",
            "",
        ]

    return entete + [
        f" same => n,{_application_asterisk(service)}",
        " same => n,Hangup()",
        "",
    ]


def _bloc_commercial_submenu() -> list[str]:
    """
    Sous-menu du service commercial (achat de credit / agent). Chaque niveau
    vit dans son propre contexte a chiffre unique, meme principe que
    [ivr-menu] dans extensions-billing.conf : eviter qu'un choix a un
    chiffre (ex: "1") ne soit ambigu avec une autre extension plus longue du
    meme contexte (ex: "1001#"), ce qui forcerait Asterisk a attendre le
    timeout complet avant de reagir.
    """
    return [
        "[commercial-submenu]",
        "; Tape 1 : acheter du credit -- Tape 2 : parler a un agent -- Tape 3 : retour au menu principal",
        "exten => s,1,Background(custom/menu-commercial)",
        " same => n,WaitExten(10)",
        " same => n,Playback(custom/menu-commercial)",
        " same => n,WaitExten(10)",
        " same => n,Goto(ivr-menu,s,1)",
        "",
        "exten => 1,1,Goto(commercial-submenu-montant,s,1)",
        "",
        "exten => 2,1,Queue(commercial_queue,,,,45)",
        # QUEUESTATUS vide = appel reellement termine (voir _bloc_service pour
        # le detail) ; tout le reste (TIMEOUT, LEAVEEMPTY si aucun agent
        # connecte, FULL, ...) doit tomber sur la messagerie, pas raccrocher.
        ' same => n,GotoIf($["${QUEUESTATUS}" = ""]?fin:voicemail)',
        " same => n(voicemail),Playback(custom/agent-occupe)",
        " same => n,Voicemail(commercial@voip-billing)",
        " same => n,Hangup()",
        " same => n(fin),Hangup()",
        "",
        "exten => 3,1,Playback(custom/retour-menu)",
        " same => n,Goto(ivr-menu,s,1)",
        "",
        "[commercial-submenu-montant]",
        "; Tape 1-4 : montant a acheter (500/1000/2000/5000 Ar) -- pas de choix : retour au sous-menu",
        "exten => s,1,Background(custom/choisir-montant)",
        " same => n,WaitExten(10)",
        " same => n,Playback(custom/choisir-montant)",
        " same => n,WaitExten(10)",
        " same => n,Goto(commercial-submenu,s,1)",
        "",
        "exten => 1,1,Goto(commercial-achat,1,1)",
        "exten => 2,1,Goto(commercial-achat,2,1)",
        "exten => 3,1,Goto(commercial-achat,3,1)",
        "exten => 4,1,Goto(commercial-achat,4,1)",
        "",
        "[commercial-achat]",
        "exten => _[1-4],1,Set(SIP_ID=${CALLERID(num)})",
        " same => n,AGI(acheter_credit.py,${EXTEN})",
        ' same => n,GotoIf($["${ACHAT_STATUT}" = "SUCCESS"]?ok:echec)',
        "",
        # Le code est lu deux fois -- une seule lecture est trop rapide pour
        # que l'appelant ait le temps de le noter.
        " same => n(ok),Playback(custom/votre-code)",
        " same => n,SayDigits(${CODE_TOKEN})",
        " same => n,Playback(custom/votre-code)",
        " same => n,SayDigits(${CODE_TOKEN})",
        " same => n,Goto(commercial-code-confirme,s,1)",
        "",
        " same => n(echec),Hangup()",
        "",
        "[commercial-code-confirme]",
        "; Recharger tout de suite le compte de l'appelant avec le code qu'il vient",
        "; d'entendre, sans qu'il ait besoin de raccrocher et recomposer 700+code#.",
        "exten => s,1,Playback(custom/recharger-maintenant)",
        " same => n,WaitExten(5)",
        " same => n,Hangup()",
        "",
        "exten => 1,1,AGI(recharger_solde.py,${CODE_TOKEN})",
        ' same => n,GotoIf($["${RECHARGE_STATUT}" = "SUCCESS"]?ok:ko)',
        "",
        " same => n(ok),Playback(custom/recharger-succes)",
        " same => n,Hangup()",
        "",
        " same => n(ko),Playback(custom/token-invalide)",
        " same => n,Hangup()",
        "",
    ]


async def generer_extensions_ivr(db: AsyncSession) -> str:
    """Génère le contenu du dialplan des services IVR."""
    result = await db.execute(
        select(ServiceIVR).where(ServiceIVR.actif.is_(True)).order_by(ServiceIVR.code)
    )
    services = result.scalars().all()

    lignes = [
        "; Fichier généré automatiquement — NE PAS ÉDITER",
        "; Source : interface admin (services_ivr)",
        "",
        "[services-ivr]",
        "",
    ]

    for service in services:
        lignes.extend(_bloc_service(service))

    # Une seule extension "h" partagee par le contexte (pas une par service) :
    # elle enregistre le CDR final quel que soit le service appele. Doit
    # rester dans [services-ivr], donc emise AVANT les sous-contextes
    # commerciaux ci-dessous (chacun ouvre son propre contexte).
    lignes.extend(
        [
            "; Fin d'appel automatique (enregistrement CDR)",
            "exten => h,1,NoOp(Fin d'appel ${SIP_ID:-inconnu} -> ${APPEL_DESTINATION} statut=${DIALSTATUS} duree=${CDR(billsec)}s)",
            ' same => n,GotoIf($["${SIP_ID}" = ""]?fin)',
            ' same => n,GotoIf($["${DIALSTATUS}" = "ANSWER"]?termine)',
            ' same => n,GotoIf($["${DIALSTATUS}" = "CANCEL"]?coupe)',
            ' same => n,GotoIf($["${DIALSTATUS}" = "BUSY"]?occupe)',
            ' same => n,GotoIf($["${DIALSTATUS}" = "NOANSWER"]?sans_reponse)',
            ' same => n,GotoIf($["${DIALSTATUS}" = "CHANUNAVAIL"]?hors_ligne)',
            " same => n,Set(STATUT_CDR=echoue)",
            " same => n,Goto(enregistrer)",
            "",
            " same => n(termine),Set(STATUT_CDR=termine)",
            " same => n,Goto(enregistrer)",
            "",
            " same => n(coupe),Set(STATUT_CDR=coupe)",
            " same => n,Goto(enregistrer)",
            "",
            " same => n(occupe),Set(STATUT_CDR=occupe)",
            " same => n,Goto(enregistrer)",
            "",
            " same => n(sans_reponse),Set(STATUT_CDR=sans_reponse)",
            " same => n,Goto(enregistrer)",
            "",
            " same => n(hors_ligne),Set(STATUT_CDR=hors_ligne)",
            " same => n,Goto(enregistrer)",
            "",
            " same => n(enregistrer),AGI(enregistrer_appel.py,${SIP_ID},${CDR(billsec)},${APPEL_DESTINATION},${STATUT_CDR})",
            " same => n(fin),NoOp()",
            "",
        ]
    )

    lignes.extend(_bloc_commercial_submenu())

    return "\n".join(lignes)


async def ecrire_dialplan(db: AsyncSession) -> None:
    """Écrit extensions_ivr.conf sur le disque et recharge le dialplan Asterisk
    (best-effort, ne leve pas). Sans ce reload, le fichier reecrit reste sans
    effet tant que personne n'execute manuellement `dialplan reload`."""
    contenu = await generer_extensions_ivr(db)
    try:
        _chemin_dialplan().write_text(contenu, encoding="utf-8")
    except OSError as exc:
        logger.warning("Impossible d'ecrire extensions_ivr.conf (%s) : %s", _chemin_dialplan(), exc)
        return

    if not await recharger_asterisk("dialplan reload"):
        logger.warning("extensions_ivr.conf ecrit mais echec du rechargement dialplan via AMI")
