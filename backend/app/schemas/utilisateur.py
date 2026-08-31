from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

TYPES_UTILISATEUR = ["normal", "commercial", "support", "comptabilite"]


class UtilisateurBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nom_complet: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    sip_id: str | None = Field(default=None, max_length=10)
    type_utilisateur: str = Field(default="normal", pattern="^(normal|commercial|support|comptabilite)$")


class UtilisateurCreate(UtilisateurBase):
    password: str = Field(min_length=8)
    sip_secret: str | None = Field(default=None, min_length=8, max_length=64)


class UtilisateurUpdate(BaseModel):
    nom_complet: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    sip_id: str | None = Field(default=None, max_length=10)
    sip_secret: str | None = Field(default=None, min_length=8, max_length=64)
    statut: str | None = Field(default=None, pattern="^(actif|inactif|suspendu)$")
    type_utilisateur: str | None = Field(default=None, pattern="^(normal|commercial|support|comptabilite)$")


class UtilisateurRead(UtilisateurBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solde: Decimal
    statut: str
    date_creation: datetime
    sip_secret: str | None = None


class SoldeRead(BaseModel):
    utilisateur_id: int
    solde: Decimal


class MontantRequest(BaseModel):
    montant: Decimal = Field(gt=0)
