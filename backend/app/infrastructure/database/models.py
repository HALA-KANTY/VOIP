from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.session import Base


def _maintenant() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=_maintenant)


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nom_complet: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    solde: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    statut: Mapped[str] = mapped_column(String(20), default="actif")  # actif, inactif, suspendu
    type_utilisateur: Mapped[str] = mapped_column(String(20), default="normal")
    sip_id: Mapped[str | None] = mapped_column(String(10), unique=True, nullable=True)
    sip_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=_maintenant)

    cdrs: Mapped[list["CDR"]] = relationship(back_populates="utilisateur")
    rechargements: Mapped[list["Rechargement"]] = relationship(back_populates="utilisateur")


class CDR(Base):
    __tablename__ = "cdr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    date_appel: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_maintenant)
    duree: Mapped[int] = mapped_column(Integer, nullable=False)  # secondes
    destination: Mapped[str] = mapped_column(String(50), nullable=False)
    cout: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default="termine")  # termine, echoue, coupe, occupe, sans_reponse, hors_ligne
    type_connexion: Mapped[str] = mapped_column(String(20), default="sip")  # sip, webrtc

    utilisateur: Mapped["Utilisateur"] = relationship(back_populates="cdrs")

    @property
    def utilisateur_nom(self) -> str:
        """Necessite que la relation `utilisateur` soit deja chargee (selectinload) :
        un acces lazy echouerait en contexte async. Voir api/cdr.py."""
        return self.utilisateur.nom_complet


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default="non_utilise")  # non_utilise, utilise
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=_maintenant)
    date_utilisation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    rechargement: Mapped["Rechargement | None"] = relationship(back_populates="token")


class Rechargement(Base):
    __tablename__ = "rechargements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id"), nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    date_rechargement: Mapped[datetime] = mapped_column(DateTime, default=_maintenant)

    utilisateur: Mapped["Utilisateur"] = relationship(back_populates="rechargements")
    token: Mapped["Token"] = relationship(back_populates="rechargement")


class Tarif(Base):
    __tablename__ = "tarifs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    montant_par_seconde: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.0"))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

class ServiceIVR(Base):
    __tablename__ = "services_ivr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # ex: 1001#
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # queue, conf, dial, playback
    destination: Mapped[str] = mapped_column(String(100), nullable=False)  # commercial_queue, PJSIP/2001, 1234
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=_maintenant)
