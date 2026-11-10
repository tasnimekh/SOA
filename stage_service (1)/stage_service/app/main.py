from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import insert, update
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stage Service",
    description="Service de gestion des stages (DOS - Equipe 4). Donnees fictives uniquement.",
    version="1.0.0",
)


# Les erreurs de validation renvoient 400 (et non 422) comme demande dans l'enonce.
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    erreurs = [
        {"champ": ".".join(str(x) for x in e["loc"] if x != "body"), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": erreurs})


def to_out(stage: models.Stage) -> schemas.StageOut:
    return schemas.StageOut(
        id_stage=stage.id_stage,
        id_etudiant=stage.id_etudiant,
        encadrant_academique=stage.encadrant.nom,
        sujet=stage.sujet,
        periode=schemas.Periode(debut=stage.date_debut, fin=stage.date_fin),
        statut=stage.statut,
    )


def get_stage_or_404(db: Session, id_stage: int) -> models.Stage:
    stage = db.get(models.Stage, id_stage)
    if stage is None:
        raise HTTPException(status_code=404, detail=f"Stage {id_stage} introuvable")
    return stage


def promouvoir_stagiaire(db: Session, id_etudiant: int) -> None:
    """Etudiant -> Stagiaire (heritage) : meme identifiant, nouvelle ligne dans 'stagiaire'."""
    etu = db.get(models.Etudiant, id_etudiant)
    if etu is None:
        raise HTTPException(status_code=404, detail=f"Etudiant {id_etudiant} introuvable")
    if etu.type == "stagiaire":
        return
    db.execute(insert(models.Stagiaire.__table__).values(id_etudiant=id_etudiant, date_statut=date.today()))
    db.execute(update(models.Etudiant.__table__)
               .where(models.Etudiant.__table__.c.id_etudiant == id_etudiant).values(type="stagiaire"))
    db.expunge(etu)  # l'objet sera recharge comme Stagiaire


def promouvoir_encadrant(db: Session, id_enseignant: int) -> None:
    """Enseignant -> Encadrant academique (heritage) : meme identifiant."""
    ens = db.get(models.Enseignant, id_enseignant)
    if ens is None:
        raise HTTPException(status_code=404, detail=f"Enseignant {id_enseignant} introuvable")
    if ens.type == "encadrant":
        return
    db.execute(insert(models.EncadrantAcademique.__table__).values(id_enseignant=id_enseignant, date_statut=date.today()))
    db.execute(update(models.Enseignant.__table__)
               .where(models.Enseignant.__table__.c.id_enseignant == id_enseignant).values(type="encadrant"))
    db.expunge(ens)


# ---------- Etudiants et enseignants (classes meres) ----------
# Dans le systeme complet, ces donnees viennent des services Etudiants et Enseignants
# de l'ISI (TP de l'enseignant) ; ici ce sont des copies locales minimales.
@app.post("/etudiants", response_model=schemas.EtudiantOut, status_code=201, tags=["Etudiants"])
def creer_etudiant(data: schemas.EtudiantCreate, db: Session = Depends(get_db)):
    etu = models.Etudiant(**data.model_dump())
    db.add(etu)
    db.commit()
    db.refresh(etu)
    return {**data.model_dump(), "id_etudiant": etu.id_etudiant, "statut": etu.type}


@app.get("/etudiants/{id_etudiant}", response_model=schemas.EtudiantOut, tags=["Etudiants"])
def consulter_etudiant(id_etudiant: int, db: Session = Depends(get_db)):
    etu = db.get(models.Etudiant, id_etudiant)
    if etu is None:
        raise HTTPException(status_code=404, detail=f"Etudiant {id_etudiant} introuvable")
    return {"id_etudiant": etu.id_etudiant, "nom": etu.nom, "prenom": etu.prenom, "email": etu.email,
            "classe": etu.classe, "statut": etu.type}


@app.post("/enseignants", response_model=schemas.EnseignantOut, status_code=201, tags=["Enseignants"])
def creer_enseignant(data: schemas.EnseignantCreate, db: Session = Depends(get_db)):
    ens = models.Enseignant(**data.model_dump())
    db.add(ens)
    db.commit()
    db.refresh(ens)
    return {**data.model_dump(), "id_enseignant": ens.id_enseignant, "statut": ens.type}


@app.get("/enseignants/{id_enseignant}", response_model=schemas.EnseignantOut, tags=["Enseignants"])
def consulter_enseignant(id_enseignant: int, db: Session = Depends(get_db)):
    ens = db.get(models.Enseignant, id_enseignant)
    if ens is None:
        raise HTTPException(status_code=404, detail=f"Enseignant {id_enseignant} introuvable")
    return {"id_enseignant": ens.id_enseignant, "nom": ens.nom, "prenom": ens.prenom, "email": ens.email,
            "departement": ens.departement, "statut": ens.type}


# ---------- Stages ----------
@app.post("/stages", response_model=schemas.StageOut, status_code=201, tags=["Stages"])
def creer_stage(data: schemas.StageCreate, db: Session = Depends(get_db)):
    """Creer un stage fait passer l'etudiant au statut Stagiaire et l'enseignant au statut Encadrant."""
    promouvoir_stagiaire(db, data.id_etudiant)
    promouvoir_encadrant(db, data.id_encadrant)
    stage = models.Stage(**data.model_dump())
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return to_out(stage)


@app.get("/stages/{id_stage}", response_model=schemas.StageOut, tags=["Stages"])
def consulter_stage(id_stage: int, db: Session = Depends(get_db)):
    """Contrat d'API commun, appele par les autres services."""
    return to_out(get_stage_or_404(db, id_stage))


@app.put("/stages/{id_stage}", response_model=schemas.StageOut, tags=["Stages"])
def modifier_stage(id_stage: int, data: schemas.StageUpdate, db: Session = Depends(get_db)):
    stage = get_stage_or_404(db, id_stage)
    changes = data.model_dump(exclude_unset=True)
    if "id_encadrant" in changes:
        promouvoir_encadrant(db, changes["id_encadrant"])
    for champ, valeur in changes.items():
        setattr(stage, champ, valeur)
    if stage.date_fin < stage.date_debut:
        db.rollback()
        raise HTTPException(status_code=400, detail="date_fin doit etre posterieure a date_debut")
    db.commit()
    db.refresh(stage)
    return to_out(stage)


# ---------- Suivi de bien-etre (donnees fictives) ----------
@app.post("/stages/{id_stage}/suivi", response_model=schemas.SuiviOut, status_code=201, tags=["Bien-etre"])
def ajouter_suivi(id_stage: int, data: schemas.SuiviCreate, db: Session = Depends(get_db)):
    get_stage_or_404(db, id_stage)
    suivi = models.SuiviBienEtre(id_stage=id_stage, **data.model_dump())
    db.add(suivi)
    db.commit()
    db.refresh(suivi)
    return suivi


@app.get("/stages/{id_stage}/suivi", response_model=list[schemas.SuiviOut], tags=["Bien-etre"])
def lister_suivis(id_stage: int, db: Session = Depends(get_db)):
    get_stage_or_404(db, id_stage)
    return db.query(models.SuiviBienEtre).filter_by(id_stage=id_stage).order_by(models.SuiviBienEtre.date).all()
