"""Gestion automatique des files d'attente Asterisk."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database.models import Utilisateur

logger = logging.getLogger("asterisk_sync")

MAPPING_TYPE_QUEUE = {
    "commercial": "commercial_queue",
    "support": "support_queue",
    "comptabilite": "comptabilite_queue",
}


def _chemin_queues() -> Path:
    return Path(settings.ASTERISK_CONFIG_DIR) / "queues.conf"


async def generer_queues_conf(db: AsyncSession) -> str:
    """Génère le fichier queues.conf avec les membres selon leur type."""
    result = await db.execute(
        select(Utilisateur).where(Utilisateur.statut == "actif").order_by(Utilisateur.sip_id)
    )
    utilisateurs = result.scalars().all()

    lignes = [
        "; Fichier généré automatiquement — NE PAS ÉDITER",
        "; Source : interface admin (utilisateurs par type)",
        "",
        "[general]",
        "persistentmembers = yes",
        "autofill = yes",
        "",
    ]

    for type_utilisateur, queue_name in MAPPING_TYPE_QUEUE.items():
        membres = [u for u in utilisateurs if u.type_utilisateur == type_utilisateur]

        lignes.append(f"; === {type_utilisateur.upper()} ===")
        lignes.append(f"[{queue_name}]")
        lignes.append("musicclass = default")
        lignes.append("strategy = ringall")
        lignes.append("timeout = 15")
        lignes.append("retry = 5")
        lignes.append("maxlen = 10")
        lignes.append("joinempty = yes")
        lignes.append("leavewhenempty = yes")
        lignes.append("announce-position = yes")
        lignes.append("announce-holdtime = yes")
        lignes.append("")

        if membres:
            for membre in membres:
                lignes.append(f"member => PJSIP/{membre.sip_id}")
        else:
            lignes.append("; Aucun membre actif")

        lignes.append("")

    return "\n".join(lignes)


async def ecrire_queues(db: AsyncSession) -> None:
    """Écrit le fichier queues.conf sur le disque (best-effort, ne leve pas)."""
    contenu = await generer_queues_conf(db)
    try:
        _chemin_queues().write_text(contenu, encoding="utf-8")
    except OSError as exc:
        logger.warning("Impossible d'ecrire queues.conf (%s) : %s", _chemin_queues(), exc)
