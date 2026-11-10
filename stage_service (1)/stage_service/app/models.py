from datetime import date
from sqlalchemy import ForeignKey, String, Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


# ---------- Hierarchie 1 : Etudiant  <-  Stagiaire ----------
class Etudiant(Base):
    """Classe mere. 'type' indique le statut actuel : etudiant ou stagiaire."""
    __tablename__ = "etudiant"
    id_etudiant: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150))
    classe: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(20), default="etudiant")

    __mapper_args__ = {"polymorphic_identity": "etudiant", "polymorphic_on": "type"}


class Stagiaire(Etudiant):
    """Classe fille : un Etudiant qui est devenu stagiaire (meme identifiant)."""
    __tablename__ = "stagiaire"
    id_etudiant: Mapped[int] = mapped_column(ForeignKey("etudiant.id_etudiant"), primary_key=True)
    date_statut: Mapped[date] = mapped_column(Date)

    __mapper_args__ = {"polymorphic_identity": "stagiaire"}


# ---------- Hierarchie 2 : Enseignant  <-  EncadrantAcademique ----------
class Enseignant(Base):
    """Classe mere. 'type' indique le role actuel : enseignant ou encadrant."""
    __tablename__ = "enseignant"
    id_enseignant: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150))
    departement: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20), default="enseignant")

    __mapper_args__ = {"polymorphic_identity": "enseignant", "polymorphic_on": "type"}


class EncadrantAcademique(Enseignant):
    """Classe fille : un Enseignant qui encadre un stage (meme identifiant)."""
    __tablename__ = "encadrant_academique"
    id_enseignant: Mapped[int] = mapped_column(ForeignKey("enseignant.id_enseignant"), primary_key=True)
    date_statut: Mapped[date] = mapped_column(Date)

    __mapper_args__ = {"polymorphic_identity": "encadrant"}


# ---------- Stage et suivi ----------
class Stage(Base):
    __tablename__ = "stage"
    id_stage: Mapped[int] = mapped_column(primary_key=True)
    id_etudiant: Mapped[int] = mapped_column(ForeignKey("stagiaire.id_etudiant"), index=True)
    id_encadrant: Mapped[int] = mapped_column(ForeignKey("encadrant_academique.id_enseignant"))
    sujet: Mapped[str] = mapped_column(String(255))
    date_debut: Mapped[date] = mapped_column(Date)
    date_fin: Mapped[date] = mapped_column(Date)
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")

    encadrant: Mapped[EncadrantAcademique] = relationship()
    suivis: Mapped[list["SuiviBienEtre"]] = relationship(back_populates="stage")


class SuiviBienEtre(Base):
    __tablename__ = "suivi_bienetre"
    id_suivi: Mapped[int] = mapped_column(primary_key=True)
    id_stage: Mapped[int] = mapped_column(ForeignKey("stage.id_stage"))
    date: Mapped[date] = mapped_column(Date)
    niveau: Mapped[int] = mapped_column(Integer)  # 1 a 5, donnees fictives
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)

    stage: Mapped[Stage] = relationship(back_populates="suivis")
