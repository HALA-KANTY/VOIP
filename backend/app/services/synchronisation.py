"""Synchronisation centralisée des fichiers Asterisk via AMI."""

import asyncio
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger("asterisk_sync")


async def recharger_asterisk(module: str) -> bool:
   
    host = settings.ASTERISK_AMI_HOST
    port = int(settings.ASTERISK_AMI_PORT)
    user = settings.ASTERISK_AMI_USER
    secret = settings.ASTERISK_AMI_SECRET

    try:
        reader, writer = await asyncio.open_connection(host, port)

        # Authentification
        login_packet = (
            f"Action: Login\r\n"
            f"Username: {user}\r\n"
            f"Secret: {secret}\r\n\r\n"
        )
        writer.write(login_packet.encode("utf-8"))
        await writer.drain()
        await reader.readuntil(b"\r\n\r\n")

        # Commande de rechargement selon le module
        if module == "pjsip":
            command = "pjsip reload"
        elif module == "voicemail":
            command = "voicemail reload"
        elif module == "queue":
            command = "queue reload all"
        else:
            command = module

        command_packet = (
            f"Action: Command\r\n"
            f"Command: {command}\r\n\r\n"
        )
        writer.write(command_packet.encode("utf-8"))
        await writer.drain()
        await reader.readuntil(b"\r\n\r\n")

        # Déconnexion
        logoff_packet = "Action: Logoff\r\n\r\n"
        writer.write(logoff_packet.encode("utf-8"))
        await writer.drain()

        writer.close()
        await writer.wait_closed()
        return True

    except Exception:
        return False


async def ecrire_et_recharger(chemin: Path, contenu: str, module: str) -> tuple[bool, str]:
    
    try:
        chemin.write_text(contenu, encoding="utf-8")
    except OSError as e:
        return False, f"Impossible d'écrire {chemin.name} : {e}"

    succes = await recharger_asterisk(module)
    if succes:
        return True, f"{chemin.name} synchronisé et {module} rechargé"
    else:
        return False, f"{chemin.name} écrit mais échec du rechargement {module}"


async def synchroniser_asterisk(db: AsyncSession) -> None:
    
    from app.api.ami_endpoints import exporter_pjsip
    from app.services.generateur_dialplan import ecrire_dialplan
    from app.services.gestion_queues import generer_queues_conf
    from app.services.gestion_voicemail import generer_voicemail_conf

    config_dir = Path(settings.ASTERISK_CONFIG_DIR)

    await ecrire_dialplan(db)

    succes, message = await ecrire_et_recharger(config_dir / "pjsip_users.conf", await exporter_pjsip(db), "pjsip")
    if not succes:
        logger.warning(message)

    contenu_queues = await generer_queues_conf(db)
    succes, message = await ecrire_et_recharger(config_dir / "queues.conf", contenu_queues, "queue")
    if not succes:
        logger.warning(message)

    contenu_voicemail = await generer_voicemail_conf(db)
    succes, message = await ecrire_et_recharger(config_dir / "voicemail.conf", contenu_voicemail, "voicemail")
    if not succes:
        logger.warning(message)