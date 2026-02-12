"""
AZALS - Database Module
=======================
Module de base de donnees unifie avec support UUID obligatoire.

EXPORTS PRINCIPAUX:
- Base: Classe de base ORM avec UUIDMixin integre
- load_all_models: Fonction pour charger tous les modeles ORM
- verify_models_loaded: Verification que les modeles sont charges
- UUIDComplianceManager: Gestionnaire de conformite UUID
- TenantContext: Contexte d'isolation multi-tenant
- TenantMixin: Mixin pour modeles tenant-scoped

USAGE:
    from app.db import Base, load_all_models, UUIDComplianceManager
    from app.db import TenantContext, get_current_tenant_id
    load_all_models()  # Charger tous les modeles avant operations DB

SÉCURITÉ MULTI-TENANT:
    with TenantContext(db, tenant_id):
        items = db.query(Item).all()  # Filtré automatiquement
"""

from app.db.base import Base
from app.db.model_loader import get_loaded_modules, get_loaded_table_count, load_all_models, verify_models_loaded
from app.db.uuid_base import UUIDForeignKey, UUIDMixin, uuid_column, uuid_fk_column
from app.db.uuid_reset import UUIDComplianceError, UUIDComplianceManager, UUIDResetBlockedError, reset_database_for_uuid
from app.db.tenant_isolation import (
    TenantContext,
    TenantMixin,
    get_current_tenant_id,
    set_current_tenant_id,
    has_tenant_id,
    setup_tenant_filtering,
    tenant_required,
    validate_tenant_isolation,
)

__all__ = [
    # Base ORM
    'Base',
    # UUID utilities
    'UUIDMixin',
    'UUIDForeignKey',
    'uuid_column',
    'uuid_fk_column',
    # Model loader
    'load_all_models',
    'verify_models_loaded',
    'get_loaded_table_count',
    'get_loaded_modules',
    # UUID compliance
    'UUIDComplianceManager',
    'UUIDComplianceError',
    'UUIDResetBlockedError',
    'reset_database_for_uuid',
    # Tenant isolation (SÉCURITÉ P1)
    'TenantContext',
    'TenantMixin',
    'get_current_tenant_id',
    'set_current_tenant_id',
    'has_tenant_id',
    'setup_tenant_filtering',
    'tenant_required',
    'validate_tenant_isolation',
]
