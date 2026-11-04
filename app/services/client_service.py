"""Logique métier des clients."""

import re

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import Client, Commande, Mesure
from app.schemas.client import ClientCreate, ClientUpdate


def _verifier_telephone_libre(
    db: Session, telephone: str, exclure_id: int | None = None
):
    """RG1 : le téléphone est unique. Garder son propre numéro n'est pas un doublon."""
    requete = select(Client).where(Client.telephone == telephone)
    if exclure_id is not None:
        requete = requete.where(Client.id != exclure_id)
    if db.scalar(requete):
        raise ErreurMetier(409, f"Un client existe déjà avec le téléphone {telephone}")


def creer_client(db: Session, donnees: ClientCreate) -> Client:
    _verifier_telephone_libre(db, donnees.telephone)
    client = Client(**donnees.model_dump())
    db.add(client)
    db.flush()
    return client


def lister_clients(
    db: Session, q: str | None, genre: str | None, limit: int, offset: int
):
    """Liste paginée triée par nom puis prénom, avec recherche et filtre."""
    requete = select(Client)
    if q:
        motif = f"%{q}%"
        conditions = [
            Client.nom.ilike(motif),
            Client.prenom.ilike(motif),
            Client.telephone.ilike(motif),
        ]
        # Si on cherche "77 123", on cherche aussi "77123" dans les téléphones
        chiffres = re.sub(r"[\s.\-()]", "", q)
        if chiffres:
            conditions.append(Client.telephone.ilike(f"%{chiffres}%"))
        requete = requete.where(or_(*conditions))
    if genre:
        requete = requete.where(Client.genre == genre)

    # Nombre total (avant pagination)
    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.order_by(Client.nom, Client.prenom).limit(limit).offset(offset)
    ).all()
    return items, total


def obtenir_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise ErreurMetier(404, f"Client {client_id} introuvable")
    return client


def modifier_client(db: Session, client_id: int, donnees: ClientUpdate) -> Client:
    client = obtenir_client(db, client_id)
    changements = donnees.model_dump(exclude_unset=True)
    if "telephone" in changements:
        _verifier_telephone_libre(db, changements["telephone"], exclure_id=client.id)
    for champ, valeur in changements.items():
        setattr(client, champ, valeur)
    db.flush()
    return client


def supprimer_client(db: Session, client_id: int) -> None:
    """RG4 : un client qui a des commandes ne peut pas être supprimé.
    Ses mesures sont supprimées avec lui (cascade du modèle)."""
    client = obtenir_client(db, client_id)
    nb = db.scalar(
        select(func.count(Commande.id)).where(Commande.client_id == client.id)
    )
    if nb:
        raise ErreurMetier(
            409, f"Suppression impossible : ce client a {nb} commande(s)"
        )
    db.delete(client)
    db.flush()


def resume_client(db: Session, client_id: int) -> dict:
    """Synthèse d'un client, commandes annulées exclues."""
    client = obtenir_client(db, client_id)
    nb, ca, paye, derniere = db.execute(
        select(
            func.count(Commande.id),
            func.coalesce(func.sum(Commande.montant_total), 0),
            func.coalesce(func.sum(Commande.montant_paye), 0),
            func.max(Commande.date_commande),
        ).where(Commande.client_id == client.id, Commande.statut != "annulee")
    ).one()
    a_des_mesures = (
        db.scalar(select(func.count(Mesure.id)).where(Mesure.client_id == client.id))
        > 0
    )
    return {
        "nb_commandes": nb,
        "chiffre_affaires": ca,
        "total_paye": paye,
        "solde_du": ca - paye,
        "derniere_commande": derniere,
        "a_des_mesures": a_des_mesures,
    }
