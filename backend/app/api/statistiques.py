from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.infrastructure.database.models import CDR, Utilisateur
from app.schemas.statistique import (
    RevenuParPeriode,
    StatistiquesAppels,
    StatistiquesUtilisateurs,
    TopDestination,
)

router = APIRouter(
    prefix="/api/statistiques", tags=["statistiques"], dependencies=[Depends(get_current_admin)]
)


def _select_count(model) -> select:
    return select(func.count()).select_from(model)


def _select_sum(column) -> select:
    return select(func.sum(column))


@router.get("/appels", response_model=StatistiquesAppels)
async def statistiques_appels(db: AsyncSession = Depends(get_db)) -> StatistiquesAppels:
    total = (await db.execute(_select_count(CDR))).scalar_one()
    termines = (await db.execute(_select_count(CDR).where(CDR.statut == "termine"))).scalar_one()
    echoues = (await db.execute(_select_count(CDR).where(CDR.statut == "echoue"))).scalar_one()
    coupes = (await db.execute(_select_count(CDR).where(CDR.statut == "coupe"))).scalar_one()
    duree_totale = (await db.execute(_select_sum(CDR.duree))).scalar_one() or 0

    return StatistiquesAppels(
        total_appels=total,
        appels_termines=termines,
        appels_echoues=echoues,
        appels_coupes=coupes,
        duree_totale_secondes=duree_totale,
        duree_moyenne_secondes=(duree_totale / total) if total else 0.0,
    )


@router.get("/revenus", response_model=list[RevenuParPeriode])
async def statistiques_revenus(
    db: AsyncSession = Depends(get_db),
    date_debut: datetime | None = None,
    date_fin: datetime | None = None,
) -> list[RevenuParPeriode]:
    # func.date(...) (plutot que cast(..., Date)) est portable SQLite/PostgreSQL :
    # le CAST SQL standard vers DATE n'est pas fiable sur SQLite (utilise en dev/tests).
    stmt = (
        select(func.date(CDR.date_appel).label("jour"), func.sum(CDR.cout).label("revenu"))
        .group_by("jour")
        .order_by("jour")
    )
    if date_debut is not None:
        stmt = stmt.where(CDR.date_appel >= date_debut)
    if date_fin is not None:
        stmt = stmt.where(CDR.date_appel <= date_fin)

    result = await db.execute(stmt)
    return [
        RevenuParPeriode(periode=str(jour), revenu=revenu or Decimal("0"))
        for jour, revenu in result.all()
    ]


@router.get("/utilisateurs", response_model=StatistiquesUtilisateurs)
async def statistiques_utilisateurs(db: AsyncSession = Depends(get_db)) -> StatistiquesUtilisateurs:
    total = (await db.execute(_select_count(Utilisateur))).scalar_one()
    actifs = (await db.execute(_select_count(Utilisateur).where(Utilisateur.statut == "actif"))).scalar_one()
    suspendus = (await db.execute(_select_count(Utilisateur).where(Utilisateur.statut == "suspendu"))).scalar_one()
    solde_total = (await db.execute(_select_sum(Utilisateur.solde))).scalar_one() or Decimal("0")

    return StatistiquesUtilisateurs(
        total_utilisateurs=total,
        utilisateurs_actifs=actifs,
        utilisateurs_suspendus=suspendus,
        solde_total=solde_total,
    )


@router.get("/destinations", response_model=list[TopDestination])
async def statistiques_destinations(db: AsyncSession = Depends(get_db), limite: int = 10) -> list[TopDestination]:
    stmt = (
        select(CDR.destination, func.count(CDR.id).label("nb"), func.sum(CDR.cout).label("cout_total"))
        .group_by(CDR.destination)
        .order_by(func.count(CDR.id).desc())
        .limit(limite)
    )
    result = await db.execute(stmt)
    return [
        TopDestination(destination=destination, nombre_appels=nb, cout_total=cout_total or Decimal("0"))
        for destination, nb, cout_total in result.all()
    ]
