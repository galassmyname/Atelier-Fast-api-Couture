"""Schémas Pydantic des prises de mesures."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.mesure import CHAMPS_MESURES

# RG2 : chaque mesure est strictement positive et ne dépasse pas 300 cm
Cm = Optional[float]
CONTRAINTE = dict(default=None, gt=0, le=300)


class MesuresValeurs(BaseModel):
    """Les 18 mesures facultatives, en centimètres."""

    taille_cm: Cm = Field(**CONTRAINTE)
    tour_cou: Cm = Field(**CONTRAINTE)
    carrure_dos: Cm = Field(**CONTRAINTE)
    longueur_epaule: Cm = Field(**CONTRAINTE)
    tour_poitrine: Cm = Field(**CONTRAINTE)
    tour_taille: Cm = Field(**CONTRAINTE)
    tour_bassin: Cm = Field(**CONTRAINTE)
    longueur_manche: Cm = Field(**CONTRAINTE)
    tour_bras: Cm = Field(**CONTRAINTE)
    tour_poignet: Cm = Field(**CONTRAINTE)
    longueur_dos: Cm = Field(**CONTRAINTE)
    longueur_haut: Cm = Field(**CONTRAINTE)
    longueur_pantalon: Cm = Field(**CONTRAINTE)
    tour_cuisse: Cm = Field(**CONTRAINTE)
    tour_genou: Cm = Field(**CONTRAINTE)
    bas_pantalon: Cm = Field(**CONTRAINTE)
    entrejambe: Cm = Field(**CONTRAINTE)
    longueur_robe: Cm = Field(**CONTRAINTE)


class MesureCreate(MesuresValeurs):
    date_prise: Optional[date] = None  # aujourd'hui par défaut (géré dans le service)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def au_moins_une_mesure(self):
        """RG2 : une prise doit contenir au moins une mesure."""
        if all(getattr(self, champ) is None for champ in CHAMPS_MESURES):
            raise ValueError("Une prise de mesures doit contenir au moins une mesure")
        return self


class MesureUpdate(MesuresValeurs):
    """PATCH : la règle « au moins une mesure » est vérifiée dans le service,
    car il faut combiner les valeurs envoyées avec celles déjà enregistrées."""

    date_prise: Optional[date] = None
    notes: Optional[str] = None


class MesureRead(MesuresValeurs):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    date_prise: date
    prise_par_id: Optional[int]
    notes: Optional[str]
