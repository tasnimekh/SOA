import os
os.environ["DATABASE_URL"] = "sqlite:///./test_stage.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def base_propre():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def creer_etudiant():
    r = client.post("/etudiants", json={"nom": "Ben Salah", "prenom": "Sami", "email": "sami@isi.example", "classe": "3 IDL"})
    assert r.status_code == 201
    return r.json()["id_etudiant"]


def creer_enseignant():
    r = client.post("/enseignants", json={"nom": "Ben Ali", "prenom": "Karim", "email": "karim@isi.example", "departement": "GLSI"})
    assert r.status_code == 201
    return r.json()["id_enseignant"]


def stage_valide(id_etu, id_ens, **extra):
    data = {"id_etudiant": id_etu, "id_encadrant": id_ens, "sujet": "Application de gestion (fictive)",
            "date_debut": "2027-02-01", "date_fin": "2027-06-30"}
    data.update(extra)
    return data


def nouveau_stage():
    id_etu, id_ens = creer_etudiant(), creer_enseignant()
    r = client.post("/stages", json=stage_valide(id_etu, id_ens))
    assert r.status_code == 201
    return r.json()["id_stage"]


def test_01_creation_stage_et_contrat_api():
    id_etu, id_ens = creer_etudiant(), creer_enseignant()
    r = client.post("/stages", json=stage_valide(id_etu, id_ens))
    assert r.status_code == 201
    corps = client.get(f"/stages/{r.json()['id_stage']}").json()
    assert corps["encadrant_academique"] == "Ben Ali"
    assert corps["id_etudiant"] == id_etu
    assert corps["periode"] == {"debut": "2027-02-01", "fin": "2027-06-30"}
    assert {"id_stage", "id_etudiant", "encadrant_academique", "periode", "statut"} <= set(corps)


def test_02_stage_inexistant_404():
    assert client.get("/stages/999").status_code == 404


def test_03_dates_invalides_400():
    id_etu, id_ens = creer_etudiant(), creer_enseignant()
    r = client.post("/stages", json=stage_valide(id_etu, id_ens, date_debut="2027-06-30", date_fin="2027-02-01"))
    assert r.status_code == 400


def test_04_ajout_suivi_bienetre():
    id_stage = nouveau_stage()
    r = client.post(f"/stages/{id_stage}/suivi", json={"date": "2027-03-01", "niveau": 4, "commentaire": "ok (fictif)"})
    assert r.status_code == 201
    assert len(client.get(f"/stages/{id_stage}/suivi").json()) == 1


def test_05_niveau_hors_limites_400():
    id_stage = nouveau_stage()
    for niveau in (0, 6):
        r = client.post(f"/stages/{id_stage}/suivi", json={"date": "2027-03-01", "niveau": niveau})
        assert r.status_code == 400


def test_06_modification_statut():
    id_stage = nouveau_stage()
    r = client.put(f"/stages/{id_stage}", json={"statut": "en_cours"})
    assert r.status_code == 200 and r.json()["statut"] == "en_cours"


def test_07_heritage_etudiant_devient_stagiaire():
    id_etu, id_ens = creer_etudiant(), creer_enseignant()
    assert client.get(f"/etudiants/{id_etu}").json()["statut"] == "etudiant"
    client.post("/stages", json=stage_valide(id_etu, id_ens))
    assert client.get(f"/etudiants/{id_etu}").json()["statut"] == "stagiaire"
    # un deuxieme stage ne casse rien (promotion deja faite)
    assert client.post("/stages", json=stage_valide(id_etu, id_ens)).status_code == 201


def test_08_heritage_enseignant_devient_encadrant():
    id_etu, id_ens = creer_etudiant(), creer_enseignant()
    assert client.get(f"/enseignants/{id_ens}").json()["statut"] == "enseignant"
    client.post("/stages", json=stage_valide(id_etu, id_ens))
    assert client.get(f"/enseignants/{id_ens}").json()["statut"] == "encadrant"


def test_09_etudiant_ou_enseignant_inexistant_404():
    id_etu, id_ens = creer_etudiant(), creer_enseignant()
    assert client.post("/stages", json=stage_valide(999, id_ens)).status_code == 404
    assert client.post("/stages", json=stage_valide(id_etu, 999)).status_code == 404
    # rien n'a change : l'etudiant reste etudiant apres l'echec
    assert client.get(f"/etudiants/{id_etu}").json()["statut"] == "etudiant"
