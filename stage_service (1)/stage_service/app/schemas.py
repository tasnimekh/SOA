from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, EmailStr, model_validator, ConfigDict

Statut = Literal["en_attente", "en_cours", "termine"]


class EtudiantCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=150)
    classe: str = Field(min_length=1, max_length=50)


class EtudiantOut(EtudiantCreate):
    model_config = ConfigDict(from_attributes=True)
    id_etudiant: int
    statut: Literal["etudiant", "stagiaire"]


class EnseignantCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=150)
    departement: str = Field(min_length=1, max_length=100)


class EnseignantOut(EnseignantCreate):
    model_config = ConfigDict(from_attributes=True)
    id_enseignant: int
    statut: Literal["enseignant", "encadrant"]


class StageCreate(BaseModel):
    id_etudiant: int
    id_encadrant: int
    sujet: str = Field(min_length=1, max_length=255)
    date_debut: date
    date_fin: date
    statut: Statut = "en_attente"

    @model_validator(mode="after")
    def dates_coherentes(self):
        if self.date_fin < self.date_debut:
            raise ValueError("date_fin doit etre posterieure ou egale a date_debut")
        return self


class StageUpdate(BaseModel):
    id_encadrant: Optional[int] = None
    sujet: Optional[str] = Field(default=None, min_length=1, max_length=255)
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    statut: Optional[Statut] = None


class Periode(BaseModel):
    debut: date
    fin: date


class StageOut(BaseModel):
    """Contrat d'API commun : reponse de GET /stages/{id_stage}."""
    id_stage: int
    id_etudiant: int
    encadrant_academique: str
    sujet: str
    periode: Periode
    statut: Statut


class SuiviCreate(BaseModel):
    date: date
    niveau: int = Field(ge=1, le=5)
    commentaire: Optional[str] = Field(default=None, max_length=500)


class SuiviOut(SuiviCreate):
    model_config = ConfigDict(from_attributes=True)
    id_suivi: int
    id_stage: int
