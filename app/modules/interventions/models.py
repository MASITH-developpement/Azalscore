"""
AZALS MODULE INTERVENTIONS - Models
====================================

Modèles SQLAlchemy pour le module Interventions v1.

Entités:
- Intervention (avec numérotation INT-YYYY-XXXX)
- RapportIntervention
- RapportFinal
- DonneurOrdre
- InterventionSequence (pour numérotation transactionnelle)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base
from app.core.types import UniversalUUID

# ============================================================================
# ENUMS
# ============================================================================

class InterventionStatut(str, enum.Enum):
    """Statut de l'intervention - workflow strict."""
    A_PLANIFIER = "A_PLANIFIER"
    PLANIFIEE = "PLANIFIEE"
    EN_COURS = "EN_COURS"
    TERMINEE = "TERMINEE"


class InterventionPriorite(str, enum.Enum):
    """Priorité de l'intervention."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class TypeIntervention(str, enum.Enum):
    """Type d'intervention."""
    INSTALLATION = "INSTALLATION"
    MAINTENANCE = "MAINTENANCE"
    REPARATION = "REPARATION"
    INSPECTION = "INSPECTION"
    FORMATION = "FORMATION"
    CONSULTATION = "CONSULTATION"
    AUTRE = "AUTRE"


class CanalDemande(str, enum.Enum):
    """Canal de la demande d'intervention."""
    TELEPHONE = "TELEPHONE"
    EMAIL = "EMAIL"
    PORTAIL = "PORTAIL"
    DIRECT = "DIRECT"
    CONTRAT = "CONTRAT"
    AUTRE = "AUTRE"


# ============================================================================
# SEQUENCE NUMEROTATION (pour anti-conflit transactionnel)
# ============================================================================

class InterventionSequence(Base):
    """
    Séquence de numérotation par tenant et année.
    Utilisée pour générer INT-YYYY-XXXX de manière transactionnelle.
    """
    __tablename__ = "int_sequences"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    last_number = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'year', name='uq_int_seq_tenant_year'),
        Index('idx_int_seq_tenant_year', 'tenant_id', 'year'),
    )


# ============================================================================
# DONNEUR D'ORDRE
# ============================================================================

class DonneurOrdre(Base):
    """
    Donneur d'ordre pour les interventions.
    Peut être un client, un fournisseur ou une entité distincte.
    """
    __tablename__ = "int_donneurs_ordre"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    nom = Column(String(255), nullable=False)
    type = Column(String(50))  # CLIENT, FOURNISSEUR, AUTRE

    # Référence externe
    client_id = Column(UniversalUUID())  # Lien vers customers si applicable
    fournisseur_id = Column(UniversalUUID())  # Lien vers suppliers si applicable

    # Contact
    email = Column(String(255))
    telephone = Column(String(50))
    adresse = Column(Text)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    interventions = relationship("Intervention", back_populates="donneur_ordre")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_do_tenant_code'),
        Index('idx_do_tenant', 'tenant_id'),
        Index('idx_do_tenant_code', 'tenant_id', 'code'),
    )


# ============================================================================
# INTERVENTION (Entité principale)
# ============================================================================

