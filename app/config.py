"""Lecture de la configuration depuis les variables d'environnement (.env).

Aucun mot de passe ni clé secrète n'est écrit dans le code :
tout vient du fichier .env (exclu de Git).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Indique à pydantic-settings de lire le fichier .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de données
    DATABASE_URL: str

    # Sécurité JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Premier administrateur (script de seed)
    ADMIN_EMAIL: str = "admin@atelier.sn"
    ADMIN_PASSWORD: str = "changez-moi"
    ADMIN_NOM: str = "Administrateur"


# Instance unique, importée partout dans l'application
settings = Settings()
