"""create_all_enum_types

Revision ID: enums_create_all
Revises: a15a43ff0165
Create Date: 2026-01-11 14:30:00.000000+00:00

Cette migration cree tous les types ENUM PostgreSQL necessaires
pour les tables du systeme AZALS.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'enums_create_all'
down_revision: Union[str, None] = 'a15a43ff0165'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Liste de tous les ENUMs a creer
# Format: (nom, valeurs)
ENUM_DEFINITIONS = [
    # --- Accounting & Banking ---
    ('bankconnectionstatus', ['ACTIVE', 'EXPIRED', 'REQUIRES_ACTION', 'ERROR', 'DISCONNECTED']),
    ('emailinboxtype', ['INVOICES', 'EXPENSE_NOTES', 'GENERAL']),
    ('banktransactiontype', ['CREDIT', 'DEBIT', 'TRANSFER', 'FEE', 'INTEREST']),
    ('reconciliationstatus', ['PENDING', 'MATCHED', 'PARTIAL', 'UNMATCHED']),
    ('reconciliationstatusauto', ['PENDING', 'MATCHED', 'PARTIAL', 'MANUAL', 'UNMATCHED']),
    ('journaltype', ['GENERAL', 'PURCHASES', 'SALES', 'BANK', 'CASH', 'OD', 'OPENING', 'CLOSING']),
    ('entrystatus', ['DRAFT', 'PENDING', 'VALIDATED', 'POSTED', 'CANCELLED']),
    ('accounttype', ['ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE']),
    ('fiscalyearstatus', ['OPEN', 'CLOSING', 'CLOSED']),
    ('forecastperiod', ['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY']),
    ('paymentstatus', ['UNPAID', 'PARTIALLY_PAID', 'PAID', 'OVERPAID', 'CANCELLED']),

    # --- Document Processing ---
    ('documenttype', ['INVOICE_RECEIVED', 'INVOICE_SENT', 'EXPENSE_NOTE', 'CREDIT_NOTE_RECEIVED',
                      'CREDIT_NOTE_SENT', 'QUOTE', 'PURCHASE_ORDER', 'DELIVERY_NOTE', 'BANK_STATEMENT', 'OTHER']),
    ('documentsource', ['EMAIL', 'UPLOAD', 'MOBILE_SCAN', 'API', 'BANK_SYNC', 'INTERNAL']),
    ('documentstatus', ['RECEIVED', 'PROCESSING', 'ANALYZED', 'PENDING_VALIDATION', 'VALIDATED', 'ACCOUNTED', 'REJECTED', 'ERROR']),
    ('confidencelevel', ['HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']),
    ('alerttype', ['DOCUMENT_UNREADABLE', 'MISSING_INFO', 'LOW_CONFIDENCE', 'DUPLICATE_SUSPECTED',
                   'AMOUNT_MISMATCH', 'TAX_ERROR', 'OVERDUE_PAYMENT', 'CASH_FLOW_WARNING', 'RECONCILIATION_ISSUE']),
    ('alertseverity', ['INFO', 'WARNING', 'ERROR', 'CRITICAL']),

    # --- Compliance & GRC ---
    ('compliancedocumenttype', ['POLICY', 'PROCEDURE', 'WORK_INSTRUCTION', 'FORM', 'RECORD', 'CERTIFICATE', 'LICENSE', 'PERMIT', 'REPORT']),
    ('regulationtype', ['ISO', 'GDPR', 'SOX', 'FDA', 'CUSTOMS', 'TAX', 'LABOR', 'ENVIRONMENTAL', 'SAFETY', 'QUALITY', 'INDUSTRY_SPECIFIC', 'INTERNAL']),
    ('reporttype', ['COMPLIANCE_STATUS', 'GAP_ANALYSIS', 'RISK_ASSESSMENT', 'AUDIT_SUMMARY', 'INCIDENT_REPORT', 'TRAINING_STATUS', 'REGULATORY_FILING']),
    ('compliancestatus', ['COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'PENDING', 'EXPIRED', 'NOT_APPLICABLE']),
    ('assessmentstatus', ['DRAFT', 'IN_PROGRESS', 'COMPLETED', 'APPROVED', 'REJECTED']),
    ('auditstatus', ['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CLOSED', 'CANCELLED']),
    ('incidentseverity', ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    ('incidentstatus', ['REPORTED', 'INVESTIGATING', 'ACTION_REQUIRED', 'RESOLVED', 'CLOSED']),
    ('requirementpriority', ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    ('risklevel', ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    ('findingseverity', ['OBSERVATION', 'MINOR', 'MAJOR', 'CRITICAL']),
    ('actionstatus', ['OPEN', 'IN_PROGRESS', 'COMPLETED', 'VERIFIED', 'CANCELLED', 'OVERDUE']),

    # --- Tenant & Users ---
    ('tenantstatus', ['PENDING', 'ACTIVE', 'SUSPENDED', 'CANCELLED', 'TRIAL']),
    ('tenantenvironment', ['BETA', 'PRODUCTION', 'STAGING', 'DEVELOPMENT']),
    ('subscriptionplan', ['STARTER', 'PROFESSIONAL', 'ENTERPRISE', 'CUSTOM']),
    ('billingcycle', ['MONTHLY', 'QUARTERLY', 'YEARLY']),
    ('invitationstatus', ['PENDING', 'ACCEPTED', 'EXPIRED', 'CANCELLED']),
    ('modulestatus', ['ACTIVE', 'DISABLED', 'PENDING']),
    ('userrole', ['SUPERADMIN', 'DIRIGEANT', 'ADMIN', 'DAF', 'COMPTABLE', 'COMMERCIAL', 'EMPLOYE']),
    ('viewtype', ['DIRIGEANT', 'ASSISTANTE', 'EXPERT_COMPTABLE']),
    ('decisionlevel', ['GREEN', 'ORANGE', 'RED']),
    ('synctype', ['MANUAL', 'SCHEDULED', 'ON_DEMAND']),
    ('syncstatus', ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED']),
    ('redworkflowstep', ['ACKNOWLEDGE', 'COMPLETENESS', 'FINAL']),

    # --- Inventory & Warehouse ---
    ('warehousetype', ['INTERNAL', 'EXTERNAL', 'TRANSIT', 'VIRTUAL']),
    ('locationtype', ['STORAGE', 'RECEIVING', 'SHIPPING', 'PRODUCTION', 'QUALITY', 'VIRTUAL']),
    ('movementtype', ['IN', 'OUT', 'TRANSFER', 'ADJUSTMENT', 'PRODUCTION', 'RETURN', 'SCRAP']),
    ('movementstatus', ['DRAFT', 'CONFIRMED', 'CANCELLED']),
    ('pickingstatus', ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'DONE', 'CANCELLED']),
    ('inventorystatus', ['DRAFT', 'IN_PROGRESS', 'VALIDATED', 'CANCELLED']),
    ('lotstatus', ['AVAILABLE', 'RESERVED', 'BLOCKED', 'EXPIRED']),
    ('valuationmethod', ['FIFO', 'LIFO', 'AVG', 'STANDARD']),

    # --- Products ---
    ('producttype', ['STOCKABLE', 'CONSUMABLE', 'SERVICE']),
    ('productstatus', ['DRAFT', 'ACTIVE', 'DISCONTINUED', 'BLOCKED']),

    # --- Assets & Maintenance ---
    ('assetcategory', ['MACHINE', 'EQUIPMENT', 'VEHICLE', 'BUILDING', 'INFRASTRUCTURE', 'IT_EQUIPMENT', 'TOOL', 'UTILITY', 'FURNITURE', 'OTHER']),
    ('assetstatus', ['ACTIVE', 'INACTIVE', 'IN_MAINTENANCE', 'RESERVED', 'DISPOSED', 'UNDER_REPAIR', 'STANDBY']),
    ('assetcriticality', ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']),
    ('contracttype', ['FULL_SERVICE', 'PREVENTIVE', 'ON_CALL', 'PARTS_ONLY', 'LABOR_ONLY', 'WARRANTY']),
    ('contractstatus', ['DRAFT', 'ACTIVE', 'SUSPENDED', 'EXPIRED', 'TERMINATED']),
    ('maintenancetype', ['PREVENTIVE', 'CORRECTIVE', 'PREDICTIVE', 'CONDITION_BASED', 'BREAKDOWN', 'IMPROVEMENT', 'INSPECTION', 'CALIBRATION']),
    ('maintenanceworkorderstatus', ['DRAFT', 'REQUESTED', 'APPROVED', 'PLANNED', 'ASSIGNED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'VERIFIED', 'CLOSED', 'CANCELLED']),
    ('workorderpriority', ['EMERGENCY', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SCHEDULED']),
    ('partrequeststatus', ['REQUESTED', 'APPROVED', 'ORDERED', 'RECEIVED', 'ISSUED', 'CANCELLED']),
    ('failuretype', ['MECHANICAL', 'ELECTRICAL', 'ELECTRONIC', 'HYDRAULIC', 'PNEUMATIC', 'SOFTWARE', 'OPERATOR_ERROR', 'WEAR', 'CONTAMINATION', 'UNKNOWN']),
    ('scrapreason', ['DEFECT', 'DAMAGE', 'QUALITY', 'EXPIRED', 'OTHER']),

    # --- Manufacturing (MRP) ---
    ('bomtype', ['MANUFACTURING', 'KIT', 'PHANTOM', 'SUBCONTRACT']),
    ('bomstatus', ['DRAFT', 'ACTIVE', 'OBSOLETE']),
    ('workcentertype', ['MACHINE', 'ASSEMBLY', 'MANUAL', 'QUALITY', 'PACKAGING', 'OUTSOURCED']),
    ('workcenterstatus', ['AVAILABLE', 'BUSY', 'MAINTENANCE', 'OFFLINE']),
    ('operationtype', ['SETUP', 'PRODUCTION', 'QUALITY_CHECK', 'CLEANING', 'PACKAGING', 'TRANSPORT']),
    ('consumptiontype', ['MANUAL', 'AUTO_ON_START', 'AUTO_ON_COMPLETE']),
    ('mostatus', ['DRAFT', 'CONFIRMED', 'PLANNED', 'IN_PROGRESS', 'DONE', 'CANCELLED']),
    ('mopriority', ['LOW', 'NORMAL', 'HIGH', 'URGENT']),
    ('prodworkorderstatus', ['PENDING', 'READY', 'IN_PROGRESS', 'PAUSED', 'DONE', 'CANCELLED']),

    # --- QC Module (Quality Control for modules) ---
    ('qctesttype', ['UNIT', 'INTEGRATION', 'E2E', 'PERFORMANCE', 'SECURITY', 'REGRESSION']),
    ('qccheckstatus', ['PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR']),
    ('qcrulecategory', ['ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'CODE_QUALITY', 'TESTING', 'DOCUMENTATION', 'API', 'DATABASE', 'INTEGRATION', 'COMPLIANCE']),
    ('qcruleseverity', ['INFO', 'WARNING', 'CRITICAL', 'BLOCKER']),
    ('validationphase', ['PRE_QC', 'AUTOMATED', 'MANUAL', 'FINAL', 'POST_DEPLOY']),
    ('qcmodulestatus', ['DRAFT', 'IN_DEVELOPMENT', 'READY_FOR_QC', 'QC_IN_PROGRESS', 'QC_PASSED', 'QC_FAILED', 'PRODUCTION', 'DEPRECATED']),
]


def upgrade() -> None:
    """Cree tous les types ENUM PostgreSQL necessaires."""
    bind = op.get_bind()

    for enum_name, values in ENUM_DEFINITIONS:
        # Creer l'enum avec checkfirst=True pour eviter les erreurs si existe deja
        enum_type = postgresql.ENUM(*values, name=enum_name, create_type=False)
        enum_type.create(bind, checkfirst=True)
        print(f"  [OK] Type ENUM '{enum_name}' cree")


def downgrade() -> None:
    """Supprime tous les types ENUM PostgreSQL."""
    bind = op.get_bind()

    # Supprimer dans l'ordre inverse
    for enum_name, values in reversed(ENUM_DEFINITIONS):
        enum_type = postgresql.ENUM(*values, name=enum_name, create_type=False)
        enum_type.drop(bind, checkfirst=True)
        print(f"  [OK] Type ENUM '{enum_name}' supprime")
