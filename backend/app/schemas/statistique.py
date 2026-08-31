from decimal import Decimal

from pydantic import BaseModel


class StatistiquesAppels(BaseModel):
    total_appels: int
    appels_termines: int
    appels_echoues: int
    appels_coupes: int
    duree_totale_secondes: int
    duree_moyenne_secondes: float


class RevenuParPeriode(BaseModel):
    periode: str
    revenu: Decimal


class StatistiquesUtilisateurs(BaseModel):
    total_utilisateurs: int
    utilisateurs_actifs: int
    utilisateurs_suspendus: int
    solde_total: Decimal


class TopDestination(BaseModel):
    destination: str
    nombre_appels: int
    cout_total: Decimal
