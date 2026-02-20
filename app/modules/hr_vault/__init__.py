"""
Coffre-fort RH Numérique - GAP-032

Stockage sécurisé et dématérialisé des documents RH:
- Bulletins de paie électroniques
- Contrats de travail
- Attestations diverses
- Documents de fin de contrat

Conformité: Code du travail, Décret 2016-1762, RGPD, NF Z42-020
"""

from .service import (
    # Énumérations
    DocumentType,
    DocumentStatus,
    AccessType,
    RetentionPeriod,
    EncryptionAlgorithm,

    # Data classes
    Employee,
    DocumentMetadata,
    DocumentVersion,
    VaultDocument,
    AccessLog,
    EncryptionKey,
    ConsentRecord,
    DataPortabilityRequest,

    # Service
    HRVaultService,
    create_hr_vault_service,

    # Constantes
    RETENTION_RULES,
)

__all__ = [
    "DocumentType",
    "DocumentStatus",
    "AccessType",
    "RetentionPeriod",
    "EncryptionAlgorithm",
    "Employee",
    "DocumentMetadata",
    "DocumentVersion",
    "VaultDocument",
    "AccessLog",
    "EncryptionKey",
    "ConsentRecord",
    "DataPortabilityRequest",
    "HRVaultService",
    "create_hr_vault_service",
    "RETENTION_RULES",
]
