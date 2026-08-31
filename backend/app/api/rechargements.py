from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.domain.billing import crediter
from app.infrastructure.database.models import Rechargement, Token, Utilisateur
from app.schemas.rechargement import RechargementCreate, RechargementRead

router = APIRouter(
    prefix="/api/rechargements", tags=["rechargements"], dependencies=[Depends(get_current_admin)]
)


async def effectuer_rechargement(db: AsyncSession, utilisateur_id: int, code_token: str) -> Rechargement:
    """
    Valide un token et credite le solde de l'utilisateur de facon atomique :
    le token est marque utilise, le solde est credite et la ligne de rechargement
    est creee dans la meme transaction.
    """
    result = await db.execute(select(Token).where(Token.code == code_token))
    token = result.scalar_one_or_none()
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token introuvable")
    if token.statut == "utilise":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce token a deja ete utilise")

    utilisateur = await db.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    utilisateur.solde = crediter(utilisateur.solde, token.montant)
    token.statut = "utilise"
    token.date_utilisation = datetime.now(timezone.utc).replace(tzinfo=None)

    rechargement = Rechargement(utilisateur_id=utilisateur.id, token_id=token.id, montant=token.montant)
    db.add(rechargement)
    await db.commit()
    await db.refresh(rechargement)
    return rechargement


@router.get("", response_model=list[RechargementRead])
async def lister_rechargements(db: AsyncSession = Depends(get_db)) -> list[Rechargement]:
    result = await db.execute(select(Rechargement).order_by(Rechargement.date_rechargement.desc()))
    return list(result.scalars().all())


@router.post("", response_model=RechargementRead, status_code=status.HTTP_201_CREATED)
async def creer_rechargement(payload: RechargementCreate, db: AsyncSession = Depends(get_db)) -> Rechargement:
    return await effectuer_rechargement(db, payload.utilisateur_id, payload.code_token)
