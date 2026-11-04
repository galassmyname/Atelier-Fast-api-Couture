"""Logique métier des paiements (RG16, RG17)."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import Paiement, Utilisateur
from app.schemas.paiement import PaiementCreate
from app.services.commande_service import obtenir_commande, recalculer_montants


def encaisser(
    db: Session, commande_id: int, donnees: PaiementCreate, auteur: Utilisateur
) -> Paiement:
    """Enregistre un acompte ou le solde d'une commande."""
    commande = obtenir_commande(db, commande_id)

    # RG16 : refusé sur une commande annulée
    if commande.statut == "annulee":
        raise ErreurMetier(
            409, "Impossible d'encaisser un paiement sur une commande annulée"
        )

    # RG16 : pas de date future
    date_paiement = donnees.date_paiement or date.today()
    if date_paiement > date.today():
        raise ErreurMetier(422, "La date de paiement ne peut pas être dans le futur")

    # RG16 : ne peut pas dépasser le solde restant
    if donnees.montant > commande.solde:
        raise ErreurMetier(
            409,
            f"Le paiement ({donnees.montant} FCFA) dépasse le solde "
            f"restant ({commande.solde} FCFA)",
        )

    paiement = Paiement(
        montant=donnees.montant,
        mode=donnees.mode,
        reference=donnees.reference,
        date_paiement=date_paiement,
        enregistre_par_id=auteur.id,
    )
    commande.paiements.append(paiement)
    recalculer_montants(commande)  # met à jour montant_paye (RG7)
    db.flush()
    return paiement


def lister_paiements(db: Session, commande_id: int) -> list[Paiement]:
    """Paiements d'une commande, dans l'ordre de saisie."""
    obtenir_commande(db, commande_id)
    return list(
        db.scalars(
            select(Paiement)
            .where(Paiement.commande_id == commande_id)
            .order_by(Paiement.id)
        )
    )


def annuler_paiement(db: Session, paiement_id: int) -> None:
    """RG17 : supprimer un paiement saisi par erreur recalcule payé et solde."""
    paiement = db.get(Paiement, paiement_id)
    if paiement is None:
        raise ErreurMetier(404, f"Paiement {paiement_id} introuvable")
    commande = paiement.commande
    commande.paiements.remove(paiement)  # supprimé grâce à delete-orphan
    recalculer_montants(commande)
    db.flush()
