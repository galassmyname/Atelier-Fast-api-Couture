"""Routes des paiements (32 à 34)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_accueil, require_admin
from app.models import Utilisateur
from app.schemas.paiement import PaiementCreate, PaiementRead
from app.services import paiement_service

# Routes rattachées à une commande
router_commande = APIRouter(
    prefix="/commandes/{commande_id}/paiements",
    tags=["Paiements"],
    dependencies=[Depends(get_current_user)],
)
# Route sur un paiement précis
router = APIRouter(
    prefix="/paiements", tags=["Paiements"], dependencies=[Depends(get_current_user)]
)


@router_commande.post(
    "", response_model=PaiementRead, status_code=status.HTTP_201_CREATED
)
def encaisser(
    commande_id: int,
    donnees: PaiementCreate,
    db: Session = Depends(get_db),
    auteur: Utilisateur = Depends(require_accueil),
):
    paiement = paiement_service.encaisser(db, commande_id, donnees, auteur)
    db.commit()
    return paiement


@router_commande.get("", response_model=list[PaiementRead])
def lister(commande_id: int, db: Session = Depends(get_db)):
    return paiement_service.lister_paiements(db, commande_id)


@router.delete(
    "/{paiement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def annuler(paiement_id: int, db: Session = Depends(get_db)):
    paiement_service.annuler_paiement(db, paiement_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
