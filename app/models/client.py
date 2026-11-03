"""Modèle Client."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), index=True)
    prenom: Mapped[str] = mapped_column(String(100))
    # Téléphone normalisé et unique (RG1)
    telephone: Mapped[str] = mapped_column(String(21), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    adresse: Mapped[Optional[str]] = mapped_column(String(255))
    genre: Mapped[Optional[str]] = mapped_column(String(10))  # homme | femme | enfant
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 1 client -> N mesures. Supprimer le client supprime ses mesures (route 11)
    mesures: Mapped[list["Mesure"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    # 1 client -> N commandes (pas de cascade : RG4 interdit la suppression)
    commandes: Mapped[list["Commande"]] = relationship(back_populates="client")
