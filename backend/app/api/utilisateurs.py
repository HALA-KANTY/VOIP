import secrets
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.synchronisation import synchroniser_asterisk as _synchroniser_asterisk

from app.api.deps import get_current_admin, get_db
from app.domain.billing import SoldeInsuffisantError, crediter, debiter
from app.infrastructure.database.models import Utilisateur
from app.schemas.utilisateur import (
    MontantRequest,
    SoldeRead,
    UtilisateurCreate,
    UtilisateurRead,
    UtilisateurUpdate,
)
from app.security import hash_password

router = APIRouter(
    prefix="/api/utilisateurs", tags=["utilisateurs"], dependencies=[Depends(get_current_admin)]
)


PLAGES_SIP = {
    "normal": "2000",
    "commercial": "3000",
    "support": "4000",
    "comptabilite": "5000",
}


async def _generer_sip_id(db: AsyncSession, type_utilisateur: str = "normal") -> str:
    """Génère le prochain sip_id selon la plage du type d'utilisateur."""
    base = PLAGES_SIP.get(type_utilisateur, "2000")
    prefixe = base[0]  # Premier chiffre de la plage (2, 3, 4, 5)

    result = await db.execute(
        select(func.max(Utilisateur.sip_id)).where(
            Utilisateur.sip_id.like(f"{prefixe}%")
        )
    )
    dernier = result.scalar_one_or_none()

    if dernier is None or dernier == "":
        return str(int(base) + 1)

    try:
        prochain = int(dernier) + 1
        return str(prochain)
    except ValueError:
        return str(int(base) + 1)

async def _get_utilisateur_ou_404(utilisateur_id: int, db: AsyncSession) -> Utilisateur:
    utilisateur = await db.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return utilisateur


def _generer_secret_sip() -> str:
    return secrets.token_urlsafe(12)


def _assurer_secret_sip(utilisateur: Utilisateur) -> None:
    """Un sip_id sans secret est inutilisable pour Asterisk : on en genere un."""
    if utilisateur.sip_id and not utilisateur.sip_secret:
        utilisateur.sip_secret = _generer_secret_sip()


@router.get("", response_model=list[UtilisateurRead])
async def lister_utilisateurs(db: AsyncSession = Depends(get_db)) -> list[Utilisateur]:
    result = await db.execute(select(Utilisateur).order_by(Utilisateur.id))
    return list(result.scalars().all())


@router.get("/{utilisateur_id}", response_model=UtilisateurRead)
async def obtenir_utilisateur(utilisateur_id: int, db: AsyncSession = Depends(get_db)) -> Utilisateur:
    return await _get_utilisateur_ou_404(utilisateur_id, db)


@router.post("", response_model=UtilisateurRead, status_code=status.HTTP_201_CREATED)
async def creer_utilisateur(
    payload: UtilisateurCreate, db: AsyncSession = Depends(get_db)
) -> Utilisateur:
    existant = await db.execute(select(Utilisateur).where(Utilisateur.username == payload.username))
    if existant.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce nom d'utilisateur existe deja")

    # Générer automatiquement le sip_id s'il n'est pas fourni
    type_utilisateur = payload.type_utilisateur if payload.type_utilisateur else "normal"
    sip_id = payload.sip_id if payload.sip_id else await _generer_sip_id(db, type_utilisateur)

    utilisateur = Utilisateur(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nom_complet=payload.nom_complet,
        email=payload.email,
        sip_id=sip_id,
        sip_secret=payload.sip_secret,  # genere par _assurer_secret_sip si non fourni
        type_utilisateur=type_utilisateur,
    )

    _assurer_secret_sip(utilisateur)
    db.add(utilisateur)
    await db.commit()
    await db.refresh(utilisateur)
    await _synchroniser_asterisk(db)
    return utilisateur


@router.put("/{utilisateur_id}", response_model=UtilisateurRead)
async def modifier_utilisateur(
    utilisateur_id: int, payload: UtilisateurUpdate, db: AsyncSession = Depends(get_db)
) -> Utilisateur:
    utilisateur = await _get_utilisateur_ou_404(utilisateur_id, db)
    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        setattr(utilisateur, champ, valeur)
    _assurer_secret_sip(utilisateur)
    await db.commit()
    await db.refresh(utilisateur)
    await _synchroniser_asterisk(db)
    return utilisateur


@router.post("/{utilisateur_id}/regenerer_secret_sip", response_model=UtilisateurRead)
async def regenerer_secret_sip(utilisateur_id: int, db: AsyncSession = Depends(get_db)) -> Utilisateur:
    utilisateur = await _get_utilisateur_ou_404(utilisateur_id, db)
    if not utilisateur.sip_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cet utilisateur n'a pas de sip_id"
        )
    utilisateur.sip_secret = _generer_secret_sip()
    await db.commit()
    await db.refresh(utilisateur)
    await _synchroniser_asterisk(db)
    return utilisateur


@router.delete("/{utilisateur_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_utilisateur(utilisateur_id: int, db: AsyncSession = Depends(get_db)) -> None:
    utilisateur = await _get_utilisateur_ou_404(utilisateur_id, db)
    await db.delete(utilisateur)
    await db.commit()
    await _synchroniser_asterisk(db)


@router.get("/{utilisateur_id}/solde", response_model=SoldeRead)
async def consulter_solde(utilisateur_id: int, db: AsyncSession = Depends(get_db)) -> SoldeRead:
    utilisateur = await _get_utilisateur_ou_404(utilisateur_id, db)
    return SoldeRead(utilisateur_id=utilisateur.id, solde=utilisateur.solde)


@router.post("/{utilisateur_id}/crediter", response_model=SoldeRead)
async def crediter_solde(
    utilisateur_id: int, payload: MontantRequest, db: AsyncSession = Depends(get_db)
) -> SoldeRead:
    utilisateur = await _get_utilisateur_ou_404(utilisateur_id, db)
    utilisateur.solde = crediter(utilisateur.solde, payload.montant)
    await db.commit()
    return SoldeRead(utilisateur_id=utilisateur.id, solde=utilisateur.solde)


@router.post("/{utilisateur_id}/debiter", response_model=SoldeRead)
async def debiter_solde(
    utilisateur_id: int, payload: MontantRequest, db: AsyncSession = Depends(get_db)
) -> SoldeRead:
    utilisateur = await _get_utilisateur_ou_404(utilisateur_id, db)
    try:
        utilisateur.solde = debiter(utilisateur.solde, payload.montant)
    except SoldeInsuffisantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()
    return SoldeRead(utilisateur_id=utilisateur.id, solde=utilisateur.solde)


