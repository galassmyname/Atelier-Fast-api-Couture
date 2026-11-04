"""Calcul des statistiques (administrateur uniquement)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import (
    Client,
    Commande,
    LigneCommande,
    Livraison,
    Paiement,
    TypeVetement,
)
from app.services.commande_service import STATUTS_FINAUX, TRANSITIONS

NON_ANNULEE = Commande.statut != "annulee"


def periode_par_defaut(
    date_debut: date | None, date_fin: date | None
) -> tuple[date, date]:
    """Par défaut : du 1er du mois à aujourd'hui. 422 si début > fin."""
    aujourd_hui = date.today()
    debut = date_debut or aujourd_hui.replace(day=1)
    fin = date_fin or aujourd_hui
    if debut > fin:
        raise ErreurMetier(422, "date_debut doit être antérieure ou égale à date_fin")
    return debut, fin


def tableau_de_bord(db: Session) -> dict:
    aujourd_hui = date.today()
    debut_mois = aujourd_hui.replace(day=1)

    # Chiffre d'affaires et nombre de commandes du mois (datés à la commande)
    ca_mois, nb_mois = db.execute(
        select(
            func.coalesce(func.sum(Commande.montant_total), 0), func.count(Commande.id)
        ).where(
            NON_ANNULEE,
            Commande.date_commande >= debut_mois,
            Commande.date_commande <= aujourd_hui,
        )
    ).one()

    # Encaissé du mois (daté au paiement)
    encaisse_mois = db.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0)).where(
            Paiement.date_paiement >= debut_mois, Paiement.date_paiement <= aujourd_hui
        )
    )

    # Reste à encaisser : somme des soldes des commandes non annulées
    reste = db.scalar(
        select(
            func.coalesce(func.sum(Commande.montant_total - Commande.montant_paye), 0)
        ).where(NON_ANNULEE)
    )

    # Nombre de commandes par statut : tous les statuts, même à 0
    par_statut = {statut: 0 for statut in TRANSITIONS}
    for statut, nb in db.execute(
        select(Commande.statut, func.count(Commande.id)).group_by(Commande.statut)
    ):
        par_statut[statut] = nb

    en_retard = db.scalar(
        select(func.count(Commande.id)).where(
            Commande.date_livraison_prevue < aujourd_hui,
            Commande.statut.not_in(STATUTS_FINAUX),
        )
    )
    livraisons_jour = db.scalar(
        select(func.count(Livraison.id)).where(
            Livraison.date_prevue == aujourd_hui, Livraison.statut == "planifiee"
        )
    )

    return {
        "chiffre_affaires_mois": ca_mois,
        "encaisse_mois": encaisse_mois,
        "nb_commandes_mois": nb_mois,
        "reste_a_encaisser": reste,
        "commandes_par_statut": par_statut,
        "nb_commandes_en_retard": en_retard,
        "commandes_pretes_a_livrer": par_statut["terminee"],
        "livraisons_du_jour": livraisons_jour,
    }


def chiffre_affaires(db: Session, granularite: str, date_debut, date_fin) -> list[dict]:
    """CA et encaissements par jour ou par mois ; seules les périodes actives."""
    debut, fin = periode_par_defaut(date_debut, date_fin)
    # Format de la clé de période
    fmt = "%Y-%m-%d" if granularite == "jour" else "%Y-%m"
    resultats: dict[str, dict] = {}

    def ligne(cle: str) -> dict:
        return resultats.setdefault(
            cle, {"periode": cle, "chiffre_affaires": 0, "encaisse": 0}
        )

    # CA : regroupé en Python par jour, puis cumulé selon la granularité
    for jour, montant in db.execute(
        select(Commande.date_commande, func.sum(Commande.montant_total))
        .where(NON_ANNULEE, Commande.date_commande.between(debut, fin))
        .group_by(Commande.date_commande)
    ):
        ligne(jour.strftime(fmt))["chiffre_affaires"] += montant

    # Encaissements
    for jour, montant in db.execute(
        select(Paiement.date_paiement, func.sum(Paiement.montant))
        .where(Paiement.date_paiement.between(debut, fin))
        .group_by(Paiement.date_paiement)
    ):
        ligne(jour.strftime(fmt))["encaisse"] += montant

    return sorted(resultats.values(), key=lambda r: r["periode"])


def par_type_vetement(db: Session, date_debut, date_fin) -> list[dict]:
    """Quantité vendue et CA avant remise, par prestation."""
    debut, fin = periode_par_defaut(date_debut, date_fin)
    ca = func.sum(LigneCommande.quantite * LigneCommande.prix_unitaire)
    lignes = db.execute(
        select(TypeVetement.id, TypeVetement.nom, func.sum(LigneCommande.quantite), ca)
        .join(LigneCommande, LigneCommande.type_vetement_id == TypeVetement.id)
        .join(Commande, Commande.id == LigneCommande.commande_id)
        .where(NON_ANNULEE, Commande.date_commande.between(debut, fin))
        .group_by(TypeVetement.id, TypeVetement.nom)
        .order_by(ca.desc())
    )
    return [
        {"type_vetement_id": i, "nom": n, "quantite_vendue": q, "chiffre_affaires": c}
        for i, n, q, c in lignes
    ]


def top_clients(db: Session, date_debut, date_fin, limite: int) -> list[dict]:
    debut, fin = periode_par_defaut(date_debut, date_fin)
    ca = func.sum(Commande.montant_total)
    lignes = db.execute(
        select(
            Client.id,
            Client.prenom,
            Client.nom,
            func.count(Commande.id),
            ca,
            func.sum(Commande.montant_total - Commande.montant_paye),
        )
        .join(Commande, Commande.client_id == Client.id)
        .where(NON_ANNULEE, Commande.date_commande.between(debut, fin))
        .group_by(Client.id, Client.prenom, Client.nom)
        .order_by(ca.desc())
        .limit(limite)
    )
    return [
        {
            "client_id": i,
            "client_nom": f"{p} {n}",
            "nb_commandes": nb,
            "chiffre_affaires": c,
            "solde_du": s,
        }
        for i, p, n, nb, c, s in lignes
    ]


def impayes(db: Session, limit: int, offset: int):
    """Commandes non annulées non soldées, les plus urgentes d'abord."""
    requete = select(Commande).where(
        NON_ANNULEE, Commande.montant_total > Commande.montant_paye
    )
    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.order_by(Commande.date_livraison_prevue, Commande.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return items, total