class Intervention(Base):
    """
    Intervention terrain v1.

    Règles métier:
    - reference: INT-YYYY-XXXX, générée automatiquement, JAMAIS modifiable
    - client_id: OBLIGATOIRE
    - donneur_ordre_id: OPTIONNEL, jamais implicite
    - Workflow statut strict: A_PLANIFIER -> PLANIFIEE -> EN_COURS -> TERMINEE
    - Temps automatique via actions terrain (pas de feuille de temps manuelle)
    """
    __tablename__ = "int_interventions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # =========================================
    # REFERENCE OFFICIELLE (NON MODIFIABLE)
    # =========================================
    reference = Column(String(20), nullable=False)
    # Format: INT-YYYY-XXXX (ex: INT-2026-0001)
    # Générée à la création, incrémentée par tenant, transactionnelle
    # Note: Unique par tenant via l'index idx_int_tenant_reference

    # =========================================
    # RELATIONS PRINCIPALES
    # =========================================
    client_id = Column(UniversalUUID(), nullable=False, index=True)  # OBLIGATOIRE
    donneur_ordre_id = Column(UniversalUUID(), ForeignKey("int_donneurs_ordre.id"), index=True)  # OPTIONNEL
    projet_id = Column(UniversalUUID(), index=True)  # OPTIONNEL

    # Relations lecture seule (générées par d'autres modules)
    devis_id = Column(UniversalUUID())  # Lecture seule
    facture_client_id = Column(UniversalUUID())  # Lecture seule
    commande_fournisseur_id = Column(UniversalUUID())  # Lecture seule

    # =========================================
    # INFORMATIONS INTERVENTION
    # =========================================
    type_intervention = Column(Enum(TypeIntervention), default=TypeIntervention.AUTRE)
    priorite = Column(Enum(InterventionPriorite), default=InterventionPriorite.NORMAL)
    reference_externe = Column(String(100))  # OPTIONNEL
    canal_demande = Column(Enum(CanalDemande))  # OPTIONNEL

    # Description
    titre = Column(String(500))
    description = Column(Text)
    notes_internes = Column(Text)

    # =========================================
    # PLANIFICATION
    # =========================================
    date_prevue_debut = Column(DateTime)
    date_prevue_fin = Column(DateTime)

    # Technicien assigné
    intervenant_id = Column(UniversalUUID(), index=True)

    # Lien vers événement Planning
    planning_event_id = Column(UniversalUUID())

    # =========================================
    # TEMPS AUTOMATIQUE (RÈGLE MAJEURE)
    # =========================================
    date_arrivee_site = Column(DateTime)  # Horodatage arrivee_sur_site()
    date_demarrage = Column(DateTime)  # Horodatage demarrer_intervention()
    date_fin = Column(DateTime)  # Horodatage terminer_intervention()

    # Durée calculée automatiquement en minutes
    duree_reelle_minutes = Column(Integer)

    # Géolocalisation arrivée
    geoloc_arrivee_lat = Column(Numeric(10, 7))
    geoloc_arrivee_lng = Column(Numeric(10, 7))

    # =========================================
    # STATUT (WORKFLOW STRICT)
    # =========================================
    statut = Column(
        Enum(InterventionStatut),
        default=InterventionStatut.A_PLANIFIER,
        nullable=False
    )

    # =========================================
    # ADRESSE INTERVENTION
    # =========================================
    adresse_ligne1 = Column(String(255))
    adresse_ligne2 = Column(String(255))
    ville = Column(String(100))
    code_postal = Column(String(20))
    pays = Column(String(100), default="France")

    # =========================================
    # MÉTADONNÉES
    # =========================================
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)  # Soft delete

    # =========================================
    # RELATIONS
    # =========================================
    donneur_ordre = relationship("DonneurOrdre", back_populates="interventions")
    rapport = relationship(
        "RapportIntervention",
        back_populates="intervention",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_int_tenant', 'tenant_id'),
        Index('idx_int_reference', 'reference'),
        Index('idx_int_tenant_reference', 'tenant_id', 'reference', unique=True),
        Index('idx_int_tenant_client', 'tenant_id', 'client_id'),
        Index('idx_int_tenant_statut', 'tenant_id', 'statut'),
        Index('idx_int_tenant_projet', 'tenant_id', 'projet_id'),
        Index('idx_int_tenant_donneur', 'tenant_id', 'donneur_ordre_id'),
        Index('idx_int_tenant_dates', 'tenant_id', 'date_prevue_debut', 'date_prevue_fin'),
    )


# ============================================================================
# RAPPORT D'INTERVENTION
# ============================================================================

class RapportIntervention(Base):
    """
    Rapport d'intervention.

    Règles:
    - Généré automatiquement à la fin d'intervention
    - Figé après signature
    - Non modifiable après signature
    """
    __tablename__ = "int_rapports"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    intervention_id = Column(
        UniversalUUID(),
        ForeignKey("int_interventions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Références copiées pour traçabilité
    reference_intervention = Column(String(20), nullable=False)
    client_id = Column(UniversalUUID(), nullable=False)
    donneur_ordre_id = Column(UniversalUUID())

    # Contenu du rapport
    resume_actions = Column(Text)
    anomalies = Column(Text)
    recommandations = Column(Text)

    # Photos (métadonnées JSON)
    photos = Column(JSON, default=list)
    # Format: [{"url": "...", "caption": "...", "taken_at": "..."}]

    # Signature client
    signature_client = Column(Text)  # Hash/blob sécurisé base64
    date_signature = Column(DateTime)
    nom_signataire = Column(String(255))

    # Géolocalisation signature
    geoloc_signature_lat = Column(Numeric(10, 7))
    geoloc_signature_lng = Column(Numeric(10, 7))

    # Verrouillage après signature
    is_signed = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relation
    intervention = relationship("Intervention", back_populates="rapport")

    __table_args__ = (
        Index('idx_rapport_tenant', 'tenant_id'),
        Index('idx_rapport_intervention', 'intervention_id'),
        Index('idx_rapport_tenant_client', 'tenant_id', 'client_id'),
    )


# ============================================================================
# RAPPORT FINAL (Consolidé par projet/dossier)
# ============================================================================

class RapportFinal(Base):
    """
    Rapport final consolidé.

    Généré automatiquement si plusieurs interventions partagent:
    - le même projet_id
    - OU le même dossier/donneur d'ordre

    Règles:
    - Non modifiable
    - Traçable
    - Horodaté
    """
    __tablename__ = "int_rapports_final"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Critère de regroupement
    projet_id = Column(UniversalUUID(), index=True)
    donneur_ordre_id = Column(UniversalUUID(), index=True)

    # Référence du rapport final
    reference = Column(String(50), nullable=False, unique=True)
    # Format: RFINAL-YYYY-XXXX

    # Liste des interventions consolidées
    interventions_references = Column(JSON, nullable=False)
    # Format: ["INT-2026-0001", "INT-2026-0002", ...]

    # Temps total cumulé (minutes)
    temps_total_minutes = Column(Integer, nullable=False, default=0)

    # Synthèse consolidée
    synthese = Column(Text)

    # Date de génération
    date_generation = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Verrouillage (toujours verrouillé à la création)
    is_locked = Column(Boolean, default=True, nullable=False)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_rfinal_tenant', 'tenant_id'),
        Index('idx_rfinal_reference', 'reference'),
        Index('idx_rfinal_tenant_projet', 'tenant_id', 'projet_id'),
        Index('idx_rfinal_tenant_donneur', 'tenant_id', 'donneur_ordre_id'),
    )
