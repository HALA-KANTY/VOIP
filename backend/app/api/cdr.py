import csv
import io
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin, get_db
from app.infrastructure.database.models import CDR
from app.schemas.cdr import CDRRead

router = APIRouter(prefix="/api/cdr", tags=["cdr"], dependencies=[Depends(get_current_admin)])


def _appliquer_filtres(
    stmt,
    date_debut: datetime | None,
    date_fin: datetime | None,
    utilisateur_id: int | None,
    destination: str | None,
    duree_min: int | None,
    duree_max: int | None,
    cout_min: Decimal | None,
    cout_max: Decimal | None,
):
    """Filtres combinables (ET logique)."""
    if date_debut is not None:
        stmt = stmt.where(CDR.date_appel >= date_debut)
    if date_fin is not None:
        stmt = stmt.where(CDR.date_appel <= date_fin)
    if utilisateur_id is not None:
        stmt = stmt.where(CDR.utilisateur_id == utilisateur_id)
    if destination is not None:
        stmt = stmt.where(CDR.destination == destination)
    if duree_min is not None:
        stmt = stmt.where(CDR.duree >= duree_min)
    if duree_max is not None:
        stmt = stmt.where(CDR.duree <= duree_max)
    if cout_min is not None:
        stmt = stmt.where(CDR.cout >= cout_min)
    if cout_max is not None:
        stmt = stmt.where(CDR.cout <= cout_max)
    return stmt


@router.get("", response_model=list[CDRRead])
async def lister_cdr(
    db: AsyncSession = Depends(get_db),
    date_debut: datetime | None = None,
    date_fin: datetime | None = None,
    utilisateur_id: int | None = None,
    destination: str | None = None,
    duree_min: int | None = None,
    duree_max: int | None = None,
    cout_min: Decimal | None = None,
    cout_max: Decimal | None = None,
) -> list[CDR]:
    stmt = _appliquer_filtres(
        select(CDR), date_debut, date_fin, utilisateur_id, destination, duree_min, duree_max, cout_min, cout_max
    ).options(selectinload(CDR.utilisateur)).order_by(CDR.date_appel.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/export")
async def exporter_cdr(
    db: AsyncSession = Depends(get_db),
    date_debut: datetime | None = None,
    date_fin: datetime | None = None,
    utilisateur_id: int | None = None,
    destination: str | None = None,
    duree_min: int | None = None,
    duree_max: int | None = None,
    cout_min: Decimal | None = None,
    cout_max: Decimal | None = None,
) -> StreamingResponse:
    stmt = _appliquer_filtres(
        select(CDR), date_debut, date_fin, utilisateur_id, destination, duree_min, duree_max, cout_min, cout_max
    ).options(selectinload(CDR.utilisateur)).order_by(CDR.date_appel.desc())
    result = await db.execute(stmt)
    lignes = result.scalars().all()

    buffer = io.StringIO()
    buffer.write("﻿")  # BOM UTF-8 pour compatibilite Excel
    writer = csv.writer(buffer)
    writer.writerow(["id", "utilisateur_id", "utilisateur_nom", "date_appel", "duree", "destination", "cout", "statut", "type_connexion"])
    for cdr in lignes:
        writer.writerow(
            [cdr.id, cdr.utilisateur_id, cdr.utilisateur_nom, cdr.date_appel.isoformat(), cdr.duree, cdr.destination, cdr.cout, cdr.statut, cdr.type_connexion]
        )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cdr_export.csv"},
    )


@router.get("/{cdr_id}", response_model=CDRRead)
async def obtenir_cdr(cdr_id: int, db: AsyncSession = Depends(get_db)) -> CDR:
    cdr = await db.get(CDR, cdr_id, options=[selectinload(CDR.utilisateur)])
    if cdr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CDR introuvable")
    return cdr
