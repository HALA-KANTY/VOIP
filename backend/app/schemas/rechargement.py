from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RechargementCreate(BaseModel):
    utilisateur_id: int
    code_token: str


class RechargementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    token_id: int
    montant: Decimal
    date_rechargement: datetime
