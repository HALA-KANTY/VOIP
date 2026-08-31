from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CDRRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    utilisateur_nom: str
    date_appel: datetime
    duree: int
    destination: str
    cout: Decimal
    statut: str
    type_connexion: str
