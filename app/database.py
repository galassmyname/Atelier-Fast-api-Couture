"""Connexion à PostgreSQL avec SQLAlchemy 2."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Le moteur gère les connexions à la base.
# pool_pre_ping vérifie qu'une connexion est vivante avant de l'utiliser.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Fabrique de sessions : une session = une "conversation" avec la base
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Classe mère de tous les modèles SQLAlchemy (style moderne)."""

    pass


def get_db():
    """Dépendance FastAPI : ouvre une session par requête
    et la ferme toujours à la fin, même en cas d'erreur."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
