from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceIVRCreate(BaseModel):
    nom: str
    code: str  # ex: "1001#"
    type: str  # "queue", "conf", "dial", "playback"
    destination: str  # "commercial_queue", "PJSIP/2001", "1234"
    description: str | None = None


class ServiceIVRUpdate(BaseModel):
    nom: str | None = None
    code: str | None = None
    type: str | None = None
    destination: str | None = None
    description: str | None = None
    actif: bool | None = None


class ServiceIVRRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    code: str
    type: str
    destination: str
    description: str | None
    actif: bool
    date_creation: datetime
