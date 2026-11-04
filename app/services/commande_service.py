"""Logique métier des commandes : montants, statuts, lignes (RG5 à RG15)."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import (
    Commande,
    HistoriqueStatut,
    LigneCommande,
    Mesure,
    TypeVetement,
    Utilisateur,
)
from app.schemas.commande import (
    CommandeCreate,
    CommandeUpdate,
    LigneCreate,
    StatutChange,
)
from app.services.client_service import obtenir_client
from app.services.mesure_service import dernieres_mesures

# Workflow des statuts (section 6). "livree" n'est posé que par la confirmation de livraison.
TRANSITIONS: dict[str, set[str]] = {
    "en_attente": {"en_coupe", "annulee"},
    "en_coupe": {"en_couture", "annulee"},
    "en_couture": {"essayage", "terminee", "annulee"},
    "essayage": {"retouches", "terminee", "annulee"},
    "retouches": {"essayage", "terminee", "annulee"},
    "terminee": {"livree"},
    "livree": set(),
    "annulee": set(),
}
STATUTS_FINAUX = {"livree", "annulee"}


# ---------- Fonctions utilitaires ----------
def ajouter_historique(
    db: Session,
    commande: Commande,
    ancien: str | None,
    nouveau: str,
    auteur: Utilisateur,
    commentaire: str | None = None,
):
    """RG15 : chaque changement de statut est tracé."""
    db.add(
        HistoriqueStatut(
            commande_id=commande.id,
            ancien_statut=ancien,
            nouveau_statut=nouveau,
            commentaire=commentaire,
            utilisateur_id=auteur.id,
        )
    )


def recalculer_montants(commande: Commande) -> None:
    """RG7 : total = somme(quantité × prix) − remise ; payé = somme des paiements."""
    somme_prestations = sum(l.quantite * l.prix_unitaire for l in commande.lignes)
    if commande.remise > somme_prestations:
        raise ErreurMetier(
            422,
            f"La remise ({commande.remise} FCFA) dépasse la somme "
            f"des prestations ({somme_prestations} FCFA)",
        )
    total = somme_prestations - commande.remise
    paye = sum(p.montant for p in commande.paiements)
    if total < paye:
        raise ErreurMetier(
            409,
            f"Le nouveau total ({total} FCFA) serait inférieur "
            f"au montant déjà payé ({paye} FCFA)",
        )
    commande.montant_total = total
    commande.montant_paye = paye


def verifier_modifiable(commande: Commande) -> None:
    """RG12 : une commande livrée ou annulée n'est plus modifiable."""
    if commande.statut in STATUTS_FINAUX:
        raise ErreurMetier(
            409,
            f"La commande {commande.numero} est « {commande.statut} » "
            f"et n'est plus modifiable",
        )


def _resoudre_mesure(db: Session, client_id: int, mesure_id: int | None) -> int | None:
    """RG9 : les mesures doivent appartenir au client ; sinon, dernières mesures."""
    if mesure_id is None:
        derniere = dernieres_mesures(db, client_id)
        return derniere.id if derniere else None
    mesure = db.get(Mesure, mesure_id)
    if mesure is None or mesure.client_id != client_id:
        raise ErreurMetier(
            422,
            f"Les mesures {mesure_id} n'appartiennent pas " f"au client de la commande",
        )
    return mesure.id


def _construire_ligne(db: Session, donnees: LigneCreate) -> LigneCommande:
    """RG6 : prix par défaut = prix catalogue ; prestation inactive refusée."""
    prestation = db.get(TypeVetement, donnees.type_vetement_id)
    if prestation is None:
        raise ErreurMetier(422, f"Prestation {donnees.type_vetement_id} introuvable")
    if not prestation.actif:
        raise ErreurMetier(
            422,
            f"La prestation « {prestation.nom} » n'est plus "
            f"disponible au catalogue",
        )
    prix = (
        donnees.prix_unitaire
        if donnees.prix_unitaire is not None
        else prestation.prix_base
    )
    ligne = LigneCommande(
        type_vetement_id=prestation.id,
        description=donnees.description,
        quantite=donnees.quantite,
        prix_unitaire=prix,
    )
    ligne.type_vetement = prestation  # utile pour le délai et le nom
    return ligne


