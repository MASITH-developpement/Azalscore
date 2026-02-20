"""
Module de Gestion des Contrats (CLM) - GAP-035

Contract Lifecycle Management complet:
- Création et rédaction de contrats
- Templates et clauses réutilisables
- Workflow d'approbation
- Signature électronique intégrée
- Suivi des obligations et jalons
- Alertes de renouvellement/échéance
- Gestion des avenants
- Archivage et recherche
"""

from .service import (
    # Énumérations
    ContractType,
    ContractStatus,
    PartyRole,
    ObligationType,
    RenewalType,
    AmendmentType,

    # Data classes
    ContractParty,
    ContractClause,
    ContractObligation,
    ContractMilestone,
    ContractFinancials,
    ContractDocument,
    ContractAmendment,
    ContractTemplate,
    Contract,
    ContractAlert,

    # Service
    ContractService,
    create_contract_service,
)

__all__ = [
    "ContractType",
    "ContractStatus",
    "PartyRole",
    "ObligationType",
    "RenewalType",
    "AmendmentType",
    "ContractParty",
    "ContractClause",
    "ContractObligation",
    "ContractMilestone",
    "ContractFinancials",
    "ContractDocument",
    "ContractAmendment",
    "ContractTemplate",
    "Contract",
    "ContractAlert",
    "ContractService",
    "create_contract_service",
]
