"""Script d'initialisation : python -m app.seed

Crée le premier administrateur (depuis le .env) et le catalogue de l'annexe B.
Peut être relancé sans créer de doublons."""

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import TypeVetement, Utilisateur
from app.security import hacher_mot_de_passe

# Catalogue de départ (annexe B) : nom, description, prix FCFA, délai en jours
CATALOGUE = [
    ("Boubou", "Boubou homme en bazin ou brodé", 35000, 10),
    ("Costume 2 pièces", "Veste et pantalon", 85000, 14),
    ("Robe", "Robe sur mesure", 30000, 7),
    ("Ensemble wax", "Tenue deux pièces en wax", 25000, 7),
    ("Chemise", "Chemise sur mesure", 15000, 5),
    ("Pantalon", "Pantalon sur mesure", 12000, 4),
    ("Retouche", "Ourlet, rétrécissement, remplacement de fermeture", 3000, 2),
]


def creer_admin(db) -> None:
    """Crée l'administrateur s'il n'existe pas encore."""
    existe = db.scalar(
        select(Utilisateur).where(Utilisateur.email == settings.ADMIN_EMAIL)
    )
    if existe:
        print(f"Admin déjà présent : {settings.ADMIN_EMAIL}")
        return
    db.add(
        Utilisateur(
            email=settings.ADMIN_EMAIL,
            nom_complet=settings.ADMIN_NOM,
            mot_de_passe_hash=hacher_mot_de_passe(settings.ADMIN_PASSWORD),
            role="admin",
            actif=True,
        )
    )
    print(f"Admin créé : {settings.ADMIN_EMAIL}")


def creer_catalogue(db) -> None:
    """Ajoute les prestations manquantes du catalogue."""
    for nom, description, prix, delai in CATALOGUE:
        if db.scalar(select(TypeVetement).where(TypeVetement.nom == nom)):
            continue  # déjà présente : on ne la recrée pas
        db.add(
            TypeVetement(
                nom=nom,
                description=description,
                prix_base=prix,
                delai_jours=delai,
                actif=True,
            )
        )
        print(f"Prestation ajoutée : {nom}")


def main() -> None:
    db = SessionLocal()
    try:
        creer_admin(db)
        creer_catalogue(db)
        db.commit()  # on valide tout en une seule fois
        print("Initialisation terminée ✅")
    finally:
        db.close()


if __name__ == "__main__":
    main()
