from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .stage_client import StageClient, get_stage_client

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Entreprise Service",
    description="Entreprises partenaires, encadrants professionnels et conventions de stage "
                "(locaux et a l'etranger). DOS - Equipe 4. Donnees fictives uniquement.",
    version="1.0.0",
)

PAYS_LOCAL = "Tunisie"


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    erreurs = [
        {"champ": ".".join(str(x) for x in e["loc"] if x != "body"), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": erreurs})


def convention_out(c: models.Convention) -> schemas.ConventionOut:
    return schemas.ConventionOut(
        id_convention=c.id_convention, id_stage=c.id_stage, type_stage=c.type_stage, pays=c.pays,
        entreprise=c.entreprise.nom, encadrant_professionnel=c.encadrant.nom, statut=c.statut,
    )


def get_convention_or_404(db: Session, id_convention: int) -> models.Convention:
    c = db.get(models.Convention, id_convention)
    if c is None:
        raise HTTPException(status_code=404, detail=f"Convention {id_convention} introuvable")
    return c


# ---------- Entreprises ----------
@app.post("/entreprises", response_model=schemas.EntrepriseOut, status_code=201, tags=["Entreprises"])
def creer_entreprise(data: schemas.EntrepriseCreate, db: Session = Depends(get_db)):
    e = models.Entreprise(**data.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@app.get("/entreprises/{id_entreprise}", response_model=schemas.EntrepriseOut, tags=["Entreprises"])
def consulter_entreprise(id_entreprise: int, db: Session = Depends(get_db)):
    e = db.get(models.Entreprise, id_entreprise)
    if e is None:
        raise HTTPException(status_code=404, detail=f"Entreprise {id_entreprise} introuvable")
    return e


@app.post("/entreprises/{id_entreprise}/encadrants", response_model=schemas.EncadrantProOut,
          status_code=201, tags=["Entreprises"])
def ajouter_encadrant_pro(id_entreprise: int, data: schemas.EncadrantProCreate, db: Session = Depends(get_db)):
    if db.get(models.Entreprise, id_entreprise) is None:
        raise HTTPException(status_code=404, detail=f"Entreprise {id_entreprise} introuvable")
    enc = models.EncadrantPro(id_entreprise=id_entreprise, **data.model_dump())
    db.add(enc)
    db.commit()
    db.refresh(enc)
    return enc


# ---------- Conventions ----------
@app.post("/conventions", response_model=schemas.ConventionOut, status_code=201, tags=["Conventions"])
def creer_convention(data: schemas.ConventionCreate, db: Session = Depends(get_db),
                     stages: StageClient = Depends(get_stage_client)):
    # 1. le stage doit exister (appel au Stage Service)
    if stages.get_stage(data.id_stage) is None:
        raise HTTPException(status_code=404, detail=f"Stage {data.id_stage} introuvable (Stage Service)")
    # 2. entreprise et encadrant professionnel
    if db.get(models.Entreprise, data.id_entreprise) is None:
        raise HTTPException(status_code=404, detail=f"Entreprise {data.id_entreprise} introuvable")
    enc = db.get(models.EncadrantPro, data.id_encadrant_pro)
    if enc is None:
        raise HTTPException(status_code=404, detail=f"Encadrant professionnel {data.id_encadrant_pro} introuvable")
    if enc.id_entreprise != data.id_entreprise:
        raise HTTPException(status_code=400, detail="Cet encadrant n'appartient pas a l'entreprise choisie")
    # 3. une seule convention par stage
    if db.query(models.Convention).filter_by(id_stage=data.id_stage).first():
        raise HTTPException(status_code=409, detail="Ce stage a deja une convention")
    # 4. coherence type de stage / pays
    pays = data.pays or (PAYS_LOCAL if data.type_stage == "local" else None)
    if pays is None:
        raise HTTPException(status_code=400, detail="Le pays est obligatoire pour un stage a l'etranger")
    if data.type_stage == "local" and pays != PAYS_LOCAL:
        raise HTTPException(status_code=400, detail=f"Un stage local se deroule en {PAYS_LOCAL}")
    if data.type_stage == "etranger" and pays == PAYS_LOCAL:
        raise HTTPException(status_code=400, detail=f"Un stage a l'etranger ne peut pas se derouler en {PAYS_LOCAL}")

    c = models.Convention(id_stage=data.id_stage, id_entreprise=data.id_entreprise,
                          id_encadrant_pro=data.id_encadrant_pro, type_stage=data.type_stage, pays=pays)
    db.add(c)
    db.commit()
    db.refresh(c)
    return convention_out(c)


@app.get("/conventions", response_model=schemas.ConventionOut, tags=["Conventions"])
def convention_du_stage(id_stage: int, db: Session = Depends(get_db)):
    """Contrat d'API commun : la convention d'un stage (appelee par le Soutenance Service)."""
    c = db.query(models.Convention).filter_by(id_stage=id_stage).first()
    if c is None:
        raise HTTPException(status_code=404, detail=f"Aucune convention pour le stage {id_stage}")
    return convention_out(c)


@app.get("/conventions/{id_convention}", response_model=schemas.ConventionOut, tags=["Conventions"])
def consulter_convention(id_convention: int, db: Session = Depends(get_db)):
    return convention_out(get_convention_or_404(db, id_convention))


@app.put("/conventions/{id_convention}/statut", response_model=schemas.ConventionOut, tags=["Conventions"])
def changer_statut(id_convention: int, data: schemas.StatutUpdate, db: Session = Depends(get_db)):
    c = get_convention_or_404(db, id_convention)
    c.statut = data.statut
    db.commit()
    db.refresh(c)
    return convention_out(c)


@app.post("/conventions/{id_convention}/demarrer", tags=["Conventions"])
def demarrer_stage(id_convention: int, db: Session = Depends(get_db),
                   stages: StageClient = Depends(get_stage_client)):
    """Demarre le stage (statut 'en_cours' dans le Stage Service).
    Regle : un stage a l'etranger exige une convention 'signee' (409 sinon)."""
    c = get_convention_or_404(db, id_convention)
    if c.type_stage == "etranger" and c.statut != "signee":
        raise HTTPException(status_code=409, detail="Stage a l'etranger : la convention doit etre signee avant le demarrage")
    return stages.demarrer_stage(c.id_stage)
