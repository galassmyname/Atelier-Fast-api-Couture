"""Modèle Utilisateur : le personnel de l'atelier (admin, accueil, tailleur)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nom_complet: Mapped[str] = mapped_column(String(150))
    # Uniquement le hash Argon2, jamais le mot de passe en clair (RG21)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # admin | tailleur | accueil
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    # server_default : c'est PostgreSQL qui remplit la date
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
