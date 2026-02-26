"""
AZALS MODULE - FEC: Modèles
===========================

Modèles SQLAlchemy pour le suivi des exports FEC.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
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
)
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class FECFormat(str, enum.Enum):
    """Format de fichier FEC."""
    TXT = "txt"  # Format texte tabulé (standard)
    XML = "xml"  # Format XML (optionnel)


class FECEncoding(str, enum.Enum):
    """Encodage du fichier FEC."""
    UTF8 = "UTF-8"
    ISO_8859_15 = "ISO-8859-15"  # Latin-9 (Europe occidentale)


class FECSeparator(str, enum.Enum):
    """Séparateur de champs FEC."""
    TAB = "TAB"    # Tabulation (recommandé)
    PIPE = "PIPE"  # Caractère pipe |


class FECExportStatus(str, enum.Enum):
    """Statut d'export FEC."""
    PENDING = "PENDING"        # En attente
    GENERATING = "GENERATING"  # Génération en cours
    VALIDATING = "VALIDATING"  # Validation en cours
    COMPLETED = "COMPLETED"    # Terminé avec succès
    FAILED = "FAILED"          # Échec
    ARCHIVED = "ARCHIVED"      # Archivé


class FECValidationLevel(str, enum.Enum):
    """Niveau de validation FEC."""
    ERROR = "ERROR"      # Erreur bloquante (non conforme)
    WARNING = "WARNING"  # Avertissement (conforme mais à vérifier)
    INFO = "INFO"        # Information


# ============================================================================
# MODÈLES
# ============================================================================

class FECExport(Base):
    """
    Export FEC (Fichier des Écritures Comptables).

    Traçabilité complète des exports FEC générés pour le contrôle fiscal.
    """
    __tablename__ = "fec_exports"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification entreprise
    siren = Column(String(9), nullable=False)  # SIREN 9 chiffres
    company_name = Column(String(255), nullable=False)

    # Exercice fiscal
    fiscal_year_id = Column(UniversalUUID(), ForeignKey("fiscal_years.id"), nullable=False)
    fiscal_year_code = Column(String(20), nullable=False)  # Ex: "2025"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Paramètres export
    format = Column(Enum(FECFormat), default=FECFormat.TXT, nullable=False)
    encoding = Column(Enum(FECEncoding), default=FECEncoding.UTF8, nullable=False)
    separator = Column(Enum(FECSeparator), default=FECSeparator.TAB, nullable=False)

    # Fichier généré
    filename = Column(String(255))  # Ex: "123456789FEC20260131.txt"
    file_path = Column(String(500))  # Chemin complet
    file_size = Column(Integer)  # Taille en octets
    file_hash = Column(String(64))  # SHA-256 du fichier

    # Statistiques
    total_entries = Column(Integer, default=0)  # Nombre d'écritures
    total_lines = Column(Integer, default=0)    # Nombre de lignes
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)

    # Statut
    status = Column(Enum(FECExportStatus), default=FECExportStatus.PENDING, nullable=False)

    # Validation
    is_valid = Column(Boolean, default=False)
    validation_errors = Column(Integer, default=0)
    validation_warnings = Column(Integer, default=0)
    validation_details = Column(JSON, default=list)

    # Messages
    error_message = Column(Text)

    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Audit
    requested_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Index
    __table_args__ = (
        Index('idx_fec_exports_tenant', 'tenant_id'),
        Index('idx_fec_exports_siren', 'siren'),
        Index('idx_fec_exports_fiscal_year', 'fiscal_year_id'),
        Index('idx_fec_exports_status', 'status'),
        Index('idx_fec_exports_tenant_year', 'tenant_id', 'fiscal_year_code'),
    )


class FECValidationResult(Base):
    """
    Résultat de validation FEC.

    Détail des erreurs et avertissements de validation.
    """
    __tablename__ = "fec_validation_results"

    # Clé primaire
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Export associé
    export_id = Column(UniversalUUID(), ForeignKey("fec_exports.id", ondelete="CASCADE"), nullable=False)

    # Validation
    level = Column(Enum(FECValidationLevel), nullable=False)
    code = Column(String(20), nullable=False)  # Code erreur (ex: FEC-001)
    message = Column(Text, nullable=False)

    # Localisation
    line_number = Column(Integer)  # Numéro de ligne concernée
    column_name = Column(String(50))  # Nom de colonne concernée
    entry_number = Column(String(50))  # Numéro d'écriture concernée

    # Valeurs
    expected_value = Column(String(255))
    actual_value = Column(String(255))

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Index
    __table_args__ = (
        Index('idx_fec_validation_export', 'export_id'),
        Index('idx_fec_validation_level', 'level'),
        Index('idx_fec_validation_code', 'code'),
    )


class FECArchive(Base):
    """
    Archive FEC pour conservation légale (10 ans).

    Copie immuable des exports FEC avec signature.
    """
    __tablename__ = "fec_archives"

    # Clé primaire
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Export source
    export_id = Column(UniversalUUID(), ForeignKey("fec_exports.id"), nullable=False)

    # Identification
    siren = Column(String(9), nullable=False)
    fiscal_year_code = Column(String(20), nullable=False)

    # Fichier archivé
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    file_size = Column(Integer, nullable=False)

    # Signature (horodatage qualifié optionnel)
    signature = Column(Text)
    signature_timestamp = Column(DateTime)
    signature_authority = Column(String(255))

    # Conservation
    archived_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    retention_until = Column(DateTime, nullable=False)  # Date de fin de conservation (10 ans)

    # Statut
    is_deleted = Column(Boolean, default=False)  # Suppression logique uniquement après 10 ans
    deleted_at = Column(DateTime)

    # Audit
    archived_by = Column(UniversalUUID())

    # Index
    __table_args__ = (
        Index('idx_fec_archives_tenant', 'tenant_id'),
        Index('idx_fec_archives_siren_year', 'siren', 'fiscal_year_code'),
        Index('idx_fec_archives_retention', 'retention_until'),
    )
