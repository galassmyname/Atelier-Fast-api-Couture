"""Routes d'authentification (routes 1 et 2)."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Utilisateur
from app.schemas.auth import Token
from app.schemas.utilisateur import UtilisateurRead
from app.security import creer_jeton
from app.services import utilisateur_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Connexion par formulaire OAuth2 : username = e-mail, password = mot de passe."""
    utilisateur = utilisateur_service.authentifier(db, form.username, form.password)
    jeton, expires_in = creer_jeton(utilisateur.id)
    return Token(access_token=jeton, expires_in=expires_in)


@router.get("/me", response_model=UtilisateurRead)
def me(utilisateur: Utilisateur = Depends(get_current_user)):
    """Profil de l'utilisateur connecté (le schéma exclut le hash)."""
    return utilisateur
