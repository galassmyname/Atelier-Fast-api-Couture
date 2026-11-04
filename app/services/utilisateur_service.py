"""Logique métier des utilisateurs et de l'authentification."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurUpdate
from app.security import hacher_mot_de_passe, verifier_mot_de_passe

# Même message que l'e-mail soit inconnu ou le mot de passe faux (RG23)
MESSAGE_LOGIN_ECHOUE = "E-mail ou mot de passe incorrect"


def authentifier(db: Session, email: str, mot_de_passe: str) -> Utilisateur:
    """Vérifie les identifiants. Lève une 401 identique dans tous les cas d'échec."""
    utilisateur = db.scalar(
        select(Utilisateur).where(Utilisateur.email == email.lower())
    )
    if (
        utilisateur is None
        or not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash)
        or not utilisateur.actif  # compte désactivé : refusé aussi
    ):
        raise ErreurMetier(401, MESSAGE_LOGIN_ECHOUE)
    return utilisateur


def creer_utilisateur(db: Session, donnees: UtilisateurCreate) -> Utilisateur:
    email = donnees.email.lower()
    if db.scalar(select(Utilisateur).where(Utilisateur.email == email)):
        raise ErreurMetier(409, f"Un compte existe déjà avec l'e-mail {email}")
    utilisateur = Utilisateur(
        email=email,
        nom_complet=donnees.nom_complet,
        mot_de_passe_hash=hacher_mot_de_passe(donnees.mot_de_passe),
        role=donnees.role,
        actif=True,
    )
    db.add(utilisateur)
    db.flush()  # obtient l'id sans valider la transaction (c'est le routeur qui commit)
    return utilisateur


def lister_utilisateurs(db: Session) -> list[Utilisateur]:
    return list(db.scalars(select(Utilisateur).order_by(Utilisateur.nom_complet)))


def obtenir_utilisateur(db: Session, utilisateur_id: int) -> Utilisateur:
    utilisateur = db.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise ErreurMetier(404, f"Utilisateur {utilisateur_id} introuvable")
    return utilisateur


def modifier_utilisateur(
    db: Session, utilisateur_id: int, donnees: UtilisateurUpdate, auteur: Utilisateur
) -> Utilisateur:
    utilisateur = obtenir_utilisateur(db, utilisateur_id)
    changements = donnees.model_dump(exclude_unset=True)  # seulement les champs envoyés

    # RG24 : un admin ne peut ni se désactiver ni perdre son propre rôle admin
    if utilisateur.id == auteur.id:
        if changements.get("actif") is False:
            raise ErreurMetier(409, "Vous ne pouvez pas désactiver votre propre compte")
        if "role" in changements and changements["role"] != "admin":
            raise ErreurMetier(
                409, "Vous ne pouvez pas retirer votre propre rôle d'administrateur"
            )

    # Le mot de passe est haché avant d'être enregistré
    if "mot_de_passe" in changements:
        utilisateur.mot_de_passe_hash = hacher_mot_de_passe(
            changements.pop("mot_de_passe")
        )

    for champ, valeur in changements.items():
        setattr(utilisateur, champ, valeur)
    db.flush()
    return utilisateur