# ---------- Création et lecture ----------
def creer_commande(
    db: Session, donnees: CommandeCreate, auteur: Utilisateur
) -> Commande:
    obtenir_client(db, donnees.client_id)  # 404 si le client n'existe pas
    aujourd_hui = date.today()

    lignes = [_construire_ligne(db, l) for l in donnees.lignes]

    # RG8 : par défaut, date de commande + le plus long délai des prestations
    date_prevue = donnees.date_livraison_prevue or (
        aujourd_hui + timedelta(days=max(l.type_vetement.delai_jours for l in lignes))
    )
    if date_prevue < aujourd_hui:
        raise ErreurMetier(
            422,
            "La date de livraison prévue ne peut pas précéder " "la date de commande",
        )

    commande = Commande(
        client_id=donnees.client_id,
        mesure_id=_resoudre_mesure(db, donnees.client_id, donnees.mesure_id),
        statut="en_attente",
        date_commande=aujourd_hui,
        date_livraison_prevue=date_prevue,
        remise=donnees.remise,
        notes=donnees.notes,
        cree_par_id=auteur.id,
        lignes=lignes,
    )
    recalculer_montants(commande)
    db.add(commande)
    db.flush()  # obtient l'id

    # RG5 : numéro CMD-AAAA-NNNNN construit à partir de l'id
    commande.numero = f"CMD-{aujourd_hui.year}-{commande.id:05d}"
    # RG15 : première ligne d'historique, ancien statut vide
    ajouter_historique(
        db, commande, None, "en_attente", auteur, "Création de la commande"
    )
    db.flush()
    return commande


