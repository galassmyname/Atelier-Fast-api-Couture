"""Schémas Pydantic du catalogue des prestations."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TypeVetementCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    prix_base: int = Field(ge=0)  # FCFA
    delai_jours: int = Field(ge=0)


class TypeVetementUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    prix_base: Optional[int] = Field(default=None, ge=0)
    delai_jours: Optional[int] = Field(default=None, ge=0)
    actif: Optional[bool] = None  # False = retirer du catalogue


class TypeVetementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str]
    prix_base: int
    delai_jours: int
    actif: bool
