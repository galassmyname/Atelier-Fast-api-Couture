"""Routes des clients (7 à 11 et 13)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.schemas.commande import CommandeListItem
from app.services import commande_service
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.schemas.client import (
    ClientCreate,
    ClientRead,
    ClientResume,
    ClientUpdate,
    Genre,
)
from app.schemas.common import Page
from app.services import client_service

# Toutes les routes exigent au minimum d'être connecté
router = APIRouter(
    prefix="/clients", tags=["Clients"], dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def creer(donnees: ClientCreate, db: Session = Depends(get_db)):
    client = client_service.creer_client(db, donnees)
    db.commit()
    return client


@router.get("", response_model=Page[ClientRead])
def lister(
    q: Optional[str] = Query(default=None, min_length=2),
    genre: Optional[Genre] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = client_service.lister_clients(db, q, genre, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{client_id}", response_model=ClientRead)
def detail(client_id: int, db: Session = Depends(get_db)):
    return client_service.obtenir_client(db, client_id)


@router.patch("/{client_id}", response_model=ClientRead)
def modifier(client_id: int, donnees: ClientUpdate, db: Session = Depends(get_db)):
    client = client_service.modifier_client(db, client_id, donnees)
    db.commit()
    return client


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def supprimer(client_id: int, db: Session = Depends(get_db)):
    client_service.supprimer_client(db, client_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{client_id}/resume", response_model=ClientResume)
def resume(client_id: int, db: Session = Depends(get_db)):
    return client_service.resume_client(db, client_id)


@router.get("/{client_id}/commandes", response_model=Page[CommandeListItem])
def commandes_du_client(
    client_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Commandes du client, la plus récente d'abord."""
    items, total = commande_service.commandes_du_client(db, client_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
