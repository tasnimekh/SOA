"""Scenario d'integration : Stage Service (port 8000) + Entreprise Service (port 8001).
Lancer d'abord les deux services, puis :  python demo_integration.py
"""
import httpx

STAGE = "http://127.0.0.1:8000"
ENTR = "http://127.0.0.1:8001"


def etape(titre, r):
    print(f"{titre:<62} -> {r.status_code}")
    return r


# 1. Stage Service : etudiant, enseignant, stage (heritage etudiant -> stagiaire)
etu = etape("Stage : POST /etudiants", httpx.post(f"{STAGE}/etudiants", json={
    "nom": "Ben Salah", "prenom": "Sami", "email": "sami@isi.example", "classe": "3 IDL"})).json()
ens = etape("Stage : POST /enseignants", httpx.post(f"{STAGE}/enseignants", json={
    "nom": "Ben Ali", "prenom": "Karim", "email": "karim@isi.example", "departement": "GLSI"})).json()
stage = etape("Stage : POST /stages", httpx.post(f"{STAGE}/stages", json={
    "id_etudiant": etu["id_etudiant"], "id_encadrant": ens["id_enseignant"], "sujet": "Application de gestion",
    "date_debut": "2027-02-01", "date_fin": "2027-06-30"})).json()
id_stage = stage["id_stage"]

# 2. Entreprise Service : entreprise partenaire + encadrant professionnel
entr = etape("Entreprise : POST /entreprises", httpx.post(f"{ENTR}/entreprises", json={
    "nom": "Entreprise Exemple GmbH", "pays": "Allemagne", "secteur": "Informatique"})).json()
enc = etape("Entreprise : POST /entreprises/{id}/encadrants", httpx.post(
    f"{ENTR}/entreprises/{entr['id_entreprise']}/encadrants", json={
        "nom": "Mme Muller", "email": "muller@exemple.test", "poste": "Responsable technique"})).json()

# 3. Convention pour un stage a l'etranger (appelle le Stage Service pour verifier le stage)
conv = etape("Entreprise : POST /conventions (stage a l'etranger)", httpx.post(f"{ENTR}/conventions", json={
    "id_stage": id_stage, "id_entreprise": entr["id_entreprise"], "id_encadrant_pro": enc["id_encadrant_pro"],
    "type_stage": "etranger", "pays": "Allemagne"})).json()
id_conv = conv["id_convention"]
etape("Entreprise : POST /conventions pour un stage inexistant", httpx.post(f"{ENTR}/conventions", json={
    "id_stage": 999, "id_entreprise": entr["id_entreprise"], "id_encadrant_pro": enc["id_encadrant_pro"],
    "type_stage": "local"}))

# 4. Regle : demarrage refuse tant que la convention n'est pas signee
etape("Entreprise : demarrer SANS convention signee (409 attendu)", httpx.post(f"{ENTR}/conventions/{id_conv}/demarrer"))
etape("Entreprise : PUT statut -> signee", httpx.put(f"{ENTR}/conventions/{id_conv}/statut", json={"statut": "signee"}))
etape("Entreprise : demarrer APRES signature (200 attendu)", httpx.post(f"{ENTR}/conventions/{id_conv}/demarrer"))

# 5. Verification croisee
st = etape("Stage : GET /stages/{id} (statut doit etre en_cours)", httpx.get(f"{STAGE}/stages/{id_stage}")).json()
print("   statut du stage =", st["statut"])
c = etape("Entreprise : GET /conventions?id_stage=...", httpx.get(f"{ENTR}/conventions", params={"id_stage": id_stage})).json()
print("   convention =", c)
