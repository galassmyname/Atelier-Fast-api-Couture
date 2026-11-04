"""Schémas Pydantic des commandes, lignes et historique."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.livraison import LivraisonRead
from app.schemas.paiement import PaiementRead

Statut = Literal[
    "en_attente",
    "en_coupe",
    "en_couture",
    "essayage",
    "retouches",
    "terminee",
    "livree",
    "annulee",
]


# ---------- Lignes ----------
class LigneCreate(BaseModel):
    type_vetement_id: int
    description: Optional[str] = None
    quantite: int = Field(default=1, ge=1)
    # Facultatif : par défaut le prix de base du catalogue (RG6)
    prix_unitaire: Optional[int] = Field(default=None, ge=0)


class LigneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type_vetement_id: int
    type_vetement_nom: str  # propriété du modèle
    description: Optional[str]
    quantite: int
    prix_unitaire: int
    sous_total: int  # propriété du modèle


# ---------- Commandes ----------
class CommandeCreate(BaseModel):
    client_id: int
    mesure_id: Optional[int] = None
    lignes: list[LigneCreate] = Field(min_length=1)  # au moins une ligne
    remise: int = Field(default=0, ge=0)
    date_livraison_prevue: Optional[date] = None
    notes: Optional[str] = None


class CommandeUpdate(BaseModel):
    mesure_id: Optional[int] = None
    date_livraison_prevue: Optional[date] = None
    remise: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None


class StatutChange(BaseModel):
    statut: Statut
    commentaire: Optional[str] = None


class CommandeListItem(BaseModel):
    """Élément de liste (route 25) : avec client_nom, solde et en_retard."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    client_nom: str
    statut: Statut
    date_commande: date
    date_livraison_prevue: date
    montant_total: int
    montant_paye: int
    solde: int
    en_retard: bool


class CommandeRead(CommandeListItem):
    """Détail complet (route 26)."""

    mesure_id: Optional[int]
    date_livraison_reelle: Optional[date]
    remise: int
    notes: Optional[str]
    cree_par_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    lignes: list[LigneRead]
    paiements: list[PaiementRead]
    livraison: Optional[LivraisonRead]


class HistoriqueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    ancien_statut: Optional[Statut]
    nouveau_statut: Statut
    commentaire: Optional[str]
    utilisateur_id: Optional[int]
    date_changement: datetime
