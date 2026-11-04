"""Schémas Pydantic des livraisons."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

ModeLivraison = Literal["retrait_atelier", "domicile"]
StatutLivraison = Literal["planifiee", "livree"]


class LivraisonPlanifier(BaseModel):
    """Corps du PUT : planifier ou replanifier (RG18)."""

    mode: ModeLivraison
    date_prevue: date
    adresse: Optional[str] = None
    livreur: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def adresse_si_domicile(self):
        """RG18 : une livraison à domicile exige une adresse (422)."""
        if self.mode == "domicile" and not (self.adresse and self.adresse.strip()):
            raise ValueError("Une livraison à domicile exige une adresse")
        return self


class LivraisonConfirmer(BaseModel):
    """Corps facultatif de la confirmation (RG19-20)."""

    date_effective: Optional[date] = None
    autoriser_solde_impaye: bool = False


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


class LivraisonTournee(LivraisonRead):
    """Élément de la liste de tournée (route 38)."""

    numero_commande: str
    client_nom: str
    client_telephone: str
    solde_commande: int
