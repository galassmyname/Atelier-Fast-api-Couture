"""Dépendances FastAPI : utilisateur connecté et contrôle des rôles."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Utilisateur
from app.security import decoder_jeton

# Indique à Swagger où se connecter (bouton "Authorize")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Erreur 401 réutilisée partout
ERREUR_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentification requise : jeton absent, invalide ou expiré",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    jeton: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Utilisateur:
    """Récupère l'utilisateur à partir du jeton.
    Un compte désactivé est refusé immédiatement, même avec un jeton valide (RG22)."""
    utilisateur_id = decoder_jeton(jeton)
    if utilisateur_id is None:
        raise ERREUR_401
    utilisateur = db.get(Utilisateur, utilisateur_id)
    if utilisateur is None or not utilisateur.actif:
        raise ERREUR_401
    return utilisateur


def require_roles(*roles: str):
    """Fabrique une dépendance qui n'accepte que certains rôles.
    L'admin est toujours autorisé (il peut tout faire). Sinon : 403."""

    def verifier(utilisateur: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if utilisateur.role != "admin" and utilisateur.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé : votre rôle ne permet pas cette action",
            )
        return utilisateur

    return verifier


# Raccourcis pratiques pour les routeurs
require_admin = require_roles("admin")
require_accueil = require_roles("accueil")
require_tailleur = require_roles("tailleur")
