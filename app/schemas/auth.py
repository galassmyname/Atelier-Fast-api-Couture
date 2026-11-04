"""Schéma de la réponse de connexion."""

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # durée de validité en secondes
