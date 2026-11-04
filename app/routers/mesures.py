"""Routes des mesures (18 à 23)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_tailleur
from app.models import Utilisateur
from app.schemas.mesure import MesureCreate, MesureRead, MesureUpdate
from app.services import mesure_service

# Routes rattachées à un client
router_client = APIRouter(
    prefix="/clients/{client_id}/mesures",
    tags=["Mesures"],
    dependencies=[Depends(get_current_user)],
)
# Routes sur une prise de mesures précise
router = APIRouter(
    prefix="/mesures", tags=["Mesures"], dependencies=[Depends(get_current_user)]
)


@router_client.post("", response_model=MesureRead, status_code=status.HTTP_201_CREATED)
def creer(
    client_id: int,
    donnees: MesureCreate,
    db: Session = Depends(get_db),
    tailleur: Utilisateur = Depends(require_tailleur),
):
    # prise_par_id = le tailleur connecté
    mesure = mesure_service.creer_mesure(db, client_id, donnees, tailleur)
    db.commit()
    return mesure


@router_client.get("", response_model=list[MesureRead])
def historique(client_id: int, db: Session = Depends(get_db)):
    return mesure_service.historique_mesures(db, client_id)


@router_client.get("/derniere", response_model=MesureRead)
def derniere(client_id: int, db: Session = Depends(get_db)):
    return mesure_service.obtenir_dernieres_mesures(db, client_id)


@router.get("/{mesure_id}", response_model=MesureRead)
def detail(mesure_id: int, db: Session = Depends(get_db)):
    return mesure_service.obtenir_mesure(db, mesure_id)


@router.patch(
    "/{mesure_id}", response_model=MesureRead, dependencies=[Depends(require_tailleur)]
)
def modifier(mesure_id: int, donnees: MesureUpdate, db: Session = Depends(get_db)):
    mesure = mesure_service.modifier_mesure(db, mesure_id, donnees)
    db.commit()
    return mesure


@router.delete(
    "/{mesure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tailleur)],
)
def supprimer(mesure_id: int, db: Session = Depends(get_db)):
    mesure_service.supprimer_mesure(db, mesure_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
