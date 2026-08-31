from decimal import Decimal
import random
import string
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.api.rechargements import effectuer_rechargement
from app.infrastructure.database.models import Rechargement, Token
from app.schemas.rechargement import RechargementRead
from app.schemas.token import TokenGenererRequest, TokenRead, TokenValiderRequest
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/tokens", tags=["tokens"], dependencies=[Depends(get_current_admin)])

class BulkTokenRequest(BaseModel):
    montant: Decimal = Field(..., gt=0, description="Montant de recharge en Ariary")
    quantite: int = Field(..., gt=0, le=1000, description="Nombre de tokens à générer (max 1000)")

def _generer_code() -> str:
    """
    Génère un code de recharge numérique à 12 chiffres.
    Utilise `random.SystemRandom` pour la sécurité cryptographique.
    Le code est composé uniquement de chiffres (0-9).
    """
    generateur = random.SystemRandom()
    return ''.join(generateur.choice(string.digits) for _ in range(12))


@router.get("", response_model=list[TokenRead])
async def lister_tokens(db: AsyncSession = Depends(get_db)) -> list[Token]:
    result = await db.execute(select(Token).order_by(Token.date_creation.desc()))
    return list(result.scalars().all())


@router.post("/generer", response_model=TokenRead, status_code=status.HTTP_201_CREATED)
async def generer_token(payload: TokenGenererRequest, db: AsyncSession = Depends(get_db)) -> Token:
    code = _generer_code()
    # Garantie d'unicité du code généré
    while (await db.execute(select(Token).where(Token.code == code))).scalar_one_or_none() is not None:
        code = _generer_code()

    token = Token(code=code, montant=payload.montant)
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def generer_lot_tokens(payload: BulkTokenRequest, db: AsyncSession = Depends(get_db)):
    """Génère un lot de tokens numériques à 16 chiffres de manière sécurisée et uniforme."""
    codes_generes = []
    
    for _ in range(payload.quantite):
        code_unique = _generer_code()
        
        # Sécurité anti-collision pour chaque jeton du lot
        while code_unique in codes_generes or (await db.execute(select(Token).where(Token.code == code_unique))).scalar_one_or_none() is not None:
            code_unique = _generer_code()
            
        nouveau_token = Token(
            code=code_unique, 
            montant=payload.montant
            # Le statut prendra sa valeur par défaut ("disponible" ou similaire défini dans le modèle)
        )
        db.add(nouveau_token)
        codes_generes.append(code_unique)
        
    await db.commit()
    return {
        "succes": True,
        "message": f"{payload.quantite} tokens générés avec succès",
        "montant": str(payload.montant),
        "codes": codes_generes,
    }


@router.get("/{code}", response_model=TokenRead)
async def verifier_token(code: str, db: AsyncSession = Depends(get_db)) -> Token:
    result = await db.execute(select(Token).where(Token.code == code))
    token = result.scalar_one_or_none()
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token introuvable")
    return token


@router.post("/valider", response_model=RechargementRead)
async def valider_token(payload: TokenValiderRequest, db: AsyncSession = Depends(get_db)) -> Rechargement:
    """Valide et utilise un token : délègue à la même logique que POST /api/rechargements
    pour garantir qu'un token n'est jamais crédité deux fois quel que soit le point d'entrée."""
    return await effectuer_rechargement(db, payload.utilisateur_id, payload.code)


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_token(token_id: int, db: AsyncSession = Depends(get_db)) -> None:
    token = await db.get(Token, token_id)
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token introuvable")
    if token.statut == "utilise":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un token deja utilise (lie a un rechargement existant)",
        )
    await db.delete(token)
    await db.commit()
