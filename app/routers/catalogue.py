"""Routes du catalogue (14 à 17)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.schemas.catalogue import (
    TypeVetementCreate,
    TypeVetementRead,
    TypeVetementUpdate,
)
from app.services import catalogue_service

router = APIRouter(
    prefix="/catalogue", tags=["Catalogue"], dependencies=[Depends(get_current_user)]
)


@router.post(
    "",
    response_model=TypeVetementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def creer(donnees: TypeVetementCreate, db: Session = Depends(get_db)):
    prestation = catalogue_service.creer_prestation(db, donnees)
    db.commit()
    return prestation


@router.get("", response_model=list[TypeVetementRead])
def lister(actifs_seulement: bool = True, db: Session = Depends(get_db)):
    return catalogue_service.lister_prestations(db, actifs_seulement)


@router.get("/{prestation_id}", response_model=TypeVetementRead)
def detail(prestation_id: int, db: Session = Depends(get_db)):
    return catalogue_service.obtenir_prestation(db, prestation_id)


@router.patch(
    "/{prestation_id}",
    response_model=TypeVetementRead,
    dependencies=[Depends(require_admin)],
)
def modifier(
    prestation_id: int, donnees: TypeVetementUpdate, db: Session = Depends(get_db)
):
    prestation = catalogue_service.modifier_prestation(db, prestation_id, donnees)
    db.commit()
    return prestation
