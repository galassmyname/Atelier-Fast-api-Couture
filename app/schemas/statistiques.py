"""Schémas Pydantic des utilisateurs : création, modification, lecture."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Seuls rôles autorisés : toute autre valeur donne une 422 automatique
Role = Literal["admin", "tailleur", "accueil"]


class UtilisateurCreate(BaseModel):
    email: EmailStr
    nom_complet: str = Field(min_length=1, max_length=150)
    mot_de_passe: str = Field(min_length=8)  # RG21 : 8 caractères minimum
    role: Role


class UtilisateurUpdate(BaseModel):
    """PATCH : tous les champs facultatifs, seuls ceux envoyés sont modifiés."""

    nom_complet: Optional[str] = Field(default=None, min_length=1, max_length=150)
    role: Optional[Role] = None
    actif: Optional[bool] = None
    mot_de_passe: Optional[str] = Field(default=None, min_length=8)


class UtilisateurRead(BaseModel):
    """Lecture : jamais de mot_de_passe_hash (RG21)."""

    model_config = ConfigDict(
        from_attributes=True
    )  # lecture depuis un modèle SQLAlchemy

    id: int
    email: EmailStr
    nom_complet: str
    role: Role
    actif: bool
    created_at: datetime
