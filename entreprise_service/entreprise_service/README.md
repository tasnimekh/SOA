# Entreprise Service (TP2) - Equipe 4 - DOS 3 IDL 26/27

## Lancer (le Stage Service doit tourner sur le port 8000)
    pip install -r requirements.txt
    uvicorn app.main:app --port 8001 --reload
Swagger : http://127.0.0.1:8001/docs

Autre adresse du Stage Service : set STAGE_SERVICE_URL=http://127.0.0.1:8000

## Tests (Stage Service simule)
    pytest -v

## Scenario d'integration (les deux services doivent tourner)
    python demo_integration.py
