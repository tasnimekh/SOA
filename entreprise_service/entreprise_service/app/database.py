import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Par defaut SQLite. Pour MySQL :
# export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/entreprise_db"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./entreprise.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
