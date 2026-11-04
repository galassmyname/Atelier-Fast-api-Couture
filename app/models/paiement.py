"""Schémas Pydantic des paiements."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

ModePaiement = Literal["especes", "wave", "orange_money", "virement", "cheque"]


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