def obtenir_commande(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise ErreurMetier(404, f"Commande {commande_id} introuvable")
    return commande


def _paginer(db: Session, requete, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return items, total


def lister_commandes(
    db: Session,
    statut=None,
    client_id=None,
    en_retard=None,
    date_min=None,
    date_max=None,
    numero=None,
    limit=20,
    offset=0,
):
    """Liste filtrée, la plus récente d'abord."""
    requete = select(Commande)
    if statut:
        requete = requete.where(Commande.statut == statut)
    if client_id:
        requete = requete.where(Commande.client_id == client_id)
    if date_min:
        requete = requete.where(Commande.date_commande >= date_min)
    if date_max:
        requete = requete.where(Commande.date_commande <= date_max)
    if numero:
        requete = requete.where(Commande.numero.ilike(f"%{numero}%"))
    if en_retard is not None:
        # Même définition que la propriété en_retard (RG11), mais en SQL
        condition = (Commande.date_livraison_prevue < date.today()) & (
            Commande.statut.not_in(STATUTS_FINAUX)
        )
        requete = requete.where(condition if en_retard else ~condition)
    return _paginer(db, requete, limit, offset)


def commandes_du_client(db: Session, client_id: int, limit: int, offset: int):
    """Route 12 : commandes d'un client, la plus récente d'abord."""
    obtenir_client(db, client_id)
    return _paginer(
        db, select(Commande).where(Commande.client_id == client_id), limit, offset
    )


# ---------- Modification ----------
def modifier_commande(
    db: Session, commande_id: int, donnees: CommandeUpdate
) -> Commande:
    commande = obtenir_commande(db, commande_id)
    verifier_modifiable(commande)
    changements = donnees.model_dump(exclude_unset=True)

    if "mesure_id" in changements:
        commande.mesure_id = _resoudre_mesure(
            db, commande.client_id, changements["mesure_id"]
        )
    if changements.get("date_livraison_prevue"):
        if changements["date_livraison_prevue"] < commande.date_commande:
            raise ErreurMetier(
                422,
                "La date de livraison prévue ne peut pas précéder "
                "la date de commande",
            )
        commande.date_livraison_prevue = changements["date_livraison_prevue"]
    if changements.get("remise") is not None:
        commande.remise = changements["remise"]
    if "notes" in changements:
        commande.notes = changements["notes"]

    recalculer_montants(commande)  # RG7
    db.flush()
    return commande


# ---------- Workflow des statuts ----------
def changer_statut(
    db: Session, commande_id: int, donnees: StatutChange, auteur: Utilisateur
) -> Commande:
    commande = obtenir_commande(db, commande_id)
    actuel, nouveau = commande.statut, donnees.statut

    # RG13 : demander le statut actuel est refusé
    if nouveau == actuel:
        raise ErreurMetier(409, f"La commande est déjà au statut « {actuel} »")
    # RG13 : "livree" uniquement via la confirmation de livraison
    if nouveau == "livree":
        raise ErreurMetier(
            409, "Le statut « livree » se pose uniquement en confirmant " "la livraison"
        )
    # RG14 : le tailleur ne peut pas annuler
    if nouveau == "annulee" and auteur.role == "tailleur":
        raise ErreurMetier(403, "Un tailleur ne peut pas annuler une commande")

    # Workflow : le message liste les statuts possibles
    possibles = TRANSITIONS[actuel] - {"livree"}
    if nouveau not in possibles:
        liste = ", ".join(sorted(possibles)) or "aucun (statut final)"
        raise ErreurMetier(
            409,
            f"Transition interdite : {actuel} → {nouveau}. "
            f"Statuts possibles : {liste}",
        )

    # RG14 : annuler une commande avec acompte exige un commentaire
    if nouveau == "annulee" and commande.montant_paye > 0 and not donnees.commentaire:
        raise ErreurMetier(
            422,
            f"Cette commande a reçu {commande.montant_paye} FCFA : "
            f"indiquez en commentaire le sort de l'argent "
            f"(remboursement, avoir...)",
        )

    commande.statut = nouveau
    ajouter_historique(db, commande, actuel, nouveau, auteur, donnees.commentaire)
    db.flush()
    return commande


def historique_commande(db: Session, commande_id: int) -> list[HistoriqueStatut]:
    obtenir_commande(db, commande_id)
    return list(
        db.scalars(
            select(HistoriqueStatut)
            .where(HistoriqueStatut.commande_id == commande_id)
            .order_by(HistoriqueStatut.date_changement, HistoriqueStatut.id)
        )
    )


# ---------- Lignes ----------
def _verifier_lignes_modifiables(commande: Commande) -> None:
    """RG10 : lignes modifiables seulement en "en_attente"."""
    verifier_modifiable(commande)
    if commande.statut != "en_attente":
        raise ErreurMetier(
            409,
            "Les lignes ne sont modifiables que lorsque la commande "
            "est « en_attente »",
        )


def ajouter_ligne(db: Session, commande_id: int, donnees: LigneCreate) -> Commande:
    commande = obtenir_commande(db, commande_id)
    _verifier_lignes_modifiables(commande)
    commande.lignes.append(_construire_ligne(db, donnees))
    recalculer_montants(commande)
    db.flush()
    return commande


def supprimer_ligne(db: Session, commande_id: int, ligne_id: int) -> Commande:
    commande = obtenir_commande(db, commande_id)
    ligne = next((l for l in commande.lignes if l.id == ligne_id), None)
    if ligne is None:
        raise ErreurMetier(404, f"Ligne {ligne_id} introuvable dans cette commande")
    _verifier_lignes_modifiables(commande)
    if len(commande.lignes) == 1:
        raise ErreurMetier(409, "Une commande doit garder au moins une ligne")
    commande.lignes.remove(ligne)  # supprimée grâce à delete-orphan
    recalculer_montants(commande)
    db.flush()
    return commande
