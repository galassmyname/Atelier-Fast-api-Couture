"""Gestion des comptes, réservée à l'admin (routes 3 à 6).
Le routeur vérifie les droits, appelle le service, puis valide la transaction."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import Utilisateur
from app.schemas.utilisateur import (
    UtilisateurCreate,
    UtilisateurRead,
    UtilisateurUpdate,
)
from app.services import utilisateur_service

router = APIRouter(prefix="/utilisateurs", tags=["Utilisateurs"])


@router.post(
    "",
    response_model=UtilisateurRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def creer(donnees: UtilisateurCreate, db: Session = Depends(get_db)):
    utilisateur = utilisateur_service.creer_utilisateur(db, donnees)
    db.commit()
    return utilisateur


@router.get(
    "", response_model=list[UtilisateurRead], dependencies=[Depends(require_admin)]
)
def lister(db: Session = Depends(get_db)):
    return utilisateur_service.lister_utilisateurs(db)


@router.get(
    "/{utilisateur_id}",
    response_model=UtilisateurRead,
    dependencies=[Depends(require_admin)],
)
def detail(utilisateur_id: int, db: Session = Depends(get_db)):
    return utilisateur_service.obtenir_utilisateur(db, utilisateur_id)


@router.patch("/{utilisateur_id}", response_model=UtilisateurRead)
def modifier(
    utilisateur_id: int,
    donnees: UtilisateurUpdate,
    db: Session = Depends(get_db),
    admin: Utilisateur = Depends(require_admin),
):
    # On a besoin de l'admin connecté pour appliquer RG24
    utilisateur = utilisateur_service.modifier_utilisateur(
        db, utilisateur_id, donnees, admin
    )
    db.commit()
    return utilisateur
