"""Routes des livraisons (35 à 38)."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_accueil
from app.models import Utilisateur
from app.schemas.commande import CommandeRead
from app.schemas.livraison import (
    LivraisonConfirmer,
    LivraisonPlanifier,
    LivraisonRead,
    LivraisonTournee,
    StatutLivraison,
)
from app.services import livraison_service

router_commande = APIRouter(
    prefix="/commandes/{commande_id}/livraison",
    tags=["Livraisons"],
    dependencies=[Depends(get_current_user)],
)
router = APIRouter(
    prefix="/livraisons", tags=["Livraisons"], dependencies=[Depends(get_current_user)]
)


@router_commande.put(
    "", response_model=LivraisonRead, dependencies=[Depends(require_accueil)]
)
def planifier(
    commande_id: int, donnees: LivraisonPlanifier, db: Session = Depends(get_db)
):
    livraison = livraison_service.planifier(db, commande_id, donnees)
    db.commit()
    return livraison


@router_commande.get("", response_model=LivraisonRead)
def detail(commande_id: int, db: Session = Depends(get_db)):
    return livraison_service.obtenir_livraison(db, commande_id)


@router_commande.post("/confirmer", response_model=CommandeRead)
def confirmer(
    commande_id: int,
    donnees: Optional[LivraisonConfirmer] = None,
    db: Session = Depends(get_db),
    auteur: Utilisateur = Depends(require_accueil),
):
    # Le corps est facultatif : sans corps, on prend les valeurs par défaut
    commande = livraison_service.confirmer(
        db, commande_id, donnees or LivraisonConfirmer(), auteur
    )
    db.commit()
    return commande


@router.get("", response_model=list[LivraisonTournee])
def tournee(
    statut: Optional[StatutLivraison] = None,
    date_min: Optional[date] = None,
    date_max: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return livraison_service.lister_tournee(db, statut, date_min, date_max)
