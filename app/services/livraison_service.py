"""Logique métier des livraisons (RG18 à RG20)."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import Commande, Livraison, Utilisateur
from app.schemas.livraison import LivraisonConfirmer, LivraisonPlanifier
from app.services.commande_service import (
    ajouter_historique,
    obtenir_commande,
    verifier_modifiable,
)


def planifier(db: Session, commande_id: int, donnees: LivraisonPlanifier) -> Livraison:
    """Planifie ou replanifie, sans jamais créer une seconde livraison (RG18)."""
    commande = obtenir_commande(db, commande_id)
    verifier_modifiable(commande)  # 409 si livrée ou annulée

    if donnees.date_prevue < commande.date_commande:
        raise ErreurMetier(
            422, "La date de livraison ne peut pas précéder " "la date de commande"
        )

    livraison = commande.livraison
    if livraison is None:
        livraison = Livraison(statut="planifiee")
        commande.livraison = livraison  # première planification
    # Planification ou replanification : on met à jour les champs
    for champ, valeur in donnees.model_dump().items():
        setattr(livraison, champ, valeur)

    # RG18 : la date prévue de la commande suit la livraison
    commande.date_livraison_prevue = donnees.date_prevue
    db.flush()
    return livraison


def obtenir_livraison(db: Session, commande_id: int) -> Livraison:
    commande = obtenir_commande(db, commande_id)
    if commande.livraison is None:
        raise ErreurMetier(404, "Aucune livraison n'est planifiée pour cette commande")
    return commande.livraison


def confirmer(
    db: Session, commande_id: int, donnees: LivraisonConfirmer, auteur: Utilisateur
) -> Commande:
    """Remise du vêtement au client (RG19, RG20)."""
    commande = obtenir_commande(db, commande_id)

    # RG19 : la commande doit être terminée
    if commande.statut != "terminee":
        raise ErreurMetier(
            409,
            f"Livraison impossible : la commande est « {commande.statut} », "
            f"elle doit être « terminee »",
        )

    # RG19 : elle doit être soldée, sauf autorisation explicite
    commentaire = "Livraison confirmée"
    if commande.solde > 0:
        if not donnees.autoriser_solde_impaye:
            raise ErreurMetier(
                409,
                f"Livraison impossible : il reste {commande.solde} FCFA " f"à payer",
            )
        commentaire = f"Livrée avec un solde impayé de {commande.solde} FCFA"

    date_effective = donnees.date_effective or date.today()
    if date_effective > date.today():
        raise ErreurMetier(
            422, "La date de livraison effective ne peut pas être future"
        )

    # RG20 : sans planification, on crée un retrait à l'atelier
    if commande.livraison is None:
        commande.livraison = Livraison(
            mode="retrait_atelier", date_prevue=date_effective
        )

    commande.livraison.statut = "livree"
    commande.livraison.date_effective = date_effective
    commande.date_livraison_reelle = date_effective

    ancien = commande.statut
    commande.statut = "livree"
    ajouter_historique(db, commande, ancien, "livree", auteur, commentaire)  # RG15
    db.flush()
    return commande


def lister_tournee(
    db: Session, statut=None, date_min=None, date_max=None
) -> list[Livraison]:
    """Liste de tournée triée par date prévue."""
    requete = select(Livraison)
    if statut:
        requete = requete.where(Livraison.statut == statut)
    if date_min:
        requete = requete.where(Livraison.date_prevue >= date_min)
    if date_max:
        requete = requete.where(Livraison.date_prevue <= date_max)
    return list(db.scalars(requete.order_by(Livraison.date_prevue, Livraison.id)))
