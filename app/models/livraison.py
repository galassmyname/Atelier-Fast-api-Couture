"""Modèle Livraison : une seule par commande."""

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Livraison(Base):
    __tablename__ = "livraisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True garantit "une seule livraison par commande"
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), unique=True
    )
    mode: Mapped[str] = mapped_column(String(20))  # retrait_atelier | domicile
    adresse: Mapped[Optional[str]] = mapped_column(String(255))
    livreur: Mapped[Optional[str]] = mapped_column(String(100))
    date_prevue: Mapped[date] = mapped_column(Date)
    date_effective: Mapped[Optional[date]] = mapped_column(Date)
    statut: Mapped[str] = mapped_column(
        String(20), default="planifiee"
    )  # planifiee | livree
    notes: Mapped[Optional[str]] = mapped_column(Text)

    commande: Mapped["Commande"] = relationship(back_populates="livraison")

    # Propriétés utilisées par la liste de tournée (route 38)
    @property
    def numero_commande(self) -> str:
        return self.commande.numero

    @property
    def client_nom(self) -> str:
        return self.commande.client_nom

    @property
    def client_telephone(self) -> str:
        return self.commande.client.telephone

    @property
    def solde_commande(self) -> int:
        return self.commande.solde
