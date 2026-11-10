from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Entreprise(Base):
    __tablename__ = "entreprise"
    id_entreprise: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150))
    pays: Mapped[str] = mapped_column(String(80))
    secteur: Mapped[str] = mapped_column(String(100))

    encadrants: Mapped[list["EncadrantPro"]] = relationship(back_populates="entreprise")


class EncadrantPro(Base):
    """Encadrant professionnel : personne de l'entreprise (pas un enseignant de l'ISI)."""
    __tablename__ = "encadrant_pro"
    id_encadrant_pro: Mapped[int] = mapped_column(primary_key=True)
    id_entreprise: Mapped[int] = mapped_column(ForeignKey("entreprise.id_entreprise"))
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150))
    poste: Mapped[str] = mapped_column(String(100))

    entreprise: Mapped[Entreprise] = relationship(back_populates="encadrants")


class Convention(Base):
    __tablename__ = "convention"
    id_convention: Mapped[int] = mapped_column(primary_key=True)
    id_stage: Mapped[int] = mapped_column(Integer, unique=True, index=True)  # reference vers le Stage Service
    id_entreprise: Mapped[int] = mapped_column(ForeignKey("entreprise.id_entreprise"))
    id_encadrant_pro: Mapped[int] = mapped_column(ForeignKey("encadrant_pro.id_encadrant_pro"))
    type_stage: Mapped[str] = mapped_column(String(10))   # local | etranger
    pays: Mapped[str] = mapped_column(String(80))
    statut: Mapped[str] = mapped_column(String(15), default="en_attente")  # en_attente | signee | terminee

    entreprise: Mapped[Entreprise] = relationship()
    encadrant: Mapped[EncadrantPro] = relationship()
