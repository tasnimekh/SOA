# Stage Service (TP1) - Equipe 4 - DOS 3 IDL 26/27

## Lancer
    pip install -r requirements.txt
    uvicorn app.main:app --reload
Swagger : http://127.0.0.1:8000/docs

Par defaut la base est SQLite (stage.db). Pour MySQL :
    mysql < schema_mysql.sql
    export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/stage_db"

## Tests
    python -m pytest -v
