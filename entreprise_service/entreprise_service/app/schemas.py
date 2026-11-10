from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

TypeStage = Literal["local", "etranger"]
StatutConvention = Literal["en_attente", "signee", "terminee"]


class EntrepriseCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    pays: str = Field(min_length=1, max_length=80)
    secteur: str = Field(min_length=1, max_length=100)


class EncadrantProCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=150)
    poste: str = Field(min_length=1, max_length=100)


class EncadrantProOut(EncadrantProCreate):
    model_config = ConfigDict(from_attributes=True)
    id_encadrant_pro: int
    id_entreprise: int


class EntrepriseOut(EntrepriseCreate):
    model_config = ConfigDict(from_attributes=True)
    id_entreprise: int
    encadrants: list[EncadrantProOut] = []


class ConventionCreate(BaseModel):
    id_stage: int
    id_entreprise: int
    id_encadrant_pro: int
    type_stage: TypeStage
    pays: Optional[str] = Field(default=None, max_length=80)  # 'Tunisie' par defaut pour un stage local


class StatutUpdate(BaseModel):
    statut: StatutConvention


class ConventionOut(BaseModel):
    """Contrat d'API : reponse de GET /conventions?id_stage=..."""
    id_convention: int
    id_stage: int
    type_stage: TypeStage
    pays: str
    entreprise: str
    encadrant_professionnel: str
    statut: StatutConvention
