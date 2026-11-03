"""Modèle Mesure : une prise de mesures (historique conservé, RG3)."""

from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Liste des 18 mesures : réutilisée dans les schémas et les services
CHAMPS_MESURES = [
    "taille_cm",
    "tour_cou",
    "carrure_dos",
    "longueur_epaule",
    "tour_poitrine",
    "tour_taille",
    "tour_bassin",
    "longueur_manche",
    "tour_bras",
    "tour_poignet",
    "longueur_dos",
    "longueur_haut",
    "longueur_pantalon",
    "tour_cuisse",
    "tour_genou",
    "bas_pantalon",
    "entrejambe",
    "longueur_robe",
]


class Mesure(Base):
    __tablename__ = "mesures"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    date_prise: Mapped[date] = mapped_column(Date)
    prise_par_id: Mapped[Optional[int]] = mapped_column(ForeignKey("utilisateurs.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Les 18 mesures en cm, toutes facultatives (RG2)
    taille_cm: Mapped[Optional[float]] = mapped_column(Float)
    tour_cou: Mapped[Optional[float]] = mapped_column(Float)
    carrure_dos: Mapped[Optional[float]] = mapped_column(Float)
    longueur_epaule: Mapped[Optional[float]] = mapped_column(Float)
    tour_poitrine: Mapped[Optional[float]] = mapped_column(Float)
    tour_taille: Mapped[Optional[float]] = mapped_column(Float)
    tour_bassin: Mapped[Optional[float]] = mapped_column(Float)
    longueur_manche: Mapped[Optional[float]] = mapped_column(Float)
    tour_bras: Mapped[Optional[float]] = mapped_column(Float)
    tour_poignet: Mapped[Optional[float]] = mapped_column(Float)
    longueur_dos: Mapped[Optional[float]] = mapped_column(Float)
    longueur_haut: Mapped[Optional[float]] = mapped_column(Float)
    longueur_pantalon: Mapped[Optional[float]] = mapped_column(Float)
    tour_cuisse: Mapped[Optional[float]] = mapped_column(Float)
    tour_genou: Mapped[Optional[float]] = mapped_column(Float)
    bas_pantalon: Mapped[Optional[float]] = mapped_column(Float)
    entrejambe: Mapped[Optional[float]] = mapped_column(Float)
    longueur_robe: Mapped[Optional[float]] = mapped_column(Float)

    client: Mapped["Client"] = relationship(back_populates="mesures")
