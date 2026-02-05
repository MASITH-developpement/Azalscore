"""
AZALSCORE - Systeme de numerotation automatique centralise
==========================================================

Sous-programme reutilisable pour generer des references uniques.
Parametrable par tenant via la table sequence_config.

Usage:
    from app.core.sequences import SequenceGenerator

    generator = SequenceGenerator(db, tenant_id)
    ref = generator.next_reference("CLIENT")  # -> CLI-0001
    ref = generator.next_reference("FACTURE_VENTE")  # -> FV-2026-0001
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Session

from app.db.base import Base


# ============================================================================
# MODELE - Configuration des sequences
# ============================================================================

class SequenceConfig(Base):
    """
    Configuration des sequences de numerotation par tenant.
    Permet de personnaliser le format des references dans l'administration.
    """
    __tablename__ = "core_sequence_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification du type d'entite
    entity_type = Column(String(50), nullable=False)  # CLIENT, FACTURE_VENTE, DEVIS, etc.

    # Configuration du format
    prefix = Column(String(10), nullable=False)  # CLI, FV, DEV, etc.
    include_year = Column(Boolean, default=True)  # Inclure l'annee dans la reference
    padding = Column(Integer, default=4)  # Nombre de chiffres (0001, 00001, etc.)
    separator = Column(String(1), default="-")  # Separateur (-, /, .)

    # Compteur actuel
    current_year = Column(Integer, nullable=False)
    current_number = Column(Integer, default=0)

    # Reset annuel
    reset_yearly = Column(Boolean, default=True)  # Repart a 1 chaque annee

    __table_args__ = (
        UniqueConstraint('tenant_id', 'entity_type', name='uq_sequence_tenant_entity'),
        Index('idx_sequence_tenant', 'tenant_id'),
    )


# ============================================================================
# CONFIGURATION PAR DEFAUT DES ENTITES
# ============================================================================

DEFAULT_SEQUENCES = {
    # Commercial - Clients/Fournisseurs
    "CLIENT": {"prefix": "CLI", "include_year": False, "padding": 4, "reset_yearly": False},
    "FOURNISSEUR": {"prefix": "FRN", "include_year": False, "padding": 4, "reset_yearly": False},
    "OPPORTUNITE": {"prefix": "OPP", "include_year": True, "padding": 4, "reset_yearly": True},

    # Commercial - Documents vente
    "DEVIS": {"prefix": "DEV", "include_year": True, "padding": 5, "reset_yearly": True},
    "COMMANDE_CLIENT": {"prefix": "CC", "include_year": True, "padding": 5, "reset_yearly": True},
    "FACTURE_VENTE": {"prefix": "FV", "include_year": True, "padding": 5, "reset_yearly": True},
    "AVOIR_CLIENT": {"prefix": "AV", "include_year": True, "padding": 5, "reset_yearly": True},
    "PROFORMA": {"prefix": "PRO", "include_year": True, "padding": 5, "reset_yearly": True},
    "BON_LIVRAISON": {"prefix": "BL", "include_year": True, "padding": 5, "reset_yearly": True},

    # Commercial - Documents achat
    "COMMANDE_FOURNISSEUR": {"prefix": "CF", "include_year": True, "padding": 5, "reset_yearly": True},
    "FACTURE_ACHAT": {"prefix": "FA", "include_year": True, "padding": 5, "reset_yearly": True},
    "AVOIR_FOURNISSEUR": {"prefix": "AFR", "include_year": True, "padding": 5, "reset_yearly": True},
    "BON_RECEPTION": {"prefix": "BR", "include_year": True, "padding": 5, "reset_yearly": True},

    # RH
    "EMPLOYE": {"prefix": "EMP", "include_year": False, "padding": 4, "reset_yearly": False},

    # Interventions
    "INTERVENTION": {"prefix": "INT", "include_year": True, "padding": 4, "reset_yearly": True},
    "DONNEUR_ORDRE": {"prefix": "DO", "include_year": False, "padding": 4, "reset_yearly": False},
    "RAPPORT_INTERVENTION": {"prefix": "RI", "include_year": True, "padding": 4, "reset_yearly": True},

    # Projets
    "AFFAIRE": {"prefix": "AFF", "include_year": True, "padding": 4, "reset_yearly": True},
    "PROJET": {"prefix": "PRJ", "include_year": True, "padding": 4, "reset_yearly": True},

    # Maintenance
    "ORDRE_MAINTENANCE": {"prefix": "OM", "include_year": True, "padding": 4, "reset_yearly": True},

    # Qualite
    "NON_CONFORMITE": {"prefix": "NC", "include_year": True, "padding": 4, "reset_yearly": True},
    "REGLE_QC": {"prefix": "RQC", "include_year": False, "padding": 4, "reset_yearly": False},
    "INSPECTION": {"prefix": "INS", "include_year": True, "padding": 4, "reset_yearly": True},

    # Helpdesk
    "TICKET": {"prefix": "TIC", "include_year": True, "padding": 5, "reset_yearly": True},
    "CATEGORIE_TICKET": {"prefix": "CAT", "include_year": False, "padding": 3, "reset_yearly": False},

    # Comptabilite
    "PIECE_COMPTABLE": {"prefix": "PC", "include_year": True, "padding": 5, "reset_yearly": True},
    "EXERCICE": {"prefix": "EX", "include_year": False, "padding": 4, "reset_yearly": False},
}


# ============================================================================
# GENERATEUR DE SEQUENCES
# ============================================================================

class SequenceGenerator:
    """
    Generateur de references automatiques.

    Utilise SELECT FOR UPDATE pour eviter les conflits en environnement concurrent.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def next_reference(self, entity_type: str) -> str:
        """
        Genere la prochaine reference pour un type d'entite.

        Args:
            entity_type: Type d'entite (CLIENT, FACTURE_VENTE, etc.)

        Returns:
            Reference formatee (ex: CLI-0001, FV-2026-0001)
        """
        current_year = datetime.utcnow().year

        # Recuperer ou creer la config avec verrouillage
        config = self.db.query(SequenceConfig).filter(
            SequenceConfig.tenant_id == self.tenant_id,
            SequenceConfig.entity_type == entity_type
        ).with_for_update().first()

        if not config:
            # Creer avec les valeurs par defaut
            defaults = DEFAULT_SEQUENCES.get(entity_type, {
                "prefix": entity_type[:3].upper(),
                "include_year": True,
                "padding": 4,
                "reset_yearly": True
            })

            config = SequenceConfig(
                tenant_id=self.tenant_id,
                entity_type=entity_type,
                prefix=defaults["prefix"],
                include_year=defaults["include_year"],
                padding=defaults["padding"],
                reset_yearly=defaults["reset_yearly"],
                current_year=current_year,
                current_number=0
            )
            self.db.add(config)
            self.db.flush()

        # Verifier si on doit reset le compteur (nouvelle annee)
        if config.reset_yearly and config.current_year != current_year:
            config.current_year = current_year
            config.current_number = 0

        # Incrementer
        config.current_number += 1

        # Formater la reference
        if config.include_year:
            reference = f"{config.prefix}{config.separator}{current_year}{config.separator}{config.current_number:0{config.padding}d}"
        else:
            reference = f"{config.prefix}{config.separator}{config.current_number:0{config.padding}d}"

        return reference

    def get_config(self, entity_type: str) -> dict:
        """Recupere la configuration d'une sequence."""
        config = self.db.query(SequenceConfig).filter(
            SequenceConfig.tenant_id == self.tenant_id,
            SequenceConfig.entity_type == entity_type
        ).first()

        if config:
            return {
                "entity_type": config.entity_type,
                "prefix": config.prefix,
                "include_year": config.include_year,
                "padding": config.padding,
                "separator": config.separator,
                "reset_yearly": config.reset_yearly,
                "current_year": config.current_year,
                "current_number": config.current_number,
            }

        # Retourner les valeurs par defaut
        return DEFAULT_SEQUENCES.get(entity_type, {})

    def update_config(
        self,
        entity_type: str,
        prefix: str = None,
        include_year: bool = None,
        padding: int = None,
        separator: str = None,
        reset_yearly: bool = None
    ) -> SequenceConfig:
        """
        Met a jour la configuration d'une sequence.
        Pour l'administration.
        """
        config = self.db.query(SequenceConfig).filter(
            SequenceConfig.tenant_id == self.tenant_id,
            SequenceConfig.entity_type == entity_type
        ).first()

        if not config:
            # Creer avec les valeurs par defaut puis appliquer les modifications
            defaults = DEFAULT_SEQUENCES.get(entity_type, {
                "prefix": entity_type[:3].upper(),
                "include_year": True,
                "padding": 4,
                "reset_yearly": True
            })

            config = SequenceConfig(
                tenant_id=self.tenant_id,
                entity_type=entity_type,
                prefix=defaults["prefix"],
                include_year=defaults["include_year"],
                padding=defaults["padding"],
                reset_yearly=defaults["reset_yearly"],
                current_year=datetime.utcnow().year,
                current_number=0
            )
            self.db.add(config)

        # Appliquer les modifications
        if prefix is not None:
            config.prefix = prefix
        if include_year is not None:
            config.include_year = include_year
        if padding is not None:
            config.padding = padding
        if separator is not None:
            config.separator = separator
        if reset_yearly is not None:
            config.reset_yearly = reset_yearly

        self.db.commit()
        self.db.refresh(config)
        return config

    def list_configs(self) -> list[dict]:
        """Liste toutes les configurations du tenant."""
        configs = self.db.query(SequenceConfig).filter(
            SequenceConfig.tenant_id == self.tenant_id
        ).all()

        result = []

        # Ajouter les configs existantes
        existing_types = set()
        for config in configs:
            existing_types.add(config.entity_type)
            result.append({
                "entity_type": config.entity_type,
                "prefix": config.prefix,
                "include_year": config.include_year,
                "padding": config.padding,
                "separator": config.separator,
                "reset_yearly": config.reset_yearly,
                "current_year": config.current_year,
                "current_number": config.current_number,
                "configured": True
            })

        # Ajouter les types par defaut non configures
        for entity_type, defaults in DEFAULT_SEQUENCES.items():
            if entity_type not in existing_types:
                result.append({
                    "entity_type": entity_type,
                    "prefix": defaults["prefix"],
                    "include_year": defaults["include_year"],
                    "padding": defaults["padding"],
                    "separator": "-",
                    "reset_yearly": defaults["reset_yearly"],
                    "current_year": datetime.utcnow().year,
                    "current_number": 0,
                    "configured": False
                })

        return sorted(result, key=lambda x: x["entity_type"])
