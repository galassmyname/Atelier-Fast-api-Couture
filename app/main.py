"""Point d'entrée de l'API : création de l'application FastAPI."""

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.routers import auth, catalogue, clients, commandes, mesures, utilisateurs
from app.routers import (
    auth,
    catalogue,
    clients,
    commandes,
    mesures,
    paiements,
    utilisateurs,
)
from app.database import get_db
from app.exceptions import ErreurMetier
from app.routers import auth, utilisateurs

app = FastAPI(
    title="API Atelier de couture",
    description="Gestion des clients, mesures, commandes, paiements et livraisons.",
    version="1.0.0",
)

API_PREFIX = "/api/v1"


@app.exception_handler(ErreurMetier)
def gerer_erreur_metier(request: Request, exc: ErreurMetier):
    """Convertit une erreur métier en réponse {"detail": "..."}."""
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=headers
    )


# Enregistrement des routeurs (on en ajoutera à chaque étape)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(utilisateurs.router, prefix=API_PREFIX)
app.include_router(clients.router, prefix=API_PREFIX)
app.include_router(catalogue.router, prefix=API_PREFIX)
app.include_router(mesures.router_client, prefix=API_PREFIX)
app.include_router(mesures.router, prefix=API_PREFIX)
app.include_router(commandes.router, prefix=API_PREFIX)
app.include_router(paiements.router, prefix=API_PREFIX)
app.include_router(paiements.router_commande, prefix=API_PREFIX)


@app.get("/health", tags=["Santé"])
def health(db: Session = Depends(get_db)):
    """Route de santé (hors préfixe) : vérifie que la base répond."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="La base de données ne répond pas")
    return {"status": "ok"}
