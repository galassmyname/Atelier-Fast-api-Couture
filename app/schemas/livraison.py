"""Schémas Pydantic des livraisons."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

ModeLivraison = Literal["retrait_atelier", "domicile"]
StatutLivraison = Literal["planifiee", "livree"]


class LivraisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    mode: ModeLivraison
    adresse: Optional[str]
    livreur: Optional[str]
    date_prevue: date
    date_effective: Optional[date]
    statut: StatutLivraison
    notes: Optional[str]
