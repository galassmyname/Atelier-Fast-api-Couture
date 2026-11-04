"""Routes des statistiques (39 à 43), réservées à l'admin."""

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.schemas.commande import CommandeListItem
from app.schemas.common import Page
from app.schemas.statistiques import (
    PeriodeCA,
    StatTypeVetement,
    TableauDeBord,
    TopClient,
)
from app.services import statistiques_service as stats

# require_admin sur tout le routeur : 403 pour les autres rôles
router = APIRouter(
    prefix="/statistiques", tags=["Statistiques"], dependencies=[Depends(require_admin)]
)


@router.get("/tableau-de-bord", response_model=TableauDeBord)
def tableau_de_bord(db: Session = Depends(get_db)):
    return stats.tableau_de_bord(db)


@router.get("/chiffre-affaires", response_model=list[PeriodeCA])
def chiffre_affaires(
    granularite: Literal["jour", "mois"] = "jour",
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return stats.chiffre_affaires(db, granularite, date_debut, date_fin)


@router.get("/types-vetement", response_model=list[StatTypeVetement])
def types_vetement(
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return stats.par_type_vetement(db, date_debut, date_fin)


@router.get("/top-clients", response_model=list[TopClient])
def top_clients(
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return stats.top_clients(db, date_debut, date_fin, limite)


@router.get("/impayes", response_model=Page[CommandeListItem])
def impayes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = stats.impayes(db, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
