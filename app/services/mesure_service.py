"""Logique métier des mesures (RG2, RG3, RG4)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import CHAMPS_MESURES, Commande, Mesure, Utilisateur
from app.schemas.mesure import MesureCreate, MesureUpdate
from app.services.client_service import obtenir_client


def creer_mesure(
    db: Session, client_id: int, donnees: MesureCreate, auteur: Utilisateur
) -> Mesure:
    """Nouvelle prise : on n'écrase jamais l'ancienne (historique, RG3)."""
    obtenir_client(db, client_id)  # 404 si le client n'existe pas
    valeurs = donnees.model_dump()
    valeurs["date_prise"] = valeurs["date_prise"] or date.today()
    mesure = Mesure(client_id=client_id, prise_par_id=auteur.id, **valeurs)
    db.add(mesure)
    db.flush()
    return mesure


def historique_mesures(db: Session, client_id: int) -> list[Mesure]:
    """Toutes les prises du client, la plus récente d'abord."""
    obtenir_client(db, client_id)
    return list(
        db.scalars(
            select(Mesure)
            .where(Mesure.client_id == client_id)
            .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
        )
    )


def dernieres_mesures(db: Session, client_id: int) -> Mesure | None:
    """RG3 : la prise de date la plus récente (None s'il n'y en a pas).
    Réutilisée par les commandes (RG9)."""
    return db.scalar(
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
        .limit(1)
    )


def obtenir_dernieres_mesures(db: Session, client_id: int) -> Mesure:
    obtenir_client(db, client_id)
    mesure = dernieres_mesures(db, client_id)
    if mesure is None:
        raise ErreurMetier(404, "Ce client n'a encore aucune prise de mesures")
    return mesure


def obtenir_mesure(db: Session, mesure_id: int) -> Mesure:
    mesure = db.get(Mesure, mesure_id)
    if mesure is None:
        raise ErreurMetier(404, f"Prise de mesures {mesure_id} introuvable")
    return mesure


def modifier_mesure(db: Session, mesure_id: int, donnees: MesureUpdate) -> Mesure:
    """Corrige une erreur de saisie. 422 si plus aucune mesure ne resterait."""
    mesure = obtenir_mesure(db, mesure_id)
    changements = donnees.model_dump(exclude_unset=True)

    # On simule le résultat final avant d'enregistrer
    resultat = {c: changements.get(c, getattr(mesure, c)) for c in CHAMPS_MESURES}
    if all(v is None for v in resultat.values()):
        raise ErreurMetier(
            422,
            "La correction supprimerait toutes les mesures : "
            "au moins une doit être renseignée",
        )

    if "date_prise" in changements and changements["date_prise"] is None:
        changements.pop("date_prise")  # on ne vide pas la date

    for champ, valeur in changements.items():
        setattr(mesure, champ, valeur)
    db.flush()
    return mesure


def supprimer_mesure(db: Session, mesure_id: int) -> None:
    """RG4 : des mesures utilisées par une commande ne peuvent pas être supprimées."""
    mesure = obtenir_mesure(db, mesure_id)
    nb = db.scalar(
        select(func.count(Commande.id)).where(Commande.mesure_id == mesure.id)
    )
    if nb:
        raise ErreurMetier(
            409,
            f"Suppression impossible : ces mesures sont utilisées "
            f"par {nb} commande(s)",
        )
    db.delete(mesure)
    db.flush()
