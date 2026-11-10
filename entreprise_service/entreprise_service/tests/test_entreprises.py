import os
os.environ["DATABASE_URL"] = "sqlite:///./test_entreprise.db"

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.stage_client import get_stage_client

client = TestClient(app)


class FauxStageClient:
    """Remplace le Stage Service pendant les tests."""
    def __init__(self):
        self.stages = {12: {"id_stage": 12, "id_etudiant": 3045, "encadrant_academique": "Ben Ali",
                            "periode": {"debut": "2027-02-01", "fin": "2027-06-30"}, "statut": "en_attente"},
                       13: {"id_stage": 13, "id_etudiant": 3046, "encadrant_academique": "Ben Ali",
                            "periode": {"debut": "2027-02-01", "fin": "2027-06-30"}, "statut": "en_attente"}}
        self.indisponible = False

    def get_stage(self, id_stage):
        if self.indisponible:
            raise HTTPException(status_code=503, detail="Stage Service indisponible")
        return self.stages.get(id_stage)

    def demarrer_stage(self, id_stage):
        self.stages[id_stage]["statut"] = "en_cours"
        return self.stages[id_stage]


faux = FauxStageClient()


@pytest.fixture(autouse=True)
def base_propre():
    global faux
    faux = FauxStageClient()
    app.dependency_overrides[get_stage_client] = lambda: faux
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()


def creer_entreprise_et_encadrant(nom="Entreprise Test"):
    e = client.post("/entreprises", json={"nom": nom, "pays": "Allemagne", "secteur": "Informatique"}).json()
    enc = client.post(f"/entreprises/{e['id_entreprise']}/encadrants",
                      json={"nom": "Mme Muller", "email": "muller@exemple.test", "poste": "Responsable technique"})
    assert enc.status_code == 201
    return e["id_entreprise"], enc.json()["id_encadrant_pro"]


def convention(id_ent, id_enc, **extra):
    data = {"id_stage": 12, "id_entreprise": id_ent, "id_encadrant_pro": id_enc, "type_stage": "local"}
    data.update(extra)
    return client.post("/conventions", json=data)


def test_01_entreprise_et_encadrant_pro():
    id_ent, _ = creer_entreprise_et_encadrant()
    r = client.get(f"/entreprises/{id_ent}")
    assert r.status_code == 200
    assert r.json()["encadrants"][0]["poste"] == "Responsable technique"
    assert client.get("/entreprises/999").status_code == 404


def test_02_convention_locale_et_contrat_api():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    r = convention(id_ent, id_enc)
    assert r.status_code == 201
    c = client.get("/conventions", params={"id_stage": 12}).json()
    assert c["type_stage"] == "local" and c["pays"] == "Tunisie"
    assert c["entreprise"] == "Entreprise Test" and c["encadrant_professionnel"] == "Mme Muller"
    assert c["statut"] == "en_attente"


def test_03_stage_inexistant_404():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    assert convention(id_ent, id_enc, id_stage=999).status_code == 404


def test_04_encadrant_d_une_autre_entreprise_400():
    id_ent, _ = creer_entreprise_et_encadrant("Entreprise A")
    _, id_enc_autre = creer_entreprise_et_encadrant("Entreprise B")
    assert convention(id_ent, id_enc_autre).status_code == 400


def test_05_incoherence_type_pays_400():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    assert convention(id_ent, id_enc, type_stage="local", pays="Allemagne").status_code == 400
    assert convention(id_ent, id_enc, type_stage="etranger", pays="Tunisie").status_code == 400
    assert convention(id_ent, id_enc, type_stage="etranger").status_code == 400  # pays manquant


def test_06_stage_etranger_exige_convention_signee():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    id_conv = convention(id_ent, id_enc, type_stage="etranger", pays="Allemagne").json()["id_convention"]
    assert client.post(f"/conventions/{id_conv}/demarrer").status_code == 409
    assert faux.stages[12]["statut"] == "en_attente"
    r = client.put(f"/conventions/{id_conv}/statut", json={"statut": "signee"})
    assert r.status_code == 200 and r.json()["statut"] == "signee"
    assert client.post(f"/conventions/{id_conv}/demarrer").status_code == 200
    assert faux.stages[12]["statut"] == "en_cours"


def test_07_stage_local_demarre_sans_signature():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    id_conv = convention(id_ent, id_enc).json()["id_convention"]
    assert client.post(f"/conventions/{id_conv}/demarrer").status_code == 200
    assert faux.stages[12]["statut"] == "en_cours"


def test_08_une_seule_convention_par_stage_409():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    assert convention(id_ent, id_enc).status_code == 201
    assert convention(id_ent, id_enc).status_code == 409


def test_09_stage_service_indisponible_503():
    id_ent, id_enc = creer_entreprise_et_encadrant()
    faux.indisponible = True
    assert convention(id_ent, id_enc).status_code == 503


def test_10_convention_inexistante_et_statut_invalide():
    assert client.get("/conventions", params={"id_stage": 12}).status_code == 404
    id_ent, id_enc = creer_entreprise_et_encadrant()
    id_conv = convention(id_ent, id_enc).json()["id_convention"]
    assert client.put(f"/conventions/{id_conv}/statut", json={"statut": "annulee"}).status_code == 400
