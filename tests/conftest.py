"""Configuration commune des tests : base SQLite en mémoire, comptes et outils."""

import os

# On force une base de test AVANT d'importer l'application
# (les variables d'environnement passent avant le fichier .env)
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("SECRET_KEY", "cle-secrete-de-test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import TypeVetement, Utilisateur
from app.security import hacher_mot_de_passe

API = "/api/v1"
MOT_DE_PASSE = "motdepasse123"

# StaticPool : une seule connexion partagée, nécessaire pour SQLite en mémoire
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionTest = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def db():
    """Base vide et neuve pour chaque test (create_all autorisé ici, pas en prod)."""
    Base.metadata.create_all(engine)
    session = SessionTest()
    # Comptes de test : un par rôle
    for email, role in [
        ("admin@test.sn", "admin"),
        ("accueil@test.sn", "accueil"),
        ("tailleur@test.sn", "tailleur"),
    ]:
        session.add(
            Utilisateur(
                email=email,
                nom_complet=role.capitalize(),
                role=role,
                mot_de_passe_hash=hacher_mot_de_passe(MOT_DE_PASSE),
                actif=True,
            )
        )
    # Petit catalogue
    session.add_all(
        [
            TypeVetement(nom="Boubou", prix_base=35000, delai_jours=10, actif=True),
            TypeVetement(nom="Pantalon", prix_base=12000, delai_jours=4, actif=True),
            TypeVetement(
                nom="Ancien modèle", prix_base=5000, delai_jours=2, actif=False
            ),
        ]
    )
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db):
    """Client HTTP de test, branché sur la base de test."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _jeton(client, email):
    r = client.post(
        f"{API}/auth/login", data={"username": email, "password": MOT_DE_PASSE}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return _jeton(client, "admin@test.sn")


@pytest.fixture
def accueil(client):
    return _jeton(client, "accueil@test.sn")


@pytest.fixture
def tailleur(client):
    return _jeton(client, "tailleur@test.sn")


@pytest.fixture
def fatou(client, accueil):
    """Une cliente prête à l'emploi."""
    r = client.post(
        f"{API}/clients",
        headers=accueil,
        json={"nom": "Diop", "prenom": "Fatou", "telephone": "77 123 45 67"},
    )
    return r.json()


@pytest.fixture
def commande(client, accueil, fatou):
    """Commande : 2 boubous (prix catalogue) + 1 pantalon négocié, remise 5 000.
    Total = 2×35000 + 10000 − 5000 = 75 000 FCFA."""
    r = client.post(
        f"{API}/commandes",
        headers=accueil,
        json={
            "client_id": fatou["id"],
            "lignes": [
                {"type_vetement_id": 1, "quantite": 2},
                {"type_vetement_id": 2, "quantite": 1, "prix_unitaire": 10000},
            ],
            "remise": 5000,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def avancer_jusqua_terminee(client, headers, commande_id):
    """Fait passer une commande de en_attente à terminee."""
    for statut in ["en_coupe", "en_couture", "terminee"]:
        r = client.post(
            f"{API}/commandes/{commande_id}/statut",
            headers=headers,
            json={"statut": statut},
        )
        assert r.status_code == 200, r.text
