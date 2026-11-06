"""Vérifie que tous les fichiers du projet existent et ne sont pas vides."""

from pathlib import Path

attendus = [
    "app/main.py",
    "app/config.py",
    "app/database.py",
    "app/security.py",
    "app/deps.py",
    "app/seed.py",
    "app/exceptions.py",
    "app/models/__init__.py",
    "app/models/utilisateur.py",
    "app/models/client.py",
    "app/models/mesure.py",
    "app/models/type_vetement.py",
    "app/models/commande.py",
    "app/models/paiement.py",
    "app/models/livraison.py",
    "app/schemas/common.py",
    "app/schemas/auth.py",
    "app/schemas/utilisateur.py",
    "app/schemas/client.py",
    "app/schemas/mesure.py",
    "app/schemas/catalogue.py",
    "app/schemas/commande.py",
    "app/schemas/paiement.py",
    "app/schemas/livraison.py",
    "app/schemas/statistiques.py",
    "app/services/utilisateur_service.py",
    "app/services/client_service.py",
    "app/services/mesure_service.py",
    "app/services/catalogue_service.py",
    "app/services/commande_service.py",
    "app/services/paiement_service.py",
    "app/services/livraison_service.py",
    "app/services/statistiques_service.py",
    "app/routers/auth.py",
    "app/routers/utilisateurs.py",
    "app/routers/clients.py",
    "app/routers/catalogue.py",
    "app/routers/mesures.py",
    "app/routers/commandes.py",
    "app/routers/paiements.py",
    "app/routers/livraisons.py",
    "app/routers/statistiques.py",
    "tests/conftest.py",
    "tests/test_auth_et_roles.py",
    "tests/test_clients_mesures.py",
    "tests/test_commandes.py",
    "tests/test_paiements_livraisons.py",
    "pytest.ini",
    "Dockerfile",
    "docker-compose.yml",
    "entrypoint.sh",
    ".env.example",
]

problemes = []
for f in attendus:
    p = Path(f)
    if not p.exists():
        problemes.append(f"MANQUANT : {f}")
    elif p.stat().st_size == 0:
        problemes.append(f"VIDE     : {f}")

print("\n".join(problemes) if problemes else "Tous les fichiers sont présents ✅")
