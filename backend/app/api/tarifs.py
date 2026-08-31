from decimal import Decimal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.config import settings
from app.infrastructure.database.models import Tarif

router = APIRouter(prefix="/api/tarifs", tags=["tarifs"], dependencies=[Depends(get_current_admin)])


class TarifCreateRequest(BaseModel):
    montant_par_seconde: Decimal = Field(..., gt=0, description="Nouveau tarif en AR/sec")


class TarifActifResponse(BaseModel):
    montant_par_seconde: Decimal


@router.get("/actif", response_model=TarifActifResponse)
async def obtenir_tarif_actif(db: AsyncSession = Depends(get_db)) -> TarifActifResponse:
    result = await db.execute(select(Tarif).where(Tarif.actif.is_(True)))
    tarif = result.scalars().first()
    montant = tarif.montant_par_seconde if tarif is not None else settings.TARIF_DEFAUT
    return TarifActifResponse(montant_par_seconde=montant)


@router.post("", status_code=status.HTTP_201_CREATED)
async def changer_tarif(payload: TarifCreateRequest, db: AsyncSession = Depends(get_db)):
    """Désactive l'ancien tarif actif et insère le nouveau."""
    await db.execute(update(Tarif).where(Tarif.actif.is_(True)).values(actif=False))
    nouveau_tarif = Tarif(montant_par_seconde=payload.montant_par_seconde, actif=True)
    db.add(nouveau_tarif)
    await db.commit()
    return {"message": "Tarif mis à jour avec succès", "nouveau_tarif": payload.montant_par_seconde}