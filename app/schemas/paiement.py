"""Schémas Pydantic des paiements."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ModePaiement = Literal["especes", "wave", "orange_money", "virement", "cheque"]


class PaiementCreate(BaseModel):
    montant: int = Field(gt=0)  # RG16 : strictement positif
    mode: ModePaiement
    reference: Optional[str] = None  # ex. identifiant de transaction Wave
    date_paiement: Optional[date] = None  # aujourd'hui par défaut


class PaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    montant: int
    mode: ModePaiement
    reference: Optional[str]
    date_paiement: date
    enregistre_par_id: Optional[int]
    created_at: datetime
