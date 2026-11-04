"""Schémas Pydantic des clients."""

import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Genre = Literal["homme", "femme", "enfant"]

# Forme valide après nettoyage : "+" facultatif puis 6 à 20 chiffres (RG1)
TELEPHONE_REGEX = re.compile(r"^\+?\d{6,20}$")


def normaliser_telephone(valeur: str) -> str:
    """Supprime espaces, points, tirets et parenthèses, puis vérifie le format.
    "77 123 45 67" et "771234567" donnent le même résultat."""
    nettoye = re.sub(r"[\s.\-()]", "", valeur)
    if not TELEPHONE_REGEX.match(nettoye):
        raise ValueError(
            "Téléphone invalide : 6 à 20 chiffres, avec un « + » initial facultatif"
        )
    return nettoye


class ClientCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    telephone: str
    email: Optional[EmailStr] = None
    adresse: Optional[str] = None
    genre: Optional[Genre] = None
    notes: Optional[str] = None

    @field_validator("telephone")
    @classmethod
    def valider_telephone(cls, v: str) -> str:
        return normaliser_telephone(v)


class ClientUpdate(BaseModel):
    """PATCH : nom, prenom et telephone ne peuvent pas être vidés (422)."""

    nom: Optional[str] = Field(default=None, max_length=100)
    prenom: Optional[str] = Field(default=None, max_length=100)
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    adresse: Optional[str] = None
    genre: Optional[Genre] = None
    notes: Optional[str] = None

    @field_validator("nom", "prenom", "telephone")
    @classmethod
    def interdire_vide(cls, v: Optional[str], info) -> str:
        # Ce validateur s'exécute seulement si le champ est envoyé (même à null)
        if v is None or not v.strip():
            raise ValueError(f"Le champ {info.field_name} ne peut pas être vide")
        if info.field_name == "telephone":
            return normaliser_telephone(v)
        return v.strip()


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    telephone: str
    email: Optional[str]
    adresse: Optional[str]
    genre: Optional[Genre]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class ClientResume(BaseModel):
    """Route 13 : synthèse d'un client (commandes annulées exclues)."""

    nb_commandes: int
    chiffre_affaires: int
    total_paye: int
    solde_du: int
    derniere_commande: Optional[date]
    a_des_mesures: bool
