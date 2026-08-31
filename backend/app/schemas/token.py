from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TokenGenererRequest(BaseModel):
    montant: Decimal = Field(gt=0)


class TokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    montant: Decimal
    statut: str
    date_creation: datetime
    date_utilisation: datetime | None


class TokenValiderRequest(BaseModel):
    code: str
    utilisateur_id: int
