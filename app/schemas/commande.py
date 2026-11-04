"""Routes des commandes (24 à 31)."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_accueil
from app.models import Utilisateur
from app.schemas.commande import (
    CommandeCreate,
    CommandeListItem,
    CommandeRead,
    CommandeUpdate,
    HistoriqueRead,
    LigneCreate,
    Statut,
    StatutChange,
)
from app.schemas.common import Page
from app.services import commande_service

router = APIRouter(
    prefix="/commandes", tags=["Commandes"], dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=CommandeRead, status_code=status.HTTP_201_CREATED)
def creer(
    donnees: CommandeCreate,
    db: Session = Depends(get_db),
    auteur: Utilisateur = Depends(require_accueil),
):
    commande = commande_service.creer_commande(db, donnees, auteur)
    db.commit()
    return commande


@router.get("", response_model=Page[CommandeListItem])
def lister(
    statut: Optional[Statut] = None,
    client_id: Optional[int] = None,
    en_retard: Optional[bool] = None,
    date_min: Optional[date] = None,
    date_max: Optional[date] = None,
    numero: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = commande_service.lister_commandes(
        db, statut, client_id, en_retard, date_min, date_max, numero, limit, offset
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{commande_id}", response_model=CommandeRead)
def detail(commande_id: int, db: Session = Depends(get_db)):
    return commande_service.obtenir_commande(db, commande_id)


@router.patch(
    "/{commande_id}",
    response_model=CommandeRead,
    dependencies=[Depends(require_accueil)],
)
def modifier(commande_id: int, donnees: CommandeUpdate, db: Session = Depends(get_db)):
    commande = commande_service.modifier_commande(db, commande_id, donnees)
    db.commit()
    return commande


@router.post("/{commande_id}/statut", response_model=CommandeRead)
def changer_statut(
    commande_id: int,
    donnees: StatutChange,
    db: Session = Depends(get_db),
    auteur: Utilisateur = Depends(get_current_user),
):
    # Tous les rôles : les restrictions (RG13-14) sont dans le service
    commande = commande_service.changer_statut(db, commande_id, donnees, auteur)
    db.commit()
    return commande


@router.get("/{commande_id}/historique", response_model=list[HistoriqueRead])
def historique(commande_id: int, db: Session = Depends(get_db)):
    return commande_service.historique_commande(db, commande_id)


@router.post(
    "/{commande_id}/lignes",
    response_model=CommandeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_accueil)],
)
def ajouter_ligne(
    commande_id: int, donnees: LigneCreate, db: Session = Depends(get_db)
):
    commande = commande_service.ajouter_ligne(db, commande_id, donnees)
    db.commit()
    return commande


@router.delete(
    "/{commande_id}/lignes/{ligne_id}",
    response_model=CommandeRead,
    dependencies=[Depends(require_accueil)],
)
def supprimer_ligne(commande_id: int, ligne_id: int, db: Session = Depends(get_db)):
    commande = commande_service.supprimer_ligne(db, commande_id, ligne_id)
    db.commit()
    return commande
