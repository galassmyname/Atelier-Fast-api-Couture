"""Regroupe tous les modèles : nécessaire pour Alembic et les relations."""

from app.models.utilisateur import Utilisateur
from app.models.client import Client
from app.models.mesure import Mesure, CHAMPS_MESURES
from app.models.type_vetement import TypeVetement
from app.models.commande import Commande, LigneCommande, HistoriqueStatut
from app.models.paiement import Paiement
from app.models.livraison import Livraison

__all__ = [
    "Utilisateur",
    "Client",
    "Mesure",
    "CHAMPS_MESURES",
    "TypeVetement",
    "Commande",
    "LigneCommande",
    "HistoriqueStatut",
    "Paiement",
    "Livraison",
]
