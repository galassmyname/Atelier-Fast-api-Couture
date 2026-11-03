"""Modèles Commande, LigneCommande et HistoriqueStatut."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Commande(Base):
    __tablename__ = "commandes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # CMD-AAAA-NNNNN (RG5), calculé après l'insertion à partir de l'id
    numero: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    mesure_id: Mapped[Optional[int]] = mapped_column(ForeignKey("mesures.id"))
    statut: Mapped[str] = mapped_column(String(20), default="en_attente", index=True)
    date_commande: Mapped[date] = mapped_column(Date)
    date_livraison_prevue: Mapped[date] = mapped_column(Date)
    date_livraison_reelle: Mapped[Optional[date]] = mapped_column(Date)
    # Montants en FCFA, toujours calculés par le serveur (RG7)
    remise: Mapped[int] = mapped_column(Integer, default=0)
    montant_total: Mapped[int] = mapped_column(Integer, default=0)
    montant_paye: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    cree_par_id: Mapped[Optional[int]] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relations
    client: Mapped["Client"] = relationship(back_populates="commandes")
    mesure: Mapped[Optional["Mesure"]] = relationship()
    lignes: Mapped[list["LigneCommande"]] = relationship(
        back_populates="commande", cascade="all, delete-orphan"
    )
    paiements: Mapped[list["Paiement"]] = relationship(
        back_populates="commande", cascade="all, delete-orphan", order_by="Paiement.id"
    )
    historique: Mapped[list["HistoriqueStatut"]] = relationship(
        back_populates="commande",
        cascade="all, delete-orphan",
        order_by="HistoriqueStatut.date_changement",
    )
    # 0 ou 1 livraison : uselist=False donne un objet et non une liste
    livraison: Mapped[Optional["Livraison"]] = relationship(
        back_populates="commande", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def solde(self) -> int:
        """Ce que le client doit encore (RG7)."""
        return self.montant_total - self.montant_paye


class LigneCommande(Base):
    __tablename__ = "lignes_commande"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    type_vetement_id: Mapped[int] = mapped_column(ForeignKey("types_vetement.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    # Prix négociable, par défaut le prix_base du catalogue (RG6)
    prix_unitaire: Mapped[int] = mapped_column(Integer)

    commande: Mapped["Commande"] = relationship(back_populates="lignes")
    type_vetement: Mapped["TypeVetement"] = relationship()

    @property
    def sous_total(self) -> int:
        return self.quantite * self.prix_unitaire


class HistoriqueStatut(Base):
    __tablename__ = "historique_statuts"

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    ancien_statut: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # vide à la création (RG15)
    nouveau_statut: Mapped[str] = mapped_column(String(20))
    commentaire: Mapped[Optional[str]] = mapped_column(Text)
    utilisateur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("utilisateurs.id"))
    date_changement: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    commande: Mapped["Commande"] = relationship(back_populates="historique")
