"""Logique métier du catalogue."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ErreurMetier
from app.models import TypeVetement
from app.schemas.catalogue import TypeVetementCreate, TypeVetementUpdate


def _verifier_nom_libre(db: Session, nom: str, exclure_id: int | None = None):
    requete = select(TypeVetement).where(TypeVetement.nom == nom)
    if exclure_id is not None:
        requete = requete.where(TypeVetement.id != exclure_id)
    if db.scalar(requete):
        raise ErreurMetier(409, f"Une prestation nommée « {nom} » existe déjà")


def creer_prestation(db: Session, donnees: TypeVetementCreate) -> TypeVetement:
    _verifier_nom_libre(db, donnees.nom)
    prestation = TypeVetement(**donnees.model_dump(), actif=True)
    db.add(prestation)
    db.flush()
    return prestation


def lister_prestations(
    db: Session, actifs_seulement: bool = True
) -> list[TypeVetement]:
    requete = select(TypeVetement).order_by(TypeVetement.nom)
    if actifs_seulement:
        requete = requete.where(TypeVetement.actif.is_(True))
    return list(db.scalars(requete))


def obtenir_prestation(db: Session, prestation_id: int) -> TypeVetement:
    prestation = db.get(TypeVetement, prestation_id)
    if prestation is None:
        raise ErreurMetier(404, f"Prestation {prestation_id} introuvable")
    return prestation


def modifier_prestation(
    db: Session, prestation_id: int, donnees: TypeVetementUpdate
) -> TypeVetement:
    """Désactiver une prestation ne touche pas aux anciennes commandes :
    leurs lignes gardent leur propre prix_unitaire."""
    prestation = obtenir_prestation(db, prestation_id)
    changements = donnees.model_dump(exclude_unset=True)
    if "nom" in changements:
        _verifier_nom_libre(db, changements["nom"], exclure_id=prestation.id)
    for champ, valeur in changements.items():
        setattr(prestation, champ, valeur)
    db.flush()
    return prestation
