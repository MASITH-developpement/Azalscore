"""
AZALS - Alembic Environment Configuration
==========================================

This module configures Alembic for database migrations.
It imports all SQLAlchemy models to enable auto-generation of migrations.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the database Base and all models
# IMPORTANT: Import Base from app.db (not app.core.database) for unified metadata
from app.db import Base

# Import all models to ensure they're registered with Base.metadata
# Core models
from app.core.models import User, CoreAuditJournal, Item, Decision, RedDecisionWorkflow, RedDecisionReport, TreasuryForecast

# Tenant models
from app.modules.tenants.models import (
    Tenant, TenantSubscription, TenantModule, TenantInvitation,
    TenantUsage, TenantEvent, TenantSettings, TenantOnboarding
)

# Inventory models (already using UUID)
from app.modules.inventory.models import (
    Product, ProductCategory, Warehouse, Location,
    StockMovement, StockMovementLine, StockLevel,
    InventoryCount, InventoryCountLine, Lot, SerialNumber,
    Picking, PickingLine, ReplenishmentRule, StockValuation
)

# Maintenance models (REFACTORED to UUID)
from app.modules.maintenance.models import (
    Asset, AssetComponent, AssetDocument, AssetMeter, MeterReading,
    MaintenancePlan, MaintenancePlanTask, MaintenanceWorkOrder, WorkOrderTask,
    WorkOrderLabor, WorkOrderPart, Failure, FailureCause,
    SparePart, SparePartStock, PartRequest, MaintenanceContract, MaintenanceKPI
)

# Quality models (REFACTORED to UUID)
from app.modules.quality.models import (
    NonConformance, NonConformanceAction, QualityControlTemplate,
    QualityControlTemplateItem, QualityControl, QualityControlLine,
    QualityAudit, AuditFinding, CAPA, CAPAAction,
    CustomerClaim, ClaimAction, QualityIndicator, IndicatorMeasurement,
    Certification, CertificationAudit
)

# Production models (already using UUID)
try:
    from app.modules.production.models import (
        ProductionLine, WorkCenter, BillOfMaterials, BOMLine,
        ProductionOrder, ProductionOrderLine, ProductionOperation,
        ProductionConsumption, ProductionOutput, ProductionKPI
    )
except ImportError:
    pass  # Module may not exist

# Compliance models (already using UUID)
try:
    from app.modules.compliance.models import (
        ComplianceRequirement, ComplianceControl, ComplianceEvidence,
        ComplianceAssessment, ComplianceRisk, ComplianceAction
    )
except ImportError:
    pass  # Module may not exist

# Automated Accounting models (already using UUID)
try:
    from app.modules.automated_accounting.models import (
        AccountingRule, BankAccount, BankTransaction,
        AccountingEntry, Reconciliation
    )
except ImportError:
    pass  # Module may not exist

# AI Guardian models (Mode A/B/C)
try:
    from app.modules.guardian.ai_models import (
        AIIncident, AIModuleScore, AIAuditReport,
        AISLAMetric, AIConfig
    )
except ImportError:
    pass  # Module may not exist

# Add metadata for autogenerate support
target_metadata = Base.metadata

# Get database URL from environment or config
def get_url():
    """Get database URL from environment variable."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fallback for development
        url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("DATABASE_URL environment variable is required")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include schemas
        include_schemas=True,
        # Compare server default values
        compare_server_default=True,
        # Compare type changes
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include schemas
            include_schemas=True,
            # Compare server default values
            compare_server_default=True,
            # Compare type changes
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
