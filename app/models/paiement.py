"""Modèle Paiement : acomptes et soldes."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Paiement(Base):
    __tablename__ = "paiements"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    montant: Mapped[int] = mapped_column(Integer)  # FCFA, > 0 (RG16)
    mode: Mapped[str] = mapped_column(
        String(20)
    )  # especes | wave | orange_money | virement | cheque
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    date_paiement: Mapped[date] = mapped_column(Date)
    enregistre_par_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("utilisateurs.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    commande: Mapped["Commande"] = relationship(back_populates="paiements")
