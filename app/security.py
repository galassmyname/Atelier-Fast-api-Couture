"""Outils de sécurité : hachage des mots de passe (Argon2) et jetons JWT."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Argon2 : algorithme recommandé par l'énoncé (RG21)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Renvoie le hash du mot de passe (on ne stocke jamais le clair)."""
    return pwd_context.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """Compare un mot de passe saisi avec le hash enregistré."""
    return pwd_context.verify(mot_de_passe, hash_stocke)


def creer_jeton(utilisateur_id: int) -> tuple[str, int]:
    """Crée un JWT signé avec une date d'expiration (RG22).
    Renvoie le jeton et sa durée de validité en secondes (expires_in)."""
    duree = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expiration = datetime.now(timezone.utc) + duree
    contenu = {"sub": str(utilisateur_id), "exp": expiration}
    jeton = jwt.encode(contenu, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return jeton, int(duree.total_seconds())


def decoder_jeton(jeton: str) -> int | None:
    """Renvoie l'id de l'utilisateur contenu dans le jeton,
    ou None si le jeton est invalide ou expiré."""
    try:
        contenu = jwt.decode(
            jeton, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return int(contenu["sub"])
    except (JWTError, KeyError, ValueError):
        return None
