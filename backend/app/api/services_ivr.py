from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.generateur_dialplan import ecrire_dialplan
from app.api.deps import get_current_admin, get_db
from app.infrastructure.database.models import ServiceIVR
from app.schemas.service_ivr import ServiceIVRCreate, ServiceIVRRead, ServiceIVRUpdate

router = APIRouter(
    prefix="/api/services-ivr", tags=["services-ivr"], dependencies=[Depends(get_current_admin)]
)


async def _get_service_ou_404(service_id: int, db: AsyncSession) -> ServiceIVR:
    service = await db.get(ServiceIVR, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service IVR introuvable")
    return service


@router.get("", response_model=list[ServiceIVRRead])
async def lister_services(db: AsyncSession = Depends(get_db)) -> list[ServiceIVR]:
    result = await db.execute(select(ServiceIVR).order_by(ServiceIVR.code))
    return list(result.scalars().all())


@router.post("", response_model=ServiceIVRRead, status_code=status.HTTP_201_CREATED)
async def creer_service(payload: ServiceIVRCreate, db: AsyncSession = Depends(get_db)) -> ServiceIVR:
    existant = await db.execute(select(ServiceIVR).where(ServiceIVR.code == payload.code))
    if existant.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce code existe déjà")

    service = ServiceIVR(**payload.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    await ecrire_dialplan(db)
    return service


@router.get("/{service_id}", response_model=ServiceIVRRead)
async def obtenir_service(service_id: int, db: AsyncSession = Depends(get_db)) -> ServiceIVR:
    return await _get_service_ou_404(service_id, db)


@router.put("/{service_id}", response_model=ServiceIVRRead)
async def modifier_service(
    service_id: int, payload: ServiceIVRUpdate, db: AsyncSession = Depends(get_db)
) -> ServiceIVR:
    service = await _get_service_ou_404(service_id, db)
    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        setattr(service, champ, valeur)
    await db.commit()
    await db.refresh(service)
    await ecrire_dialplan(db)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_service(service_id: int, db: AsyncSession = Depends(get_db)) -> None:
    service = await _get_service_ou_404(service_id, db)
    await db.delete(service)
    await db.commit()
    await ecrire_dialplan(db)

