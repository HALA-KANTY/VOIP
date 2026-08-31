"""Gestion automatique des boîtes vocales Asterisk."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database.models import Utilisateur

logger = logging.getLogger("asterisk_sync")


def _chemin_voicemail() -> Path:
    return Path(settings.ASTERISK_CONFIG_DIR) / "voicemail.conf"


async def generer_voicemail_conf(db: AsyncSession) -> str:
    """Génère le fichier voicemail.conf avec les boîtes vocales des utilisateurs."""
    result = await db.execute(
        select(Utilisateur).where(Utilisateur.statut == "actif").order_by(Utilisateur.sip_id)
    )
    utilisateurs = result.scalars().all()

    lignes = [
        "; Fichier généré automatiquement — NE PAS ÉDITER",
        "; Source : interface admin (utilisateurs actifs)",
        "",
        "[general]",
        # sln16 (16 kHz, PCM brut non compresse) au lieu de wav (8 kHz) :
        # profite du codec large bande g722 desormais priorise cote pjsip.conf.
        # Les messages ne sont ecoutes que par telephone (VoicemailMain), donc
        # l'absence d'extension audio standard lisible hors Asterisk n'est pas
        # genante ici (pas d'envoi par email/telechargement dans ce projet).
        "format = sln16",
        "maxmsg = 100",
        "maxsecs = 60",
        "minsecs = 3",
        "skipms = 3000",
        "maxsilence = 10",
        "silencethreshold = 128",
        "maxlogins = 3",
        "",
        "[voip-billing]",
        "",
        "; Boites vocales partagees par equipe (PIN commun 0000, voir option 5",
        "; du menu 100 qui redirige chaque agent vers la boite de son equipe).",
        "commercial => 0000,Boite vocale Commercial,",
        "support => 0000,Boite vocale Support,",
        "comptabilite => 0000,Boite vocale Comptabilite,",
        "",
    ]

    for utilisateur in utilisateurs:
        if utilisateur.sip_id:
            # PIN par défaut : 4 derniers chiffres du sip_id (ou 1234)
            pin = utilisateur.sip_id[-4:] if len(utilisateur.sip_id) >= 4 else "1234"
            email = utilisateur.email or ""
            lignes.append(
                f"{utilisateur.sip_id} => {pin},{utilisateur.nom_complet},{email}"
            )

    lignes.append("")
    return "\n".join(lignes)


async def ecrire_voicemail(db: AsyncSession) -> None:
    """Écrit le fichier voicemail.conf sur le disque (best-effort, ne leve pas)."""
    contenu = await generer_voicemail_conf(db)
    try:
        _chemin_voicemail().write_text(contenu, encoding="utf-8")
    except OSError as exc:
        logger.warning("Impossible d'ecrire voicemail.conf (%s) : %s", _chemin_voicemail(), exc)
