"""Point d'entrée de l'API : création de l'application FastAPI."""

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

app = FastAPI(
    title="API Atelier de couture",
    description="Gestion des clients, mesures, commandes, paiements et livraisons.",
    version="1.0.0",
)

# Préfixe commun à toutes les routes métier (les routeurs seront ajoutés ici)
API_PREFIX = "/api/v1"


@app.get("/health", tags=["Santé"])
def health(db: Session = Depends(get_db)):
    """Route de santé (hors préfixe) : vérifie que la base répond."""
    try:
        db.execute(text("SELECT 1"))  # requête minimale pour tester la base
    except Exception:
        raise HTTPException(status_code=503, detail="La base de données ne répond pas")
    return {"status": "ok"}
