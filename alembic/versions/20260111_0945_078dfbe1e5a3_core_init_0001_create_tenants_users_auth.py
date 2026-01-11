"""core_init_0001_create_tenants_users_auth

Revision ID: 078dfbe1e5a3
Revises: system_settings_001
Create Date: 2026-01-11 09:45:12.049928+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '078dfbe1e5a3'
down_revision: Union[str, None] = 'system_settings_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ==============================================================================
# ENUMs PostgreSQL déclarés en mode SAFE (no CREATE TYPE)
# Tous les ENUMs utilisent create_type=False pour éviter l'erreur
# "psycopg2.errors.DuplicateObject: type XXX already exists"
# Cette migration est IDEMPOTENTE et safe pour production/CI/rebuild
# ==============================================================================

# --- Accounting & Banking ---
bankconnectionstatus_enum = postgresql.ENUM(
    'ACTIVE', 'EXPIRED', 'REQUIRES_ACTION', 'ERROR', 'DISCONNECTED',
    name='bankconnectionstatus', create_type=False
)
emailinboxtype_enum = postgresql.ENUM(
    'INVOICES', 'EXPENSE_NOTES', 'GENERAL',
    name='emailinboxtype', create_type=False
)
banktransactiontype_enum = postgresql.ENUM(
    'CREDIT', 'DEBIT', 'TRANSFER', 'FEE', 'INTEREST',
    name='banktransactiontype', create_type=False
)
reconciliationstatus_enum = postgresql.ENUM(
    'PENDING', 'MATCHED', 'PARTIAL', 'UNMATCHED',
    name='reconciliationstatus', create_type=False
)
reconciliationstatusauto_enum = postgresql.ENUM(
    'PENDING', 'MATCHED', 'PARTIAL', 'MANUAL', 'UNMATCHED',
    name='reconciliationstatusauto', create_type=False
)
journaltype_enum = postgresql.ENUM(
    'GENERAL', 'PURCHASES', 'SALES', 'BANK', 'CASH', 'OD', 'OPENING', 'CLOSING',
    name='journaltype', create_type=False
)
entrystatus_enum = postgresql.ENUM(
    'DRAFT', 'PENDING', 'VALIDATED', 'POSTED', 'CANCELLED',
    name='entrystatus', create_type=False
)
accounttype_enum = postgresql.ENUM(
    'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE',
    name='accounttype', create_type=False
)
fiscalyearstatus_enum = postgresql.ENUM(
    'OPEN', 'CLOSING', 'CLOSED',
    name='fiscalyearstatus', create_type=False
)
forecastperiod_enum = postgresql.ENUM(
    'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY',
    name='forecastperiod', create_type=False
)
paymentstatus_enum = postgresql.ENUM(
    'UNPAID', 'PARTIALLY_PAID', 'PAID', 'OVERPAID', 'CANCELLED',
    name='paymentstatus', create_type=False
)

# --- Document Processing ---
documenttype_enum = postgresql.ENUM(
    'INVOICE_RECEIVED', 'INVOICE_SENT', 'EXPENSE_NOTE', 'CREDIT_NOTE_RECEIVED',
    'CREDIT_NOTE_SENT', 'QUOTE', 'PURCHASE_ORDER', 'DELIVERY_NOTE', 'BANK_STATEMENT', 'OTHER',
    name='documenttype', create_type=False
)
documentsource_enum = postgresql.ENUM(
    'EMAIL', 'UPLOAD', 'MOBILE_SCAN', 'API', 'BANK_SYNC', 'INTERNAL',
    name='documentsource', create_type=False
)
documentstatus_enum = postgresql.ENUM(
    'RECEIVED', 'PROCESSING', 'ANALYZED', 'PENDING_VALIDATION', 'VALIDATED', 'ACCOUNTED', 'REJECTED', 'ERROR',
    name='documentstatus', create_type=False
)
confidencelevel_enum = postgresql.ENUM(
    'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW',
    name='confidencelevel', create_type=False
)
alerttype_enum = postgresql.ENUM(
    'DOCUMENT_UNREADABLE', 'MISSING_INFO', 'LOW_CONFIDENCE', 'DUPLICATE_SUSPECTED',
    'AMOUNT_MISMATCH', 'TAX_ERROR', 'OVERDUE_PAYMENT', 'CASH_FLOW_WARNING', 'RECONCILIATION_ISSUE',
    name='alerttype', create_type=False
)
alertseverity_enum = postgresql.ENUM(
    'INFO', 'WARNING', 'ERROR', 'CRITICAL',
    name='alertseverity', create_type=False
)

# --- Compliance & GRC (documenttype différent - compliance) ---
compliancedocumenttype_enum = postgresql.ENUM(
    'POLICY', 'PROCEDURE', 'WORK_INSTRUCTION', 'FORM', 'RECORD', 'CERTIFICATE', 'LICENSE', 'PERMIT', 'REPORT',
    name='compliancedocumenttype', create_type=False
)
regulationtype_enum = postgresql.ENUM(
    'ISO', 'GDPR', 'SOX', 'FDA', 'CUSTOMS', 'TAX', 'LABOR', 'ENVIRONMENTAL', 'SAFETY', 'QUALITY', 'INDUSTRY_SPECIFIC', 'INTERNAL',
    name='regulationtype', create_type=False
)
reporttype_enum = postgresql.ENUM(
    'COMPLIANCE_STATUS', 'GAP_ANALYSIS', 'RISK_ASSESSMENT', 'AUDIT_SUMMARY', 'INCIDENT_REPORT', 'TRAINING_STATUS', 'REGULATORY_FILING',
    name='reporttype', create_type=False
)
compliancestatus_enum = postgresql.ENUM(
    'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'PENDING', 'EXPIRED', 'NOT_APPLICABLE',
    name='compliancestatus', create_type=False
)
assessmentstatus_enum = postgresql.ENUM(
    'DRAFT', 'IN_PROGRESS', 'COMPLETED', 'APPROVED', 'REJECTED',
    name='assessmentstatus', create_type=False
)
auditstatus_enum = postgresql.ENUM(
    'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CLOSED', 'CANCELLED',
    name='auditstatus', create_type=False
)
incidentseverity_enum = postgresql.ENUM(
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
    name='incidentseverity', create_type=False
)
incidentstatus_enum = postgresql.ENUM(
    'REPORTED', 'INVESTIGATING', 'ACTION_REQUIRED', 'RESOLVED', 'CLOSED',
    name='incidentstatus', create_type=False
)
requirementpriority_enum = postgresql.ENUM(
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
    name='requirementpriority', create_type=False
)
risklevel_enum = postgresql.ENUM(
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
    name='risklevel', create_type=False
)
findingseverity_enum = postgresql.ENUM(
    'OBSERVATION', 'MINOR', 'MAJOR', 'CRITICAL',
    name='findingseverity', create_type=False
)
actionstatus_enum = postgresql.ENUM(
    'OPEN', 'IN_PROGRESS', 'COMPLETED', 'VERIFIED', 'CANCELLED', 'OVERDUE',
    name='actionstatus', create_type=False
)

# --- Tenant & Users ---
tenantstatus_enum = postgresql.ENUM(
    'PENDING', 'ACTIVE', 'SUSPENDED', 'CANCELLED', 'TRIAL',
    name='tenantstatus', create_type=False
)
tenantenvironment_enum = postgresql.ENUM(
    'BETA', 'PRODUCTION', 'STAGING', 'DEVELOPMENT',
    name='tenantenvironment', create_type=False
)
subscriptionplan_enum = postgresql.ENUM(
    'STARTER', 'PROFESSIONAL', 'ENTERPRISE', 'CUSTOM',
    name='subscriptionplan', create_type=False
)
billingcycle_enum = postgresql.ENUM(
    'MONTHLY', 'QUARTERLY', 'YEARLY',
    name='billingcycle', create_type=False
)
invitationstatus_enum = postgresql.ENUM(
    'PENDING', 'ACCEPTED', 'EXPIRED', 'CANCELLED',
    name='invitationstatus', create_type=False
)
tenantmodulestatus_enum = postgresql.ENUM(
    'ACTIVE', 'DISABLED', 'PENDING',
    name='modulestatus', create_type=False
)
userrole_enum = postgresql.ENUM(
    'SUPERADMIN', 'DIRIGEANT', 'ADMIN', 'DAF', 'COMPTABLE', 'COMMERCIAL', 'EMPLOYE',
    name='userrole', create_type=False
)
viewtype_enum = postgresql.ENUM(
    'DIRIGEANT', 'ASSISTANTE', 'EXPERT_COMPTABLE',
    name='viewtype', create_type=False
)
decisionlevel_enum = postgresql.ENUM(
    'GREEN', 'ORANGE', 'RED',
    name='decisionlevel', create_type=False
)
synctype_enum = postgresql.ENUM(
    'MANUAL', 'SCHEDULED', 'ON_DEMAND',
    name='synctype', create_type=False
)
syncstatus_enum = postgresql.ENUM(
    'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED',
    name='syncstatus', create_type=False
)
redworkflowstep_enum = postgresql.ENUM(
    'ACKNOWLEDGE', 'COMPLETENESS', 'FINAL',
    name='redworkflowstep', create_type=False
)

# --- Inventory & Warehouse ---
warehousetype_enum = postgresql.ENUM(
    'INTERNAL', 'EXTERNAL', 'TRANSIT', 'VIRTUAL',
    name='warehousetype', create_type=False
)
locationtype_enum = postgresql.ENUM(
    'STORAGE', 'RECEIVING', 'SHIPPING', 'PRODUCTION', 'QUALITY', 'VIRTUAL',
    name='locationtype', create_type=False
)
movementtype_enum = postgresql.ENUM(
    'IN', 'OUT', 'TRANSFER', 'ADJUSTMENT', 'PRODUCTION', 'RETURN', 'SCRAP',
    name='movementtype', create_type=False
)
movementstatus_enum = postgresql.ENUM(
    'DRAFT', 'CONFIRMED', 'CANCELLED',
    name='movementstatus', create_type=False
)
pickingstatus_enum = postgresql.ENUM(
    'PENDING', 'ASSIGNED', 'IN_PROGRESS', 'DONE', 'CANCELLED',
    name='pickingstatus', create_type=False
)
inventorystatus_enum = postgresql.ENUM(
    'DRAFT', 'IN_PROGRESS', 'VALIDATED', 'CANCELLED',
    name='inventorystatus', create_type=False
)
lotstatus_enum = postgresql.ENUM(
    'AVAILABLE', 'RESERVED', 'BLOCKED', 'EXPIRED',
    name='lotstatus', create_type=False
)
valuationmethod_enum = postgresql.ENUM(
    'FIFO', 'LIFO', 'AVG', 'STANDARD',
    name='valuationmethod', create_type=False
)

# --- Products ---
producttype_enum = postgresql.ENUM(
    'STOCKABLE', 'CONSUMABLE', 'SERVICE',
    name='producttype', create_type=False
)
productstatus_enum = postgresql.ENUM(
    'DRAFT', 'ACTIVE', 'DISCONTINUED', 'BLOCKED',
    name='productstatus', create_type=False
)

# --- Assets & Maintenance ---
assetcategory_enum = postgresql.ENUM(
    'MACHINE', 'EQUIPMENT', 'VEHICLE', 'BUILDING', 'INFRASTRUCTURE', 'IT_EQUIPMENT', 'TOOL', 'UTILITY', 'FURNITURE', 'OTHER',
    name='assetcategory', create_type=False
)
assetstatus_enum = postgresql.ENUM(
    'ACTIVE', 'INACTIVE', 'IN_MAINTENANCE', 'RESERVED', 'DISPOSED', 'UNDER_REPAIR', 'STANDBY',
    name='assetstatus', create_type=False
)
assetcriticality_enum = postgresql.ENUM(
    'CRITICAL', 'HIGH', 'MEDIUM', 'LOW',
    name='assetcriticality', create_type=False
)
contracttype_enum = postgresql.ENUM(
    'FULL_SERVICE', 'PREVENTIVE', 'ON_CALL', 'PARTS_ONLY', 'LABOR_ONLY', 'WARRANTY',
    name='contracttype', create_type=False
)
contractstatus_enum = postgresql.ENUM(
    'DRAFT', 'ACTIVE', 'SUSPENDED', 'EXPIRED', 'TERMINATED',
    name='contractstatus', create_type=False
)
maintenancetype_enum = postgresql.ENUM(
    'PREVENTIVE', 'CORRECTIVE', 'PREDICTIVE', 'CONDITION_BASED', 'BREAKDOWN', 'IMPROVEMENT', 'INSPECTION', 'CALIBRATION',
    name='maintenancetype', create_type=False
)
maintenanceworkorderstatus_enum = postgresql.ENUM(
    'DRAFT', 'REQUESTED', 'APPROVED', 'PLANNED', 'ASSIGNED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'VERIFIED', 'CLOSED', 'CANCELLED',
    name='maintenanceworkorderstatus', create_type=False
)
workorderpriority_enum = postgresql.ENUM(
    'EMERGENCY', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SCHEDULED',
    name='workorderpriority', create_type=False
)
partrequeststatus_enum = postgresql.ENUM(
    'REQUESTED', 'APPROVED', 'ORDERED', 'RECEIVED', 'ISSUED', 'CANCELLED',
    name='partrequeststatus', create_type=False
)
failuretype_enum = postgresql.ENUM(
    'MECHANICAL', 'ELECTRICAL', 'ELECTRONIC', 'HYDRAULIC', 'PNEUMATIC', 'SOFTWARE', 'OPERATOR_ERROR', 'WEAR', 'CONTAMINATION', 'UNKNOWN',
    name='failuretype', create_type=False
)
scrapreason_enum = postgresql.ENUM(
    'DEFECT', 'DAMAGE', 'QUALITY', 'EXPIRED', 'OTHER',
    name='scrapreason', create_type=False
)

# --- Manufacturing (MRP) ---
bomtype_enum = postgresql.ENUM(
    'MANUFACTURING', 'KIT', 'PHANTOM', 'SUBCONTRACT',
    name='bomtype', create_type=False
)
bomstatus_enum = postgresql.ENUM(
    'DRAFT', 'ACTIVE', 'OBSOLETE',
    name='bomstatus', create_type=False
)
workcentertype_enum = postgresql.ENUM(
    'MACHINE', 'ASSEMBLY', 'MANUAL', 'QUALITY', 'PACKAGING', 'OUTSOURCED',
    name='workcentertype', create_type=False
)
workcenterstatus_enum = postgresql.ENUM(
    'AVAILABLE', 'BUSY', 'MAINTENANCE', 'OFFLINE',
    name='workcenterstatus', create_type=False
)
operationtype_enum = postgresql.ENUM(
    'SETUP', 'PRODUCTION', 'QUALITY_CHECK', 'CLEANING', 'PACKAGING', 'TRANSPORT',
    name='operationtype', create_type=False
)
consumptiontype_enum = postgresql.ENUM(
    'MANUAL', 'AUTO_ON_START', 'AUTO_ON_COMPLETE',
    name='consumptiontype', create_type=False
)
mostatus_enum = postgresql.ENUM(
    'DRAFT', 'CONFIRMED', 'PLANNED', 'IN_PROGRESS', 'DONE', 'CANCELLED',
    name='mostatus', create_type=False
)
mopriority_enum = postgresql.ENUM(
    'LOW', 'NORMAL', 'HIGH', 'URGENT',
    name='mopriority', create_type=False
)
prodworkorderstatus_enum = postgresql.ENUM(
    'PENDING', 'READY', 'IN_PROGRESS', 'PAUSED', 'DONE', 'CANCELLED',
    name='prodworkorderstatus', create_type=False
)

# --- QC Module (Quality Control for modules) ---
qctesttype_enum = postgresql.ENUM(
    'UNIT', 'INTEGRATION', 'E2E', 'PERFORMANCE', 'SECURITY', 'REGRESSION',
    name='qctesttype', create_type=False
)
qccheckstatus_enum = postgresql.ENUM(
    'PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR',
    name='qccheckstatus', create_type=False
)
qcrulecategory_enum = postgresql.ENUM(
    'ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'CODE_QUALITY', 'TESTING', 'DOCUMENTATION', 'API', 'DATABASE', 'INTEGRATION', 'COMPLIANCE',
    name='qcrulecategory', create_type=False
)
qcruleseverity_enum = postgresql.ENUM(
    'INFO', 'WARNING', 'CRITICAL', 'BLOCKER',
    name='qcruleseverity', create_type=False
)
validationphase_enum = postgresql.ENUM(
    'PRE_QC', 'AUTOMATED', 'MANUAL', 'FINAL', 'POST_DEPLOY',
    name='validationphase', create_type=False
)
qcmodulestatus_enum = postgresql.ENUM(
    'DRAFT', 'IN_DEVELOPMENT', 'READY_FOR_QC', 'QC_IN_PROGRESS', 'QC_PASSED', 'QC_FAILED', 'PRODUCTION', 'DEPRECATED',
    name='qcmodulestatus', create_type=False
)


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('accounting_dashboard_metrics',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('metric_date', sa.Date(), nullable=False),
    sa.Column('metric_type', sa.String(length=50), nullable=False),
    sa.Column('cash_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('cash_balance_updated_at', sa.DateTime(), nullable=True),
    sa.Column('invoices_to_pay_count', sa.Integer(), nullable=True),
    sa.Column('invoices_to_pay_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('invoices_overdue_count', sa.Integer(), nullable=True),
    sa.Column('invoices_overdue_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('invoices_to_collect_count', sa.Integer(), nullable=True),
    sa.Column('invoices_to_collect_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('invoices_overdue_collect_count', sa.Integer(), nullable=True),
    sa.Column('invoices_overdue_collect_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('revenue_period', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('expenses_period', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('result_period', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('documents_pending_count', sa.Integer(), nullable=True),
    sa.Column('documents_error_count', sa.Integer(), nullable=True),
    sa.Column('transactions_unreconciled', sa.Integer(), nullable=True),
    sa.Column('data_freshness_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('last_bank_sync', sa.DateTime(), nullable=True),
    sa.Column('calculated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'metric_date', 'metric_type', name='uq_dashmetrics_date_type')
    )
bind = op.get_bind()
inspector = inspect(bind)

# ============================================================
# accounting_bank_connections
# ============================================================
if not inspector.has_table("accounting_bank_connections"):
    op.create_table(
        'accounting_bank_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('institution_id', sa.String(length=100), nullable=False),
        sa.Column('institution_name', sa.String(length=255), nullable=False),
        sa.Column('institution_logo_url', sa.String(length=500), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('connection_id', sa.String(length=255), nullable=False),
        sa.Column('status', bankconnectionstatus_enum, nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('consent_expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_consent_renewed_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.Column('linked_accounts', postgresql.JSONB(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'tenant_id',
            'provider',
            'connection_id',
            name='uq_bankconn_provider'
        )
    )

    op.create_index(
        'idx_bankconn_tenant',
        'accounting_bank_connections',
        ['tenant_id'],
        unique=False
    )

    op.create_index(
        'idx_bankconn_tenant_status',
        'accounting_bank_connections',
        ['tenant_id', 'status'],
        unique=False
    )

# ============================================================
# accounting_dashboard_metrics
# ============================================================
if not inspector.has_table("accounting_dashboard_metrics"):
    op.create_table(
        'accounting_dashboard_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('cash_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('cash_balance_updated_at', sa.DateTime(), nullable=True),
        sa.Column('invoices_to_pay_count', sa.Integer(), nullable=True),
        sa.Column('invoices_to_pay_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('invoices_overdue_count', sa.Integer(), nullable=True),
        sa.Column('invoices_overdue_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('invoices_to_collect_count', sa.Integer(), nullable=True),
        sa.Column('invoices_to_collect_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('invoices_overdue_collect_count', sa.Integer(), nullable=True),
        sa.Column('invoices_overdue_collect_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('revenue_period', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('expenses_period', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('result_period', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('documents_pending_count', sa.Integer(), nullable=True),
        sa.Column('documents_error_count', sa.Integer(), nullable=True),
        sa.Column('transactions_unreconciled', sa.Integer(), nullable=True),
        sa.Column('data_freshness_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('last_bank_sync', sa.DateTime(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'tenant_id',
            'metric_date',
            'metric_type',
            name='uq_dashmetrics_date_type'
        )
    )
    op.create_index('idx_dashmetrics_date', 'accounting_dashboard_metrics', ['tenant_id', 'metric_date'], unique=False)
    op.create_index('idx_dashmetrics_tenant', 'accounting_dashboard_metrics', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_dashboard_metrics_tenant_id'), 'accounting_dashboard_metrics', ['tenant_id'], unique=False)
    op.create_table('accounting_email_inboxes',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('email_address', sa.String(length=255), nullable=False),
    sa.Column('email_type', emailinboxtype_enum, nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('auto_process', sa.Boolean(), nullable=True),
    sa.Column('provider', sa.String(length=50), nullable=True),
    sa.Column('provider_config', postgresql.JSON(), nullable=True),
    sa.Column('emails_received', sa.Integer(), nullable=True),
    sa.Column('emails_processed', sa.Integer(), nullable=True),
    sa.Column('last_email_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email_address')
    )
    op.create_index('idx_emailinbox_tenant', 'accounting_email_inboxes', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_email_inboxes_tenant_id'), 'accounting_email_inboxes', ['tenant_id'], unique=False)
    op.create_table('accounting_reconciliation_rules',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('match_criteria', postgresql.JSON(), nullable=False),
    sa.Column('auto_reconcile', sa.Boolean(), nullable=True),
    sa.Column('min_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('default_account_code', sa.String(length=20), nullable=True),
    sa.Column('default_tax_code', sa.String(length=20), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('times_matched', sa.Integer(), nullable=True),
    sa.Column('last_matched_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reconrule_tenant', 'accounting_reconciliation_rules', ['tenant_id'], unique=False)
    op.create_index('idx_reconrule_tenant_active', 'accounting_reconciliation_rules', ['tenant_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_accounting_reconciliation_rules_tenant_id'), 'accounting_reconciliation_rules', ['tenant_id'], unique=False)
    op.create_table('accounting_tax_configurations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=True),
    sa.Column('country_code', sa.String(length=2), nullable=False),
    sa.Column('country_name', sa.String(length=100), nullable=False),
    sa.Column('tax_type', sa.String(length=50), nullable=False),
    sa.Column('tax_rates', postgresql.JSON(), nullable=False),
    sa.Column('special_rules', postgresql.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_taxconfig_country', 'accounting_tax_configurations', ['country_code'], unique=False)
    op.create_index('idx_taxconfig_tenant', 'accounting_tax_configurations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_tax_configurations_tenant_id'), 'accounting_tax_configurations', ['tenant_id'], unique=False)
    op.create_table('accounting_universal_chart',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('universal_code', sa.String(length=20), nullable=False),
    sa.Column('name_en', sa.String(length=255), nullable=False),
    sa.Column('name_fr', sa.String(length=255), nullable=False),
    sa.Column('account_type', sa.String(length=20), nullable=False),
    sa.Column('parent_code', sa.String(length=20), nullable=True),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('country_mappings', postgresql.JSON(), nullable=True),
    sa.Column('ai_keywords', postgresql.JSON(), nullable=True),
    sa.Column('ai_patterns', postgresql.JSON(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['parent_code'], ['accounting_universal_chart.universal_code'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('universal_code')
    )
    op.create_index('idx_univchart_code', 'accounting_universal_chart', ['universal_code'], unique=False)
    op.create_index('idx_univchart_parent', 'accounting_universal_chart', ['parent_code'], unique=False)
    op.create_index('idx_univchart_type', 'accounting_universal_chart', ['account_type'], unique=False)
    op.create_table('accounting_user_preferences',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('view_type', viewtype_enum, nullable=False),
    sa.Column('dashboard_widgets', postgresql.JSON(), nullable=True),
    sa.Column('default_period', sa.String(length=20), nullable=True),
    sa.Column('list_columns', postgresql.JSON(), nullable=True),
    sa.Column('default_sort', postgresql.JSON(), nullable=True),
    sa.Column('default_filters', postgresql.JSON(), nullable=True),
    sa.Column('alert_preferences', postgresql.JSON(), nullable=True),
    sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'user_id', 'view_type', name='uq_userprefs_view')
    )
    op.create_index(op.f('ix_accounting_user_preferences_tenant_id'), 'accounting_user_preferences', ['tenant_id'], unique=False)
    op.create_table('accounts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', accounttype_enum, nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_auxiliary', sa.Boolean(), nullable=True),
    sa.Column('auxiliary_type', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_reconcilable', sa.Boolean(), nullable=True),
    sa.Column('allow_posting', sa.Boolean(), nullable=True),
    sa.Column('balance_debit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('balance_credit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_accounts_tenant_code', 'accounts', ['tenant_id', 'code'], unique=True)
    op.create_index(op.f('ix_accounts_tenant_id'), 'accounts', ['tenant_id'], unique=False)
    op.create_index('ix_accounts_tenant_parent', 'accounts', ['tenant_id', 'parent_id'], unique=False)
    op.create_index('ix_accounts_tenant_type', 'accounts', ['tenant_id', 'type'], unique=False)
    op.create_table('cash_forecasts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('period', forecastperiod_enum, nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('opening_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('expected_receipts', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_receipts', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('expected_payments', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_payments', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('expected_closing', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_closing', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('details', postgresql.JSON(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cash_forecasts_tenant_id'), 'cash_forecasts', ['tenant_id'], unique=False)
    op.create_index('ix_forecasts_tenant_date', 'cash_forecasts', ['tenant_id', 'period', 'date'], unique=True)
    op.create_table('compliance_policies',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', compliancedocumenttype_enum, nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('version', sa.String(length=20), nullable=True),
    sa.Column('version_date', sa.Date(), nullable=True),
    sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('effective_date', sa.Date(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('next_review_date', sa.Date(), nullable=True),
    sa.Column('last_reviewed_date', sa.Date(), nullable=True),
    sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=True),
    sa.Column('requires_acknowledgment', sa.Boolean(), nullable=True),
    sa.Column('target_audience', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('file_path', sa.Text(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', 'version', name='uq_policy_version')
    )
    op.create_index(op.f('ix_compliance_policies_tenant_id'), 'compliance_policies', ['tenant_id'], unique=False)
    op.create_index('ix_policy_tenant_active', 'compliance_policies', ['tenant_id', 'is_active'], unique=False)
    op.create_table('compliance_regulations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', regulationtype_enum, nullable=False),
    sa.Column('version', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('scope', sa.Text(), nullable=True),
    sa.Column('authority', sa.String(length=200), nullable=True),
    sa.Column('effective_date', sa.Date(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('next_review_date', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_mandatory', sa.Boolean(), nullable=True),
    sa.Column('external_reference', sa.String(length=200), nullable=True),
    sa.Column('source_url', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='uq_regulation_tenant_code')
    )
    op.create_index(op.f('ix_compliance_regulations_tenant_id'), 'compliance_regulations', ['tenant_id'], unique=False)
    op.create_index('ix_regulation_tenant_type', 'compliance_regulations', ['tenant_id', 'type'], unique=False)
    op.create_table('compliance_reports',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', reporttype_enum, nullable=False),
    sa.Column('period_start', sa.Date(), nullable=True),
    sa.Column('period_end', sa.Date(), nullable=True),
    sa.Column('regulation_ids', sa.JSON(), nullable=True),
    sa.Column('department_ids', sa.JSON(), nullable=True),
    sa.Column('executive_summary', sa.Text(), nullable=True),
    sa.Column('content', sa.JSON(), nullable=True),
    sa.Column('metrics', sa.JSON(), nullable=True),
    sa.Column('file_path', sa.Text(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=True),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.Column('recipients', sa.JSON(), nullable=True),
    sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='uq_report_number')
    )
    op.create_index(op.f('ix_compliance_reports_tenant_id'), 'compliance_reports', ['tenant_id'], unique=False)
    op.create_index('ix_report_tenant_type', 'compliance_reports', ['tenant_id', 'type'], unique=False)
    op.create_table('core_audit_journal',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('action', sa.String(length=255), nullable=False),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_core_audit_created_at', 'core_audit_journal', ['created_at'], unique=False)
    op.create_index('idx_core_audit_tenant_id', 'core_audit_journal', ['tenant_id'], unique=False)
    op.create_index('idx_core_audit_tenant_user', 'core_audit_journal', ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_core_audit_user_id', 'core_audit_journal', ['user_id'], unique=False)
    op.create_index(op.f('ix_core_audit_journal_id'), 'core_audit_journal', ['id'], unique=False)
    op.create_index(op.f('ix_core_audit_journal_tenant_id'), 'core_audit_journal', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_core_audit_journal_user_id'), 'core_audit_journal', ['user_id'], unique=False)
    op.create_table('decisions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('entity_type', sa.String(length=255), nullable=False),
    sa.Column('entity_id', sa.String(length=255), nullable=False),
    sa.Column('level', decisionlevel_enum, nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('decision_reason', sa.Text(), nullable=True),
    sa.Column('is_fully_validated', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_decisions_entity', 'decisions', ['tenant_id', 'entity_type', 'entity_id'], unique=False)
    op.create_index('idx_decisions_level', 'decisions', ['level'], unique=False)
    op.create_index('idx_decisions_tenant_id', 'decisions', ['tenant_id'], unique=False)
    op.create_index('idx_decisions_validated', 'decisions', ['level', 'is_fully_validated'], unique=False)
    op.create_index(op.f('ix_decisions_id'), 'decisions', ['id'], unique=False)
    op.create_index(op.f('ix_decisions_tenant_id'), 'decisions', ['tenant_id'], unique=False)
    op.create_table('fiscal_years',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('status', fiscalyearstatus_enum, nullable=True),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('closed_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('total_debit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('total_credit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('result', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('end_date > start_date', name='check_fiscal_year_dates'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fiscal_years_tenant_code', 'fiscal_years', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_fiscal_years_tenant_dates', 'fiscal_years', ['tenant_id', 'start_date', 'end_date'], unique=False)
    op.create_index(op.f('ix_fiscal_years_tenant_id'), 'fiscal_years', ['tenant_id'], unique=False)
    op.create_table('inventory_categories',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('default_valuation', valuationmethod_enum, nullable=True),
    sa.Column('default_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['inventory_categories.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='unique_category_code')
    )
    op.create_index('idx_categories_parent', 'inventory_categories', ['tenant_id', 'parent_id'], unique=False)
    op.create_index('idx_categories_tenant', 'inventory_categories', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_categories_tenant_id'), 'inventory_categories', ['tenant_id'], unique=False)
    op.create_table('inventory_warehouses',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', warehousetype_enum, nullable=True),
    sa.Column('address_line1', sa.String(length=255), nullable=True),
    sa.Column('address_line2', sa.String(length=255), nullable=True),
    sa.Column('postal_code', sa.String(length=20), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('manager_name', sa.String(length=200), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('allow_negative', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='unique_warehouse_code')
    )
    op.create_index('idx_warehouses_tenant', 'inventory_warehouses', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_warehouses_tenant_id'), 'inventory_warehouses', ['tenant_id'], unique=False)
    op.create_table('items',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_items_tenant_created', 'items', ['tenant_id', 'created_at'], unique=False)
    op.create_index('idx_items_tenant_id', 'items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_index(op.f('ix_items_tenant_id'), 'items', ['tenant_id'], unique=False)
    op.create_table('maintenance_assets',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('asset_code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', assetcategory_enum, nullable=False),
    sa.Column('asset_type', sa.String(length=100), nullable=True),
    sa.Column('status', assetstatus_enum, nullable=True),
    sa.Column('criticality', assetcriticality_enum, nullable=True),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_description', sa.String(length=200), nullable=True),
    sa.Column('building', sa.String(length=100), nullable=True),
    sa.Column('floor', sa.String(length=50), nullable=True),
    sa.Column('area', sa.String(length=100), nullable=True),
    sa.Column('manufacturer', sa.String(length=200), nullable=True),
    sa.Column('model', sa.String(length=200), nullable=True),
    sa.Column('serial_number', sa.String(length=100), nullable=True),
    sa.Column('year_manufactured', sa.Integer(), nullable=True),
    sa.Column('purchase_date', sa.Date(), nullable=True),
    sa.Column('installation_date', sa.Date(), nullable=True),
    sa.Column('warranty_start_date', sa.Date(), nullable=True),
    sa.Column('warranty_end_date', sa.Date(), nullable=True),
    sa.Column('expected_end_of_life', sa.Date(), nullable=True),
    sa.Column('last_maintenance_date', sa.Date(), nullable=True),
    sa.Column('next_maintenance_date', sa.Date(), nullable=True),
    sa.Column('purchase_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('current_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('replacement_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('salvage_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('depreciation_method', sa.String(length=50), nullable=True),
    sa.Column('useful_life_years', sa.Integer(), nullable=True),
    sa.Column('depreciation_rate', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('specifications', postgresql.JSONB(), nullable=True),
    sa.Column('power_rating', sa.String(length=100), nullable=True),
    sa.Column('dimensions', sa.String(length=200), nullable=True),
    sa.Column('weight', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('weight_unit', sa.String(length=20), nullable=True),
    sa.Column('operating_hours', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('cycle_count', sa.Integer(), nullable=True),
    sa.Column('energy_consumption', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('maintenance_strategy', sa.String(length=50), nullable=True),
    sa.Column('default_maintenance_plan_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('contract_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('photo_url', sa.String(length=500), nullable=True),
    sa.Column('documents', postgresql.JSONB(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('barcode', sa.String(length=100), nullable=True),
    sa.Column('qr_code', sa.String(length=200), nullable=True),
    sa.Column('mtbf_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('mttr_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('availability_rate', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['maintenance_assets.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'asset_code', name='uq_asset_code')
    )
    op.create_index('idx_asset_category', 'maintenance_assets', ['tenant_id', 'category'], unique=False)
    op.create_index('idx_asset_code', 'maintenance_assets', ['tenant_id', 'asset_code'], unique=False)
    op.create_index('idx_asset_location', 'maintenance_assets', ['tenant_id', 'location_id'], unique=False)
    op.create_index('idx_asset_status', 'maintenance_assets', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_asset_tenant', 'maintenance_assets', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_assets_tenant_id'), 'maintenance_assets', ['tenant_id'], unique=False)
    op.create_table('maintenance_contracts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('contract_code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('contract_type', contracttype_enum, nullable=False),
    sa.Column('status', contractstatus_enum, nullable=True),
    sa.Column('vendor_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('vendor_contact', sa.String(length=200), nullable=True),
    sa.Column('vendor_phone', sa.String(length=50), nullable=True),
    sa.Column('vendor_email', sa.String(length=200), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('renewal_date', sa.Date(), nullable=True),
    sa.Column('notice_period_days', sa.Integer(), nullable=True),
    sa.Column('auto_renewal', sa.Boolean(), nullable=True),
    sa.Column('renewal_terms', sa.Text(), nullable=True),
    sa.Column('covered_assets', postgresql.JSONB(), nullable=True),
    sa.Column('coverage_description', sa.Text(), nullable=True),
    sa.Column('exclusions', sa.Text(), nullable=True),
    sa.Column('response_time_hours', sa.Integer(), nullable=True),
    sa.Column('resolution_time_hours', sa.Integer(), nullable=True),
    sa.Column('availability_guarantee', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('contract_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('annual_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('payment_frequency', sa.String(length=50), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('includes_parts', sa.Boolean(), nullable=True),
    sa.Column('includes_labor', sa.Boolean(), nullable=True),
    sa.Column('includes_travel', sa.Boolean(), nullable=True),
    sa.Column('max_interventions', sa.Integer(), nullable=True),
    sa.Column('interventions_used', sa.Integer(), nullable=True),
    sa.Column('contract_file', sa.String(length=500), nullable=True),
    sa.Column('documents', postgresql.JSONB(), nullable=True),
    sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mcontract_code', 'maintenance_contracts', ['tenant_id', 'contract_code'], unique=False)
    op.create_index('idx_mcontract_tenant', 'maintenance_contracts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_contracts_tenant_id'), 'maintenance_contracts', ['tenant_id'], unique=False)
    op.create_table('production_plans',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('planning_horizon_days', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('planning_method', sa.String(length=50), nullable=True),
    sa.Column('total_orders', sa.Integer(), nullable=True),
    sa.Column('total_quantity', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('total_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('generated_at', sa.DateTime(), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='unique_plan_code')
    )
    op.create_index('idx_plan_dates', 'production_plans', ['tenant_id', 'start_date', 'end_date'], unique=False)
    op.create_index('idx_plan_tenant', 'production_plans', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_production_plans_tenant_id'), 'production_plans', ['tenant_id'], unique=False)
    op.create_table('production_routings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('version', sa.String(length=20), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', bomstatus_enum, nullable=True),
    sa.Column('total_setup_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total_operation_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total_labor_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('total_machine_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', 'version', name='unique_routing_code_version')
    )
    op.create_index('idx_routing_product', 'production_routings', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_routing_tenant', 'production_routings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_production_routings_tenant_id'), 'production_routings', ['tenant_id'], unique=False)
    op.create_table('production_work_centers',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', workcentertype_enum, nullable=True),
    sa.Column('status', workcenterstatus_enum, nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location', sa.String(length=100), nullable=True),
    sa.Column('capacity', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('efficiency', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('oee_target', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('time_start', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('time_stop', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('time_before', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('time_after', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('cost_per_hour', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('cost_per_cycle', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('working_hours_per_day', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('working_days_per_week', sa.Integer(), nullable=True),
    sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('operator_ids', postgresql.JSONB(), nullable=True),
    sa.Column('requires_approval', sa.Boolean(), nullable=True),
    sa.Column('allow_parallel', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='unique_workcenter_code')
    )
    op.create_index('idx_wc_status', 'production_work_centers', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_wc_tenant', 'production_work_centers', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_production_work_centers_tenant_id'), 'production_work_centers', ['tenant_id'], unique=False)
    op.create_table('red_decision_reports',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('decision_reason', sa.Text(), nullable=False),
    sa.Column('trigger_data', sa.Text(), nullable=False),
    sa.Column('validated_at', sa.DateTime(), nullable=False),
    sa.Column('validator_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('journal_references', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_report_decision', 'red_decision_reports', ['decision_id'], unique=False)
    op.create_index('idx_report_tenant', 'red_decision_reports', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_red_decision_reports_decision_id'), 'red_decision_reports', ['decision_id'], unique=True)
    op.create_index(op.f('ix_red_decision_reports_id'), 'red_decision_reports', ['id'], unique=False)
    op.create_index(op.f('ix_red_decision_reports_tenant_id'), 'red_decision_reports', ['tenant_id'], unique=False)
    op.create_table('red_decision_workflows',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('step', redworkflowstep_enum, nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_red_workflow_decision', 'red_decision_workflows', ['decision_id'], unique=False)
    op.create_index('idx_red_workflow_decision_step', 'red_decision_workflows', ['decision_id', 'step'], unique=False)
    op.create_index('idx_red_workflow_tenant', 'red_decision_workflows', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_red_decision_workflows_decision_id'), 'red_decision_workflows', ['decision_id'], unique=False)
    op.create_index(op.f('ix_red_decision_workflows_id'), 'red_decision_workflows', ['id'], unique=False)
    op.create_index(op.f('ix_red_decision_workflows_tenant_id'), 'red_decision_workflows', ['tenant_id'], unique=False)
    op.create_table('tenant_events',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('event_data', postgresql.JSON(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('actor_email', sa.String(length=255), nullable=True),
    sa.Column('actor_ip', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_events_event_type'), 'tenant_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_tenant_events_id'), 'tenant_events', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_events_tenant_id'), 'tenant_events', ['tenant_id'], unique=False)
    op.create_table('tenant_invitations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=True),
    sa.Column('tenant_name', sa.String(length=255), nullable=True),
    sa.Column('plan', subscriptionplan_enum, nullable=True),
    sa.Column('proposed_role', sa.String(length=50), nullable=True),
    sa.Column('status', invitationstatus_enum, nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('accepted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_tenant_invitations_email'), 'tenant_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_tenant_invitations_id'), 'tenant_invitations', ['id'], unique=False)
    op.create_table('tenant_modules',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('module_code', sa.String(length=10), nullable=False),
    sa.Column('module_name', sa.String(length=100), nullable=True),
    sa.Column('module_version', sa.String(length=20), nullable=True),
    sa.Column('status', tenantmodulestatus_enum, nullable=True),
    sa.Column('config', postgresql.JSON(), nullable=True),
    sa.Column('limits', postgresql.JSON(), nullable=True),
    sa.Column('activated_at', sa.DateTime(), nullable=True),
    sa.Column('deactivated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_modules_id'), 'tenant_modules', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_modules_tenant_id'), 'tenant_modules', ['tenant_id'], unique=False)
    op.create_table('tenant_onboarding',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('company_info_completed', sa.Boolean(), nullable=True),
    sa.Column('admin_created', sa.Boolean(), nullable=True),
    sa.Column('users_invited', sa.Boolean(), nullable=True),
    sa.Column('modules_configured', sa.Boolean(), nullable=True),
    sa.Column('country_pack_selected', sa.Boolean(), nullable=True),
    sa.Column('first_data_imported', sa.Boolean(), nullable=True),
    sa.Column('training_completed', sa.Boolean(), nullable=True),
    sa.Column('progress_percent', sa.Integer(), nullable=True),
    sa.Column('current_step', sa.String(length=50), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_onboarding_id'), 'tenant_onboarding', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_onboarding_tenant_id'), 'tenant_onboarding', ['tenant_id'], unique=True)
    op.create_table('tenant_settings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('two_factor_required', sa.Boolean(), nullable=True),
    sa.Column('session_timeout_minutes', sa.Integer(), nullable=True),
    sa.Column('password_expiry_days', sa.Integer(), nullable=True),
    sa.Column('ip_whitelist', postgresql.JSON(), nullable=True),
    sa.Column('notify_admin_on_signup', sa.Boolean(), nullable=True),
    sa.Column('notify_admin_on_error', sa.Boolean(), nullable=True),
    sa.Column('daily_digest_enabled', sa.Boolean(), nullable=True),
    sa.Column('webhook_url', sa.String(length=500), nullable=True),
    sa.Column('api_rate_limit', sa.Integer(), nullable=True),
    sa.Column('auto_backup_enabled', sa.Boolean(), nullable=True),
    sa.Column('backup_retention_days', sa.Integer(), nullable=True),
    sa.Column('custom_settings', postgresql.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_settings_id'), 'tenant_settings', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_settings_tenant_id'), 'tenant_settings', ['tenant_id'], unique=True)
    op.create_table('tenant_subscriptions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('plan', subscriptionplan_enum, nullable=False),
    sa.Column('billing_cycle', billingcycle_enum, nullable=True),
    sa.Column('price_monthly', sa.Float(), nullable=True),
    sa.Column('price_yearly', sa.Float(), nullable=True),
    sa.Column('discount_percent', sa.Float(), nullable=True),
    sa.Column('starts_at', sa.DateTime(), nullable=False),
    sa.Column('ends_at', sa.DateTime(), nullable=True),
    sa.Column('next_billing_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_trial', sa.Boolean(), nullable=True),
    sa.Column('auto_renew', sa.Boolean(), nullable=True),
    sa.Column('payment_method', sa.String(length=50), nullable=True),
    sa.Column('last_payment_at', sa.DateTime(), nullable=True),
    sa.Column('last_payment_amount', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_subscriptions_id'), 'tenant_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_subscriptions_tenant_id'), 'tenant_subscriptions', ['tenant_id'], unique=False)
    op.create_table('tenant_usage',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('period', sa.String(length=20), nullable=True),
    sa.Column('active_users', sa.Integer(), nullable=True),
    sa.Column('total_users', sa.Integer(), nullable=True),
    sa.Column('new_users', sa.Integer(), nullable=True),
    sa.Column('storage_used_gb', sa.Float(), nullable=True),
    sa.Column('files_count', sa.Integer(), nullable=True),
    sa.Column('api_calls', sa.Integer(), nullable=True),
    sa.Column('api_errors', sa.Integer(), nullable=True),
    sa.Column('module_usage', postgresql.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_usage_date'), 'tenant_usage', ['date'], unique=False)
    op.create_index(op.f('ix_tenant_usage_id'), 'tenant_usage', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_usage_tenant_id'), 'tenant_usage', ['tenant_id'], unique=False)
    op.create_table('tenants',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('legal_name', sa.String(length=255), nullable=True),
    sa.Column('siret', sa.String(length=20), nullable=True),
    sa.Column('vat_number', sa.String(length=30), nullable=True),
    sa.Column('address_line1', sa.String(length=255), nullable=True),
    sa.Column('address_line2', sa.String(length=255), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('postal_code', sa.String(length=20), nullable=True),
    sa.Column('country', sa.String(length=2), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('website', sa.String(length=255), nullable=True),
    sa.Column('status', tenantstatus_enum, nullable=True),
    sa.Column('plan', subscriptionplan_enum, nullable=True),
    sa.Column('environment', tenantenvironment_enum, nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=True),
    sa.Column('language', sa.String(length=5), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('date_format', sa.String(length=20), nullable=True),
    sa.Column('max_users', sa.Integer(), nullable=True),
    sa.Column('max_storage_gb', sa.Integer(), nullable=True),
    sa.Column('storage_used_gb', sa.Float(), nullable=True),
    sa.Column('logo_url', sa.String(length=500), nullable=True),
    sa.Column('primary_color', sa.String(length=7), nullable=True),
    sa.Column('secondary_color', sa.String(length=7), nullable=True),
    sa.Column('features', postgresql.JSON(), nullable=True),
    sa.Column('extra_data', postgresql.JSON(), nullable=True),
    sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
    sa.Column('activated_at', sa.DateTime(), nullable=True),
    sa.Column('suspended_at', sa.DateTime(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)
    op.create_index(op.f('ix_tenants_tenant_id'), 'tenants', ['tenant_id'], unique=True)
    op.create_table('treasury_forecasts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('opening_balance', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('inflows', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('outflows', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('forecast_balance', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('red_triggered', sa.String(length=1), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_treasury_created', 'treasury_forecasts', ['created_at'], unique=False)
    op.create_index('idx_treasury_red', 'treasury_forecasts', ['tenant_id', 'red_triggered'], unique=False)
    op.create_index('idx_treasury_tenant', 'treasury_forecasts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_treasury_forecasts_id'), 'treasury_forecasts', ['id'], unique=False)
    op.create_index(op.f('ix_treasury_forecasts_tenant_id'), 'treasury_forecasts', ['tenant_id'], unique=False)
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', userrole_enum, nullable=False),
    sa.Column('is_active', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('totp_secret', sa.String(length=32), nullable=True),
    sa.Column('totp_enabled', sa.Integer(), nullable=False),
    sa.Column('totp_verified_at', sa.DateTime(), nullable=True),
    sa.Column('backup_codes', sa.Text(), nullable=True),
    sa.Column('must_change_password', sa.Integer(), nullable=False),
    sa.Column('password_changed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=False)
    op.create_index('idx_users_tenant_email', 'users', ['tenant_id', 'email'], unique=False)
    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_table('accounting_bank_sync_sessions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sync_type', synctype_enum, nullable=False),
    sa.Column('triggered_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', syncstatus_enum, nullable=False),
    sa.Column('sync_from_date', sa.Date(), nullable=True),
    sa.Column('sync_to_date', sa.Date(), nullable=True),
    sa.Column('accounts_synced', sa.Integer(), nullable=True),
    sa.Column('transactions_fetched', sa.Integer(), nullable=True),
    sa.Column('transactions_new', sa.Integer(), nullable=True),
    sa.Column('transactions_updated', sa.Integer(), nullable=True),
    sa.Column('reconciliations_auto', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_details', postgresql.JSON(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['connection_id'], ['accounting_bank_connections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_banksync_connection', 'accounting_bank_sync_sessions', ['connection_id'], unique=False)
    op.create_index('idx_banksync_status', 'accounting_bank_sync_sessions', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_banksync_tenant', 'accounting_bank_sync_sessions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_bank_sync_sessions_tenant_id'), 'accounting_bank_sync_sessions', ['tenant_id'], unique=False)
    op.create_table('accounting_chart_mappings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('universal_code', sa.String(length=20), nullable=False),
    sa.Column('local_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('local_account_code', sa.String(length=20), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('conditions', postgresql.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['local_account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['universal_code'], ['accounting_universal_chart.universal_code'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'universal_code', name='uq_chartmap_universal')
    )
    op.create_index('idx_chartmap_tenant', 'accounting_chart_mappings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_chart_mappings_tenant_id'), 'accounting_chart_mappings', ['tenant_id'], unique=False)
    op.create_table('accounting_email_processing_logs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('inbox_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email_id', sa.String(length=255), nullable=False),
    sa.Column('email_from', sa.String(length=255), nullable=True),
    sa.Column('email_subject', sa.String(length=500), nullable=True),
    sa.Column('email_received_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('attachments_count', sa.Integer(), nullable=True),
    sa.Column('attachments_processed', sa.Integer(), nullable=True),
    sa.Column('documents_created', postgresql.JSON(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['inbox_id'], ['accounting_email_inboxes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_emaillog_inbox', 'accounting_email_processing_logs', ['inbox_id'], unique=False)
    op.create_index('idx_emaillog_status', 'accounting_email_processing_logs', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_emaillog_tenant', 'accounting_email_processing_logs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_email_processing_logs_tenant_id'), 'accounting_email_processing_logs', ['tenant_id'], unique=False)
    op.create_table('cash_flow_categories',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_receipt', sa.Boolean(), nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.Column('default_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['default_account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['cash_flow_categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cash_categories_tenant_code', 'cash_flow_categories', ['tenant_id', 'code'], unique=True)
    op.create_index(op.f('ix_cash_flow_categories_tenant_id'), 'cash_flow_categories', ['tenant_id'], unique=False)
    op.create_table('compliance_assessments',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('assessment_type', sa.String(length=50), nullable=True),
    sa.Column('scope_description', sa.Text(), nullable=True),
    sa.Column('planned_date', sa.Date(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('status', assessmentstatus_enum, nullable=True),
    sa.Column('overall_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('overall_status', compliancestatus_enum, nullable=True),
    sa.Column('total_requirements', sa.Integer(), nullable=True),
    sa.Column('compliant_count', sa.Integer(), nullable=True),
    sa.Column('non_compliant_count', sa.Integer(), nullable=True),
    sa.Column('partial_count', sa.Integer(), nullable=True),
    sa.Column('findings_summary', sa.Text(), nullable=True),
    sa.Column('recommendations', sa.Text(), nullable=True),
    sa.Column('lead_assessor_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('assessor_ids', sa.JSON(), nullable=True),
    sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='uq_assessment_number')
    )
    op.create_index('ix_assessment_tenant_status', 'compliance_assessments', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_compliance_assessments_tenant_id'), 'compliance_assessments', ['tenant_id'], unique=False)
    op.create_table('compliance_audits',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('audit_type', sa.String(length=50), nullable=False),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('scope', sa.Text(), nullable=True),
    sa.Column('departments', sa.JSON(), nullable=True),
    sa.Column('planned_start', sa.Date(), nullable=True),
    sa.Column('planned_end', sa.Date(), nullable=True),
    sa.Column('actual_start', sa.Date(), nullable=True),
    sa.Column('actual_end', sa.Date(), nullable=True),
    sa.Column('lead_auditor_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('auditor_ids', sa.JSON(), nullable=True),
    sa.Column('auditee_ids', sa.JSON(), nullable=True),
    sa.Column('status', auditstatus_enum, nullable=True),
    sa.Column('total_findings', sa.Integer(), nullable=True),
    sa.Column('critical_findings', sa.Integer(), nullable=True),
    sa.Column('major_findings', sa.Integer(), nullable=True),
    sa.Column('minor_findings', sa.Integer(), nullable=True),
    sa.Column('observations', sa.Integer(), nullable=True),
    sa.Column('executive_summary', sa.Text(), nullable=True),
    sa.Column('conclusions', sa.Text(), nullable=True),
    sa.Column('recommendations', sa.Text(), nullable=True),
    sa.Column('report_file_path', sa.Text(), nullable=True),
    sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='uq_audit_number')
    )
    op.create_index('ix_audit_tenant_status', 'compliance_audits', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_compliance_audits_tenant_id'), 'compliance_audits', ['tenant_id'], unique=False)
    op.create_table('compliance_documents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', compliancedocumenttype_enum, nullable=False),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('version', sa.String(length=20), nullable=True),
    sa.Column('version_date', sa.Date(), nullable=True),
    sa.Column('effective_date', sa.Date(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('next_review_date', sa.Date(), nullable=True),
    sa.Column('file_path', sa.Text(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_controlled', sa.Boolean(), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=True),
    sa.Column('external_reference', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', 'version', name='uq_document_version')
    )
    op.create_index(op.f('ix_compliance_documents_tenant_id'), 'compliance_documents', ['tenant_id'], unique=False)
    op.create_index('ix_document_tenant_type', 'compliance_documents', ['tenant_id', 'type'], unique=False)
    op.create_table('compliance_incidents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('incident_type', sa.String(length=100), nullable=True),
    sa.Column('severity', incidentseverity_enum, nullable=True),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('incident_date', sa.DateTime(), nullable=False),
    sa.Column('reported_date', sa.DateTime(), nullable=True),
    sa.Column('resolved_date', sa.DateTime(), nullable=True),
    sa.Column('closed_date', sa.DateTime(), nullable=True),
    sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('status', incidentstatus_enum, nullable=True),
    sa.Column('investigation_notes', sa.Text(), nullable=True),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('impact_assessment', sa.Text(), nullable=True),
    sa.Column('resolution', sa.Text(), nullable=True),
    sa.Column('lessons_learned', sa.Text(), nullable=True),
    sa.Column('requires_disclosure', sa.Boolean(), nullable=True),
    sa.Column('disclosure_date', sa.Date(), nullable=True),
    sa.Column('disclosure_recipients', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='uq_incident_number')
    )
    op.create_index(op.f('ix_compliance_incidents_tenant_id'), 'compliance_incidents', ['tenant_id'], unique=False)
    op.create_index('ix_incident_tenant_status', 'compliance_incidents', ['tenant_id', 'status'], unique=False)
    op.create_table('compliance_policy_acknowledgments',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('is_valid', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['policy_id'], ['compliance_policies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('policy_id', 'user_id', name='uq_acknowledgment_user')
    )
    op.create_index('ix_acknowledgment_tenant_user', 'compliance_policy_acknowledgments', ['tenant_id', 'user_id'], unique=False)
    op.create_index(op.f('ix_compliance_policy_acknowledgments_tenant_id'), 'compliance_policy_acknowledgments', ['tenant_id'], unique=False)
    op.create_table('compliance_requirements',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('priority', requirementpriority_enum, nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('clause_reference', sa.String(length=100), nullable=True),
    sa.Column('compliance_status', compliancestatus_enum, nullable=True),
    sa.Column('current_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('target_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('control_frequency', sa.String(length=50), nullable=True),
    sa.Column('last_assessed', sa.DateTime(), nullable=True),
    sa.Column('next_assessment', sa.Date(), nullable=True),
    sa.Column('evidence_required', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_key_control', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['compliance_requirements.id'], ),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'regulation_id', 'code', name='uq_requirement_code')
    )
    op.create_index(op.f('ix_compliance_requirements_tenant_id'), 'compliance_requirements', ['tenant_id'], unique=False)
    op.create_index('ix_requirement_tenant_status', 'compliance_requirements', ['tenant_id', 'compliance_status'], unique=False)
    op.create_table('compliance_risks',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('likelihood', sa.Integer(), nullable=True),
    sa.Column('impact', sa.Integer(), nullable=True),
    sa.Column('risk_score', sa.Integer(), nullable=True),
    sa.Column('risk_level', risklevel_enum, nullable=True),
    sa.Column('residual_likelihood', sa.Integer(), nullable=True),
    sa.Column('residual_impact', sa.Integer(), nullable=True),
    sa.Column('residual_score', sa.Integer(), nullable=True),
    sa.Column('residual_level', risklevel_enum, nullable=True),
    sa.Column('treatment_strategy', sa.String(length=50), nullable=True),
    sa.Column('treatment_description', sa.Text(), nullable=True),
    sa.Column('current_controls', sa.Text(), nullable=True),
    sa.Column('planned_controls', sa.Text(), nullable=True),
    sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('identified_date', sa.Date(), nullable=True),
    sa.Column('last_review_date', sa.Date(), nullable=True),
    sa.Column('next_review_date', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_accepted', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='uq_risk_code')
    )
    op.create_index(op.f('ix_compliance_risks_tenant_id'), 'compliance_risks', ['tenant_id'], unique=False)
    op.create_index('ix_risk_tenant_level', 'compliance_risks', ['tenant_id', 'risk_level'], unique=False)
    op.create_table('compliance_trainings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('content_type', sa.String(length=50), nullable=True),
    sa.Column('duration_hours', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('passing_score', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_mandatory', sa.Boolean(), nullable=True),
    sa.Column('target_departments', sa.JSON(), nullable=True),
    sa.Column('target_roles', sa.JSON(), nullable=True),
    sa.Column('recurrence_months', sa.Integer(), nullable=True),
    sa.Column('available_from', sa.Date(), nullable=True),
    sa.Column('available_until', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('materials_url', sa.Text(), nullable=True),
    sa.Column('quiz_enabled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['regulation_id'], ['compliance_regulations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='uq_training_code')
    )
    op.create_index(op.f('ix_compliance_trainings_tenant_id'), 'compliance_trainings', ['tenant_id'], unique=False)
    op.create_table('fiscal_periods',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('fiscal_year_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('is_closed', sa.Boolean(), nullable=True),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('total_debit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('total_credit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fiscal_periods_tenant_id'), 'fiscal_periods', ['tenant_id'], unique=False)
    op.create_index('ix_fiscal_periods_tenant_number', 'fiscal_periods', ['tenant_id', 'fiscal_year_id', 'number'], unique=True)
    op.create_index('ix_fiscal_periods_tenant_year', 'fiscal_periods', ['tenant_id', 'fiscal_year_id'], unique=False)
    op.create_table('inventory_locations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', locationtype_enum, nullable=True),
    sa.Column('aisle', sa.String(length=20), nullable=True),
    sa.Column('rack', sa.String(length=20), nullable=True),
    sa.Column('level', sa.String(length=20), nullable=True),
    sa.Column('position', sa.String(length=20), nullable=True),
    sa.Column('max_weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('max_volume_m3', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('requires_lot', sa.Boolean(), nullable=True),
    sa.Column('requires_serial', sa.Boolean(), nullable=True),
    sa.Column('barcode', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'warehouse_id', 'code', name='unique_location_code')
    )
    op.create_index('idx_locations_barcode', 'inventory_locations', ['tenant_id', 'barcode'], unique=False)
    op.create_index('idx_locations_tenant', 'inventory_locations', ['tenant_id'], unique=False)
    op.create_index('idx_locations_warehouse', 'inventory_locations', ['tenant_id', 'warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_locations_tenant_id'), 'inventory_locations', ['tenant_id'], unique=False)
    op.create_table('inventory_pickings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('type', movementtype_enum, nullable=True),
    sa.Column('status', pickingstatus_enum, nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('reference_type', sa.String(length=50), nullable=True),
    sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reference_number', sa.String(length=100), nullable=True),
    sa.Column('scheduled_date', sa.DateTime(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('total_lines', sa.Integer(), nullable=True),
    sa.Column('picked_lines', sa.Integer(), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='unique_picking_number')
    )
    op.create_index('idx_pickings_assigned', 'inventory_pickings', ['tenant_id', 'assigned_to'], unique=False)
    op.create_index('idx_pickings_reference', 'inventory_pickings', ['tenant_id', 'reference_type', 'reference_id'], unique=False)
    op.create_index('idx_pickings_status', 'inventory_pickings', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_pickings_tenant', 'inventory_pickings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_pickings_tenant_id'), 'inventory_pickings', ['tenant_id'], unique=False)
    op.create_table('inventory_valuations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('valuation_date', sa.Date(), nullable=False),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('total_products', sa.Integer(), nullable=True),
    sa.Column('total_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('total_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('value_fifo', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('value_lifo', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('value_avg', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('value_standard', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('details', postgresql.JSONB(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_valuations_date', 'inventory_valuations', ['tenant_id', 'valuation_date'], unique=False)
    op.create_index('idx_valuations_tenant', 'inventory_valuations', ['tenant_id'], unique=False)
    op.create_index('idx_valuations_warehouse', 'inventory_valuations', ['tenant_id', 'warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_valuations_tenant_id'), 'inventory_valuations', ['tenant_id'], unique=False)
    op.create_table('journals',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('type', journaltype_enum, nullable=False),
    sa.Column('default_debit_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('default_credit_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('sequence_prefix', sa.String(length=10), nullable=True),
    sa.Column('next_sequence', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['default_credit_account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['default_debit_account_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_journals_tenant_code', 'journals', ['tenant_id', 'code'], unique=True)
    op.create_index(op.f('ix_journals_tenant_id'), 'journals', ['tenant_id'], unique=False)
    op.create_index('ix_journals_tenant_type', 'journals', ['tenant_id', 'type'], unique=False)
    op.create_table('maintenance_asset_documents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('document_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('file_name', sa.String(length=200), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('version', sa.String(length=50), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_until', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_asset_doc_asset', 'maintenance_asset_documents', ['asset_id'], unique=False)
    op.create_index('idx_asset_doc_tenant', 'maintenance_asset_documents', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_asset_documents_tenant_id'), 'maintenance_asset_documents', ['tenant_id'], unique=False)
    op.create_table('maintenance_asset_meters',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('meter_code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('meter_type', sa.String(length=50), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('current_reading', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('last_reading_date', sa.DateTime(), nullable=True),
    sa.Column('initial_reading', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('alert_threshold', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('critical_threshold', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('max_reading', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('maintenance_trigger_value', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('last_maintenance_reading', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('asset_id', 'meter_code', name='uq_asset_meter')
    )
    op.create_index('idx_meter_asset', 'maintenance_asset_meters', ['asset_id'], unique=False)
    op.create_index('idx_meter_tenant', 'maintenance_asset_meters', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_asset_meters_tenant_id'), 'maintenance_asset_meters', ['tenant_id'], unique=False)
    op.create_table('maintenance_kpis',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('period_start', sa.Date(), nullable=False),
    sa.Column('period_end', sa.Date(), nullable=False),
    sa.Column('period_type', sa.String(length=20), nullable=True),
    sa.Column('availability_rate', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('uptime_hours', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('downtime_hours', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('planned_downtime_hours', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('unplanned_downtime_hours', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('mtbf_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('mttr_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('mttf_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('failure_count', sa.Integer(), nullable=True),
    sa.Column('wo_total', sa.Integer(), nullable=True),
    sa.Column('wo_preventive', sa.Integer(), nullable=True),
    sa.Column('wo_corrective', sa.Integer(), nullable=True),
    sa.Column('wo_completed', sa.Integer(), nullable=True),
    sa.Column('wo_overdue', sa.Integer(), nullable=True),
    sa.Column('wo_on_time_rate', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('total_maintenance_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('labor_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('parts_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('external_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('cost_per_asset', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('cost_per_hour', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('preventive_ratio', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('schedule_compliance', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('work_order_backlog', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mkpi_asset', 'maintenance_kpis', ['asset_id'], unique=False)
    op.create_index('idx_mkpi_period', 'maintenance_kpis', ['period_start', 'period_end'], unique=False)
    op.create_index('idx_mkpi_tenant', 'maintenance_kpis', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_kpis_tenant_id'), 'maintenance_kpis', ['tenant_id'], unique=False)
    op.create_table('production_bom',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('version', sa.String(length=20), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('type', bomtype_enum, nullable=True),
    sa.Column('status', bomstatus_enum, nullable=True),
    sa.Column('routing_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('material_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('labor_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('overhead_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('allow_alternatives', sa.Boolean(), nullable=True),
    sa.Column('consumption_type', consumptiontype_enum, nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['routing_id'], ['production_routings.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', 'version', name='unique_bom_code_version')
    )
    op.create_index('idx_bom_product', 'production_bom', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_bom_tenant', 'production_bom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_production_bom_tenant_id'), 'production_bom', ['tenant_id'], unique=False)
    op.create_table('production_maintenance_schedules',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('work_center_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('frequency_type', sa.String(length=20), nullable=False),
    sa.Column('frequency_value', sa.Integer(), nullable=True),
    sa.Column('duration_hours', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('last_maintenance', sa.DateTime(), nullable=True),
    sa.Column('next_maintenance', sa.DateTime(), nullable=True),
    sa.Column('cycles_since_last', sa.Integer(), nullable=True),
    sa.Column('hours_since_last', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['work_center_id'], ['production_work_centers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_maint_next', 'production_maintenance_schedules', ['tenant_id', 'next_maintenance'], unique=False)
    op.create_index('idx_maint_wc', 'production_maintenance_schedules', ['tenant_id', 'work_center_id'], unique=False)
    op.create_index(op.f('ix_production_maintenance_schedules_tenant_id'), 'production_maintenance_schedules', ['tenant_id'], unique=False)
    op.create_table('production_routing_operations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('routing_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', operationtype_enum, nullable=True),
    sa.Column('work_center_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('setup_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('operation_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('cleanup_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('wait_time', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('batch_size', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('labor_cost_per_hour', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('machine_cost_per_hour', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('is_subcontracted', sa.Boolean(), nullable=True),
    sa.Column('subcontractor_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('requires_quality_check', sa.Boolean(), nullable=True),
    sa.Column('skill_required', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['routing_id'], ['production_routings.id'], ),
    sa.ForeignKeyConstraint(['work_center_id'], ['production_work_centers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_routing_op', 'production_routing_operations', ['tenant_id', 'routing_id', 'sequence'], unique=False)
    op.create_index(op.f('ix_production_routing_operations_tenant_id'), 'production_routing_operations', ['tenant_id'], unique=False)
    op.create_table('production_wc_capacity',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('work_center_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift', sa.String(length=20), nullable=True),
    sa.Column('available_hours', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('planned_hours', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('actual_hours', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['work_center_id'], ['production_work_centers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'work_center_id', 'date', 'shift', name='unique_wc_capacity')
    )
    op.create_index('idx_wc_cap_date', 'production_wc_capacity', ['tenant_id', 'work_center_id', 'date'], unique=False)
    op.create_index(op.f('ix_production_wc_capacity_tenant_id'), 'production_wc_capacity', ['tenant_id'], unique=False)
    op.create_table('bank_accounts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('bank_name', sa.String(length=255), nullable=True),
    sa.Column('account_number', sa.String(length=50), nullable=True),
    sa.Column('iban', sa.String(length=50), nullable=True),
    sa.Column('bic', sa.String(length=20), nullable=True),
    sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('journal_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('initial_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('current_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('reconciled_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['journal_id'], ['journals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_accounts_tenant', 'bank_accounts', ['tenant_id'], unique=False)
    op.create_index('ix_bank_accounts_tenant_iban', 'bank_accounts', ['tenant_id', 'iban'], unique=False)
    op.create_index(op.f('ix_bank_accounts_tenant_id'), 'bank_accounts', ['tenant_id'], unique=False)
    op.create_table('compliance_audit_findings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('severity', findingseverity_enum, nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('evidence', sa.Text(), nullable=True),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('recommendation', sa.Text(), nullable=True),
    sa.Column('identified_date', sa.Date(), nullable=True),
    sa.Column('response_due_date', sa.Date(), nullable=True),
    sa.Column('closure_date', sa.Date(), nullable=True),
    sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_closed', sa.Boolean(), nullable=True),
    sa.Column('response', sa.Text(), nullable=True),
    sa.Column('response_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['audit_id'], ['compliance_audits.id'], ),
    sa.ForeignKeyConstraint(['requirement_id'], ['compliance_requirements.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_audit_findings_tenant_id'), 'compliance_audit_findings', ['tenant_id'], unique=False)
    op.create_index('ix_finding_tenant_severity', 'compliance_audit_findings', ['tenant_id', 'severity'], unique=False)
    op.create_table('compliance_gaps',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('gap_description', sa.Text(), nullable=False),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('impact_description', sa.Text(), nullable=True),
    sa.Column('severity', risklevel_enum, nullable=True),
    sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('current_status', compliancestatus_enum, nullable=True),
    sa.Column('evidence_reviewed', sa.JSON(), nullable=True),
    sa.Column('evidence_gaps', sa.Text(), nullable=True),
    sa.Column('identified_date', sa.Date(), nullable=True),
    sa.Column('target_closure_date', sa.Date(), nullable=True),
    sa.Column('actual_closure_date', sa.Date(), nullable=True),
    sa.Column('is_open', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['assessment_id'], ['compliance_assessments.id'], ),
    sa.ForeignKeyConstraint(['requirement_id'], ['compliance_requirements.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_gaps_tenant_id'), 'compliance_gaps', ['tenant_id'], unique=False)
    op.create_index('ix_gap_tenant_open', 'compliance_gaps', ['tenant_id', 'is_open'], unique=False)
    op.create_table('compliance_training_completions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('training_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('assigned_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('passed', sa.Boolean(), nullable=True),
    sa.Column('attempts', sa.Integer(), nullable=True),
    sa.Column('certificate_number', sa.String(length=100), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('is_current', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['training_id'], ['compliance_trainings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_completion_tenant_user', 'compliance_training_completions', ['tenant_id', 'user_id'], unique=False)
    op.create_index(op.f('ix_compliance_training_completions_tenant_id'), 'compliance_training_completions', ['tenant_id'], unique=False)
    op.create_table('financial_reports',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('report_type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('fiscal_year_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('period_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('data', postgresql.JSON(), nullable=False),
    sa.Column('parameters', postgresql.JSON(), nullable=True),
    sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('generated_at', sa.DateTime(), nullable=True),
    sa.Column('pdf_url', sa.String(length=500), nullable=True),
    sa.Column('excel_url', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['fiscal_periods.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_reports_tenant_id'), 'financial_reports', ['tenant_id'], unique=False)
    op.create_index('ix_reports_tenant_dates', 'financial_reports', ['tenant_id', 'start_date', 'end_date'], unique=False)
    op.create_index('ix_reports_tenant_type', 'financial_reports', ['tenant_id', 'report_type'], unique=False)
    op.create_table('inventory_counts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('status', inventorystatus_enum, nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('planned_date', sa.Date(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('total_items', sa.Integer(), nullable=True),
    sa.Column('counted_items', sa.Integer(), nullable=True),
    sa.Column('discrepancy_items', sa.Integer(), nullable=True),
    sa.Column('total_discrepancy_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('validated_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['inventory_categories.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='unique_count_number')
    )
    op.create_index('idx_counts_status', 'inventory_counts', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_counts_tenant', 'inventory_counts', ['tenant_id'], unique=False)
    op.create_index('idx_counts_warehouse', 'inventory_counts', ['tenant_id', 'warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_counts_tenant_id'), 'inventory_counts', ['tenant_id'], unique=False)
    op.create_table('inventory_movements',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('type', movementtype_enum, nullable=False),
    sa.Column('status', movementstatus_enum, nullable=True),
    sa.Column('movement_date', sa.DateTime(), nullable=False),
    sa.Column('from_warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('from_location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('to_warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('to_location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reference_type', sa.String(length=50), nullable=True),
    sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reference_number', sa.String(length=100), nullable=True),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('total_items', sa.Integer(), nullable=True),
    sa.Column('total_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('total_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('confirmed_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['from_location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['from_warehouse_id'], ['inventory_warehouses.id'], ),
    sa.ForeignKeyConstraint(['to_location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['to_warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='unique_movement_number')
    )
    op.create_index('idx_movements_date', 'inventory_movements', ['tenant_id', 'movement_date'], unique=False)
    op.create_index('idx_movements_reference', 'inventory_movements', ['tenant_id', 'reference_type', 'reference_id'], unique=False)
    op.create_index('idx_movements_status', 'inventory_movements', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_movements_tenant', 'inventory_movements', ['tenant_id'], unique=False)
    op.create_index('idx_movements_type', 'inventory_movements', ['tenant_id', 'type'], unique=False)
    op.create_index(op.f('ix_inventory_movements_tenant_id'), 'inventory_movements', ['tenant_id'], unique=False)
    op.create_table('inventory_products',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('code', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type', producttype_enum, nullable=True),
    sa.Column('status', productstatus_enum, nullable=True),
    sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('barcode', sa.String(length=100), nullable=True),
    sa.Column('ean13', sa.String(length=13), nullable=True),
    sa.Column('sku', sa.String(length=100), nullable=True),
    sa.Column('manufacturer_code', sa.String(length=100), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('purchase_unit', sa.String(length=20), nullable=True),
    sa.Column('purchase_unit_factor', sa.Numeric(precision=10, scale=4), nullable=True),
    sa.Column('sale_unit', sa.String(length=20), nullable=True),
    sa.Column('sale_unit_factor', sa.Numeric(precision=10, scale=4), nullable=True),
    sa.Column('standard_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('average_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('last_purchase_price', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('sale_price', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('valuation_method', valuationmethod_enum, nullable=True),
    sa.Column('min_stock', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('max_stock', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('reorder_point', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('reorder_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('lead_time_days', sa.Integer(), nullable=True),
    sa.Column('weight_kg', sa.Numeric(precision=10, scale=4), nullable=True),
    sa.Column('volume_m3', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('length_cm', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('width_cm', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('height_cm', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('track_lot', sa.Boolean(), nullable=True),
    sa.Column('track_serial', sa.Boolean(), nullable=True),
    sa.Column('track_expiry', sa.Boolean(), nullable=True),
    sa.Column('expiry_warning_days', sa.Integer(), nullable=True),
    sa.Column('default_warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('default_location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('default_supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('stock_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('expense_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('income_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('tags', postgresql.JSONB(), nullable=True),
    sa.Column('custom_fields', postgresql.JSONB(), nullable=True),
    sa.Column('image_url', sa.String(length=500), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['inventory_categories.id'], ),
    sa.ForeignKeyConstraint(['default_location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['default_warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'code', name='unique_product_code')
    )
    op.create_index('idx_products_barcode', 'inventory_products', ['tenant_id', 'barcode'], unique=False)
    op.create_index('idx_products_category', 'inventory_products', ['tenant_id', 'category_id'], unique=False)
    op.create_index('idx_products_sku', 'inventory_products', ['tenant_id', 'sku'], unique=False)
    op.create_index('idx_products_status', 'inventory_products', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_products_tenant', 'inventory_products', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_products_tenant_id'), 'inventory_products', ['tenant_id'], unique=False)
    op.create_table('journal_entries',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('journal_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('fiscal_year_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', entrystatus_enum, nullable=True),
    sa.Column('total_debit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('total_credit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('source_type', sa.String(length=50), nullable=True),
    sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('validated_at', sa.DateTime(), nullable=True),
    sa.Column('posted_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('posted_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ),
    sa.ForeignKeyConstraint(['journal_id'], ['journals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_entries_tenant_date', 'journal_entries', ['tenant_id', 'date'], unique=False)
    op.create_index('ix_entries_tenant_journal', 'journal_entries', ['tenant_id', 'journal_id'], unique=False)
    op.create_index('ix_entries_tenant_number', 'journal_entries', ['tenant_id', 'journal_id', 'number'], unique=True)
    op.create_index('ix_entries_tenant_status', 'journal_entries', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_journal_entries_tenant_id'), 'journal_entries', ['tenant_id'], unique=False)
    op.create_table('maintenance_meter_readings',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('meter_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('reading_date', sa.DateTime(), nullable=False),
    sa.Column('reading_value', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('delta', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['meter_id'], ['maintenance_asset_meters.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reading_date', 'maintenance_meter_readings', ['reading_date'], unique=False)
    op.create_index('idx_reading_meter', 'maintenance_meter_readings', ['meter_id'], unique=False)
    op.create_index('idx_reading_tenant', 'maintenance_meter_readings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_meter_readings_tenant_id'), 'maintenance_meter_readings', ['tenant_id'], unique=False)
    op.create_table('maintenance_plans',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('plan_code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('maintenance_type', maintenancetype_enum, nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('asset_category', assetcategory_enum, nullable=True),
    sa.Column('trigger_type', sa.String(length=50), nullable=False),
    sa.Column('frequency_value', sa.Integer(), nullable=True),
    sa.Column('frequency_unit', sa.String(length=20), nullable=True),
    sa.Column('trigger_meter_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('trigger_meter_interval', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('last_execution_date', sa.Date(), nullable=True),
    sa.Column('next_due_date', sa.Date(), nullable=True),
    sa.Column('lead_time_days', sa.Integer(), nullable=True),
    sa.Column('estimated_duration_hours', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('estimated_labor_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('estimated_parts_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('safety_instructions', sa.Text(), nullable=True),
    sa.Column('required_tools', postgresql.JSONB(), nullable=True),
    sa.Column('required_certifications', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ),
    sa.ForeignKeyConstraint(['trigger_meter_id'], ['maintenance_asset_meters.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'plan_code', name='uq_mplan_code')
    )
    op.create_index('idx_mplan_code', 'maintenance_plans', ['tenant_id', 'plan_code'], unique=False)
    op.create_index('idx_mplan_tenant', 'maintenance_plans', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_plans_tenant_id'), 'maintenance_plans', ['tenant_id'], unique=False)
    op.create_table('production_bom_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('bom_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('line_number', sa.Integer(), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('operation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('scrap_rate', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('is_critical', sa.Boolean(), nullable=True),
    sa.Column('alternative_group', sa.String(length=50), nullable=True),
    sa.Column('consumption_type', consumptiontype_enum, nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bom_id'], ['production_bom.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bom_line', 'production_bom_lines', ['tenant_id', 'bom_id'], unique=False)
    op.create_index(op.f('ix_production_bom_lines_tenant_id'), 'production_bom_lines', ['tenant_id'], unique=False)
    op.create_table('production_manufacturing_orders',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('bom_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('routing_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('quantity_planned', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('quantity_produced', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_scrapped', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('status', mostatus_enum, nullable=True),
    sa.Column('priority', mopriority_enum, nullable=True),
    sa.Column('scheduled_start', sa.DateTime(), nullable=True),
    sa.Column('scheduled_end', sa.DateTime(), nullable=True),
    sa.Column('actual_start', sa.DateTime(), nullable=True),
    sa.Column('actual_end', sa.DateTime(), nullable=True),
    sa.Column('deadline', sa.DateTime(), nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('origin_type', sa.String(length=50), nullable=True),
    sa.Column('origin_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('origin_number', sa.String(length=50), nullable=True),
    sa.Column('planned_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('actual_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('material_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('labor_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('overhead_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('progress_percent', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('confirmed_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['bom_id'], ['production_bom.id'], ),
    sa.ForeignKeyConstraint(['routing_id'], ['production_routings.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='unique_mo_number')
    )
    op.create_index('idx_mo_dates', 'production_manufacturing_orders', ['tenant_id', 'scheduled_start', 'scheduled_end'], unique=False)
    op.create_index('idx_mo_product', 'production_manufacturing_orders', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_mo_status', 'production_manufacturing_orders', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_mo_tenant', 'production_manufacturing_orders', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_production_manufacturing_orders_tenant_id'), 'production_manufacturing_orders', ['tenant_id'], unique=False)
    op.create_table('accounting_documents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('document_type', documenttype_enum, nullable=False),
    sa.Column('source', documentsource_enum, nullable=False),
    sa.Column('status', documentstatus_enum, nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('original_filename', sa.String(length=255), nullable=True),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('file_hash', sa.String(length=64), nullable=True),
    sa.Column('document_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('received_at', sa.DateTime(), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('partner_name', sa.String(length=255), nullable=True),
    sa.Column('partner_tax_id', sa.String(length=50), nullable=True),
    sa.Column('amount_untaxed', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount_tax', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount_total', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('payment_status', paymentstatus_enum, nullable=True),
    sa.Column('amount_paid', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount_remaining', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('ocr_raw_text', sa.Text(), nullable=True),
    sa.Column('ocr_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('ai_confidence', confidencelevel_enum, nullable=True),
    sa.Column('ai_confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('ai_suggested_account', sa.String(length=20), nullable=True),
    sa.Column('ai_suggested_journal', sa.String(length=20), nullable=True),
    sa.Column('ai_analysis', postgresql.JSON(), nullable=True),
    sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('requires_validation', sa.Boolean(), nullable=True),
    sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('validated_at', sa.DateTime(), nullable=True),
    sa.Column('validation_notes', sa.Text(), nullable=True),
    sa.Column('email_from', sa.String(length=255), nullable=True),
    sa.Column('email_subject', sa.String(length=500), nullable=True),
    sa.Column('email_received_at', sa.DateTime(), nullable=True),
    sa.Column('tags', postgresql.JSON(), nullable=True),
    sa.Column('custom_fields', postgresql.JSON(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_accdocs_file_hash', 'accounting_documents', ['tenant_id', 'file_hash'], unique=False)
    op.create_index('idx_accdocs_reference', 'accounting_documents', ['tenant_id', 'reference'], unique=False)
    op.create_index('idx_accdocs_tenant', 'accounting_documents', ['tenant_id'], unique=False)
    op.create_index('idx_accdocs_tenant_date', 'accounting_documents', ['tenant_id', 'document_date'], unique=False)
    op.create_index('idx_accdocs_tenant_partner', 'accounting_documents', ['tenant_id', 'partner_id'], unique=False)
    op.create_index('idx_accdocs_tenant_payment', 'accounting_documents', ['tenant_id', 'payment_status'], unique=False)
    op.create_index('idx_accdocs_tenant_status', 'accounting_documents', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_accdocs_tenant_type', 'accounting_documents', ['tenant_id', 'document_type'], unique=False)
    op.create_index(op.f('ix_accounting_documents_tenant_id'), 'accounting_documents', ['tenant_id'], unique=False)
    op.create_table('accounting_synced_bank_accounts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('external_account_id', sa.String(length=255), nullable=False),
    sa.Column('account_name', sa.String(length=255), nullable=False),
    sa.Column('account_number_masked', sa.String(length=50), nullable=True),
    sa.Column('iban_masked', sa.String(length=50), nullable=True),
    sa.Column('account_type', sa.String(length=50), nullable=True),
    sa.Column('account_subtype', sa.String(length=50), nullable=True),
    sa.Column('balance_current', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('balance_available', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('balance_limit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('balance_currency', sa.String(length=3), nullable=True),
    sa.Column('balance_updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_sync_enabled', sa.Boolean(), nullable=True),
    sa.Column('last_transaction_date', sa.Date(), nullable=True),
    sa.Column('oldest_transaction_date', sa.Date(), nullable=True),
    sa.Column('extra_data', postgresql.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ),
    sa.ForeignKeyConstraint(['connection_id'], ['accounting_bank_connections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'connection_id', 'external_account_id', name='uq_syncedacc_external')
    )
    op.create_index('idx_syncedacc_connection', 'accounting_synced_bank_accounts', ['connection_id'], unique=False)
    op.create_index('idx_syncedacc_tenant', 'accounting_synced_bank_accounts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_synced_bank_accounts_tenant_id'), 'accounting_synced_bank_accounts', ['tenant_id'], unique=False)
    op.create_table('bank_statements',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('opening_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('closing_balance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('total_credits', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('total_debits', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('is_reconciled', sa.Boolean(), nullable=True),
    sa.Column('reconciled_at', sa.DateTime(), nullable=True),
    sa.Column('reconciled_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_statements_tenant_account', 'bank_statements', ['tenant_id', 'bank_account_id'], unique=False)
    op.create_index('ix_bank_statements_tenant_date', 'bank_statements', ['tenant_id', 'date'], unique=False)
    op.create_index(op.f('ix_bank_statements_tenant_id'), 'bank_statements', ['tenant_id'], unique=False)
    op.create_table('compliance_actions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('gap_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('action_type', sa.String(length=50), nullable=True),
    sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('completion_date', sa.Date(), nullable=True),
    sa.Column('status', actionstatus_enum, nullable=True),
    sa.Column('priority', requirementpriority_enum, nullable=True),
    sa.Column('progress_percent', sa.Integer(), nullable=True),
    sa.Column('resolution_notes', sa.Text(), nullable=True),
    sa.Column('evidence_provided', sa.JSON(), nullable=True),
    sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('verified_at', sa.DateTime(), nullable=True),
    sa.Column('verification_notes', sa.Text(), nullable=True),
    sa.Column('estimated_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['gap_id'], ['compliance_gaps.id'], ),
    sa.ForeignKeyConstraint(['requirement_id'], ['compliance_requirements.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'number', name='uq_compliance_action_number')
    )
    op.create_index('ix_action_tenant_status', 'compliance_actions', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_compliance_actions_tenant_id'), 'compliance_actions', ['tenant_id'], unique=False)
    op.create_table('inventory_lots',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('number', sa.String(length=100), nullable=False),
    sa.Column('status', lotstatus_enum, nullable=True),
    sa.Column('production_date', sa.Date(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('reception_date', sa.Date(), nullable=True),
    sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('supplier_lot', sa.String(length=100), nullable=True),
    sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('initial_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('current_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'product_id', 'number', name='unique_lot_number')
    )
    op.create_index('idx_lots_expiry', 'inventory_lots', ['tenant_id', 'expiry_date'], unique=False)
    op.create_index('idx_lots_product', 'inventory_lots', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_lots_status', 'inventory_lots', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_lots_tenant', 'inventory_lots', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_lots_tenant_id'), 'inventory_lots', ['tenant_id'], unique=False)
    op.create_table('inventory_replenishment_rules',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('min_stock', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('max_stock', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('reorder_point', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('reorder_quantity', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('lead_time_days', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'product_id', 'warehouse_id', name='unique_replenishment_rule')
    )
    op.create_index('idx_replenishment_product', 'inventory_replenishment_rules', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_replenishment_tenant', 'inventory_replenishment_rules', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_replenishment_rules_tenant_id'), 'inventory_replenishment_rules', ['tenant_id'], unique=False)
    op.create_table('inventory_stock_levels',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('quantity_on_hand', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('quantity_reserved', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('quantity_available', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('quantity_incoming', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('quantity_outgoing', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('total_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('average_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('last_movement_at', sa.DateTime(), nullable=True),
    sa.Column('last_count_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'product_id', 'warehouse_id', 'location_id', name='unique_stock_level')
    )
    op.create_index('idx_stock_levels_product', 'inventory_stock_levels', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_stock_levels_tenant', 'inventory_stock_levels', ['tenant_id'], unique=False)
    op.create_index('idx_stock_levels_warehouse', 'inventory_stock_levels', ['tenant_id', 'warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_stock_levels_tenant_id'), 'inventory_stock_levels', ['tenant_id'], unique=False)
    op.create_table('journal_entry_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('line_number', sa.Integer(), nullable=False),
    sa.Column('debit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('credit', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('label', sa.String(length=255), nullable=True),
    sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('partner_type', sa.String(length=20), nullable=True),
    sa.Column('reconcile_ref', sa.String(length=50), nullable=True),
    sa.Column('reconciled_at', sa.DateTime(), nullable=True),
    sa.Column('analytic_account', sa.String(length=50), nullable=True),
    sa.Column('analytic_tags', postgresql.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('(debit = 0 OR credit = 0)', name='check_debit_or_credit'),
    sa.CheckConstraint('(debit >= 0 AND credit >= 0)', name='check_positive_amounts'),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_entry_lines_tenant_account', 'journal_entry_lines', ['tenant_id', 'account_id'], unique=False)
    op.create_index('ix_entry_lines_tenant_entry', 'journal_entry_lines', ['tenant_id', 'entry_id'], unique=False)
    op.create_index('ix_entry_lines_tenant_reconcile', 'journal_entry_lines', ['tenant_id', 'reconcile_ref'], unique=False)
    op.create_index(op.f('ix_journal_entry_lines_tenant_id'), 'journal_entry_lines', ['tenant_id'], unique=False)
    op.create_table('maintenance_plan_tasks',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('task_code', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('detailed_instructions', sa.Text(), nullable=True),
    sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
    sa.Column('required_skill', sa.String(length=100), nullable=True),
    sa.Column('required_parts', postgresql.JSONB(), nullable=True),
    sa.Column('check_points', postgresql.JSONB(), nullable=True),
    sa.Column('is_mandatory', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['maintenance_plans.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mplan_task_plan', 'maintenance_plan_tasks', ['plan_id'], unique=False)
    op.create_index('idx_mplan_task_tenant', 'maintenance_plan_tasks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_plan_tasks_tenant_id'), 'maintenance_plan_tasks', ['tenant_id'], unique=False)
    op.create_table('maintenance_spare_parts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('part_code', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=300), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('manufacturer', sa.String(length=200), nullable=True),
    sa.Column('manufacturer_part_number', sa.String(length=100), nullable=True),
    sa.Column('preferred_supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('equivalent_parts', postgresql.JSONB(), nullable=True),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('last_purchase_price', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('min_stock_level', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('max_stock_level', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('reorder_point', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('reorder_quantity', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('lead_time_days', sa.Integer(), nullable=True),
    sa.Column('criticality', assetcriticality_enum, nullable=True),
    sa.Column('shelf_life_days', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('specifications', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'part_code', name='uq_spare_code')
    )
    op.create_index('idx_spare_code', 'maintenance_spare_parts', ['tenant_id', 'part_code'], unique=False)
    op.create_index('idx_spare_tenant', 'maintenance_spare_parts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_spare_parts_tenant_id'), 'maintenance_spare_parts', ['tenant_id'], unique=False)
    op.create_table('production_plan_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('bom_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('quantity_demanded', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_available', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_to_produce', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('required_date', sa.Date(), nullable=True),
    sa.Column('planned_start', sa.Date(), nullable=True),
    sa.Column('planned_end', sa.Date(), nullable=True),
    sa.Column('mo_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('priority', mopriority_enum, nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['mo_id'], ['production_manufacturing_orders.id'], ),
    sa.ForeignKeyConstraint(['plan_id'], ['production_plans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plan_line', 'production_plan_lines', ['tenant_id', 'plan_id'], unique=False)
    op.create_index('idx_plan_line_product', 'production_plan_lines', ['tenant_id', 'product_id'], unique=False)
    op.create_index(op.f('ix_production_plan_lines_tenant_id'), 'production_plan_lines', ['tenant_id'], unique=False)
    op.create_table('production_work_orders',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('mo_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('operation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('work_center_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', prodworkorderstatus_enum, nullable=True),
    sa.Column('quantity_planned', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('quantity_done', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_scrapped', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('setup_time_planned', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('operation_time_planned', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('setup_time_actual', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('operation_time_actual', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('scheduled_start', sa.DateTime(), nullable=True),
    sa.Column('scheduled_end', sa.DateTime(), nullable=True),
    sa.Column('actual_start', sa.DateTime(), nullable=True),
    sa.Column('actual_end', sa.DateTime(), nullable=True),
    sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('labor_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('machine_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['mo_id'], ['production_manufacturing_orders.id'], ),
    sa.ForeignKeyConstraint(['operation_id'], ['production_routing_operations.id'], ),
    sa.ForeignKeyConstraint(['work_center_id'], ['production_work_centers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wo_mo', 'production_work_orders', ['tenant_id', 'mo_id', 'sequence'], unique=False)
    op.create_index('idx_wo_wc', 'production_work_orders', ['tenant_id', 'work_center_id', 'status'], unique=False)
    op.create_index(op.f('ix_production_work_orders_tenant_id'), 'production_work_orders', ['tenant_id'], unique=False)
    op.create_table('accounting_ai_classifications',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('model_name', sa.String(length=100), nullable=False),
    sa.Column('model_version', sa.String(length=20), nullable=True),
    sa.Column('document_type_predicted', documenttype_enum, nullable=True),
    sa.Column('document_type_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('vendor_name', sa.String(length=255), nullable=True),
    sa.Column('vendor_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('invoice_number', sa.String(length=100), nullable=True),
    sa.Column('invoice_number_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('invoice_date', sa.Date(), nullable=True),
    sa.Column('invoice_date_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('due_date_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('amount_untaxed', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount_untaxed_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('amount_tax', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount_tax_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('amount_total', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('amount_total_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('tax_rates', postgresql.JSON(), nullable=True),
    sa.Column('suggested_account_code', sa.String(length=20), nullable=True),
    sa.Column('suggested_account_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('suggested_journal_code', sa.String(length=20), nullable=True),
    sa.Column('suggested_journal_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('expense_category', sa.String(length=100), nullable=True),
    sa.Column('expense_category_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('overall_confidence', confidencelevel_enum, nullable=False),
    sa.Column('overall_confidence_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('classification_reasons', postgresql.JSON(), nullable=True),
    sa.Column('was_corrected', sa.Boolean(), nullable=True),
    sa.Column('corrected_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('corrected_at', sa.DateTime(), nullable=True),
    sa.Column('correction_feedback', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['accounting_documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_aiclass_tenant_confidence', 'accounting_ai_classifications', ['tenant_id', 'overall_confidence'], unique=False)
    op.create_index('idx_aiclass_tenant_doc', 'accounting_ai_classifications', ['tenant_id', 'document_id'], unique=False)
    op.create_index(op.f('ix_accounting_ai_classifications_tenant_id'), 'accounting_ai_classifications', ['tenant_id'], unique=False)
    op.create_table('accounting_alerts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('alert_type', alerttype_enum, nullable=False),
    sa.Column('severity', alertseverity_enum, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=True),
    sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('target_roles', postgresql.JSON(), nullable=True),
    sa.Column('target_users', postgresql.JSON(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('read_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('is_resolved', sa.Boolean(), nullable=True),
    sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('resolution_notes', sa.Text(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('extra_data', postgresql.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['accounting_documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_entity', 'accounting_alerts', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_alert_tenant', 'accounting_alerts', ['tenant_id'], unique=False)
    op.create_index('idx_alert_tenant_type', 'accounting_alerts', ['tenant_id', 'alert_type'], unique=False)
    op.create_index('idx_alert_tenant_unresolved', 'accounting_alerts', ['tenant_id', 'is_resolved'], unique=False)
    op.create_index(op.f('ix_accounting_alerts_tenant_id'), 'accounting_alerts', ['tenant_id'], unique=False)
    op.create_table('accounting_auto_entries',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('confidence_level', confidencelevel_enum, nullable=False),
    sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('entry_template', sa.String(length=100), nullable=True),
    sa.Column('accounting_rules_applied', postgresql.JSON(), nullable=True),
    sa.Column('proposed_lines', postgresql.JSON(), nullable=False),
    sa.Column('auto_validated', sa.Boolean(), nullable=True),
    sa.Column('requires_review', sa.Boolean(), nullable=True),
    sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('was_modified', sa.Boolean(), nullable=True),
    sa.Column('original_lines', postgresql.JSON(), nullable=True),
    sa.Column('modification_reason', sa.Text(), nullable=True),
    sa.Column('is_posted', sa.Boolean(), nullable=True),
    sa.Column('posted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['accounting_documents.id'], ),
    sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_autoentry_tenant_confidence', 'accounting_auto_entries', ['tenant_id', 'confidence_level'], unique=False)
    op.create_index('idx_autoentry_tenant_doc', 'accounting_auto_entries', ['tenant_id', 'document_id'], unique=False)
    op.create_index('idx_autoentry_tenant_review', 'accounting_auto_entries', ['tenant_id', 'requires_review'], unique=False)
    op.create_index(op.f('ix_accounting_auto_entries_tenant_id'), 'accounting_auto_entries', ['tenant_id'], unique=False)
    op.create_table('accounting_ocr_results',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('ocr_engine', sa.String(length=50), nullable=False),
    sa.Column('ocr_version', sa.String(length=20), nullable=True),
    sa.Column('processing_time_ms', sa.Integer(), nullable=True),
    sa.Column('overall_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('structured_data', postgresql.JSON(), nullable=True),
    sa.Column('extracted_fields', postgresql.JSON(), nullable=False),
    sa.Column('errors', postgresql.JSON(), nullable=True),
    sa.Column('warnings', postgresql.JSON(), nullable=True),
    sa.Column('image_quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('image_resolution', sa.String(length=20), nullable=True),
    sa.Column('page_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['accounting_documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ocr_tenant_doc', 'accounting_ocr_results', ['tenant_id', 'document_id'], unique=False)
    op.create_index(op.f('ix_accounting_ocr_results_tenant_id'), 'accounting_ocr_results', ['tenant_id'], unique=False)
    op.create_table('accounting_synced_transactions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('synced_account_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('external_transaction_id', sa.String(length=255), nullable=False),
    sa.Column('transaction_date', sa.Date(), nullable=False),
    sa.Column('value_date', sa.Date(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('merchant_name', sa.String(length=255), nullable=True),
    sa.Column('merchant_category', sa.String(length=100), nullable=True),
    sa.Column('ai_category', sa.String(length=100), nullable=True),
    sa.Column('ai_category_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('reconciliation_status', reconciliationstatusauto_enum, nullable=True),
    sa.Column('matched_document_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('matched_entry_line_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('matched_at', sa.DateTime(), nullable=True),
    sa.Column('match_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('raw_data', postgresql.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['matched_document_id'], ['accounting_documents.id'], ),
    sa.ForeignKeyConstraint(['matched_entry_line_id'], ['journal_entry_lines.id'], ),
    sa.ForeignKeyConstraint(['synced_account_id'], ['accounting_synced_bank_accounts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'synced_account_id', 'external_transaction_id', name='uq_syncedtrans_external')
    )
    op.create_index('idx_syncedtrans_account', 'accounting_synced_transactions', ['synced_account_id'], unique=False)
    op.create_index('idx_syncedtrans_date', 'accounting_synced_transactions', ['tenant_id', 'transaction_date'], unique=False)
    op.create_index('idx_syncedtrans_recon', 'accounting_synced_transactions', ['tenant_id', 'reconciliation_status'], unique=False)
    op.create_index('idx_syncedtrans_tenant', 'accounting_synced_transactions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_accounting_synced_transactions_tenant_id'), 'accounting_synced_transactions', ['tenant_id'], unique=False)
    op.create_table('bank_statement_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('statement_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('value_date', sa.Date(), nullable=True),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('status', reconciliationstatus_enum, nullable=True),
    sa.Column('matched_entry_line_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('matched_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['matched_entry_line_id'], ['journal_entry_lines.id'], ),
    sa.ForeignKeyConstraint(['statement_id'], ['bank_statements.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_lines_tenant_statement', 'bank_statement_lines', ['tenant_id', 'statement_id'], unique=False)
    op.create_index('ix_bank_lines_tenant_status', 'bank_statement_lines', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_bank_statement_lines_tenant_id'), 'bank_statement_lines', ['tenant_id'], unique=False)
    op.create_table('bank_transactions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('type', banktransactiontype_enum, nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('value_date', sa.Date(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('partner_name', sa.String(length=255), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('entry_line_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ),
    sa.ForeignKeyConstraint(['entry_line_id'], ['journal_entry_lines.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_trans_tenant_account', 'bank_transactions', ['tenant_id', 'bank_account_id'], unique=False)
    op.create_index('ix_bank_trans_tenant_date', 'bank_transactions', ['tenant_id', 'date'], unique=False)
    op.create_index('ix_bank_trans_tenant_type', 'bank_transactions', ['tenant_id', 'type'], unique=False)
    op.create_index(op.f('ix_bank_transactions_tenant_id'), 'bank_transactions', ['tenant_id'], unique=False)
    op.create_table('inventory_count_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('count_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('theoretical_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('counted_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('discrepancy', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('discrepancy_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('counted_at', sa.DateTime(), nullable=True),
    sa.Column('counted_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['count_id'], ['inventory_counts.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_count_lines_count', 'inventory_count_lines', ['count_id'], unique=False)
    op.create_index('idx_count_lines_product', 'inventory_count_lines', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_count_lines_tenant', 'inventory_count_lines', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_count_lines_tenant_id'), 'inventory_count_lines', ['tenant_id'], unique=False)
    op.create_table('inventory_serial_numbers',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('number', sa.String(length=100), nullable=False),
    sa.Column('status', lotstatus_enum, nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reception_date', sa.Date(), nullable=True),
    sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('sale_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('sale_date', sa.Date(), nullable=True),
    sa.Column('warranty_end_date', sa.Date(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.ForeignKeyConstraint(['warehouse_id'], ['inventory_warehouses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'product_id', 'number', name='unique_serial_number')
    )
    op.create_index('idx_serials_product', 'inventory_serial_numbers', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_serials_status', 'inventory_serial_numbers', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_serials_tenant', 'inventory_serial_numbers', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_serial_numbers_tenant_id'), 'inventory_serial_numbers', ['tenant_id'], unique=False)
    op.create_table('maintenance_asset_components',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('component_code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('manufacturer', sa.String(length=200), nullable=True),
    sa.Column('part_number', sa.String(length=100), nullable=True),
    sa.Column('serial_number', sa.String(length=100), nullable=True),
    sa.Column('installation_date', sa.Date(), nullable=True),
    sa.Column('expected_replacement_date', sa.Date(), nullable=True),
    sa.Column('last_replacement_date', sa.Date(), nullable=True),
    sa.Column('expected_life_hours', sa.Integer(), nullable=True),
    sa.Column('expected_life_cycles', sa.Integer(), nullable=True),
    sa.Column('current_hours', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('current_cycles', sa.Integer(), nullable=True),
    sa.Column('criticality', assetcriticality_enum, nullable=True),
    sa.Column('spare_part_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['spare_part_id'], ['maintenance_spare_parts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_component_asset', 'maintenance_asset_components', ['asset_id'], unique=False)
    op.create_index('idx_component_tenant', 'maintenance_asset_components', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_asset_components_tenant_id'), 'maintenance_asset_components', ['tenant_id'], unique=False)
    op.create_table('maintenance_spare_part_stock',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('spare_part_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_description', sa.String(length=200), nullable=True),
    sa.Column('bin_location', sa.String(length=100), nullable=True),
    sa.Column('quantity_on_hand', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('quantity_reserved', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('quantity_available', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('last_count_date', sa.Date(), nullable=True),
    sa.Column('last_movement_date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['spare_part_id'], ['maintenance_spare_parts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('spare_part_id', 'location_id', name='uq_spare_stock_loc')
    )
    op.create_index('idx_spare_stock_part', 'maintenance_spare_part_stock', ['spare_part_id'], unique=False)
    op.create_index('idx_spare_stock_tenant', 'maintenance_spare_part_stock', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_spare_part_stock_tenant_id'), 'maintenance_spare_part_stock', ['tenant_id'], unique=False)
    op.create_table('production_material_consumptions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('mo_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('bom_line_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('quantity_planned', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('quantity_consumed', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_returned', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('serial_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('consumed_at', sa.DateTime(), nullable=True),
    sa.Column('consumed_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bom_line_id'], ['production_bom_lines.id'], ),
    sa.ForeignKeyConstraint(['mo_id'], ['production_manufacturing_orders.id'], ),
    sa.ForeignKeyConstraint(['work_order_id'], ['production_work_orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_consumption_mo', 'production_material_consumptions', ['tenant_id', 'mo_id'], unique=False)
    op.create_index('idx_consumption_product', 'production_material_consumptions', ['tenant_id', 'product_id'], unique=False)
    op.create_index(op.f('ix_production_material_consumptions_tenant_id'), 'production_material_consumptions', ['tenant_id'], unique=False)
    op.create_table('production_outputs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('mo_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('serial_ids', postgresql.JSONB(), nullable=True),
    sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_quality_passed', sa.Boolean(), nullable=True),
    sa.Column('quality_notes', sa.Text(), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('produced_at', sa.DateTime(), nullable=True),
    sa.Column('produced_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['mo_id'], ['production_manufacturing_orders.id'], ),
    sa.ForeignKeyConstraint(['work_order_id'], ['production_work_orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_output_mo', 'production_outputs', ['tenant_id', 'mo_id'], unique=False)
    op.create_index('idx_output_product', 'production_outputs', ['tenant_id', 'product_id'], unique=False)
    op.create_index(op.f('ix_production_outputs_tenant_id'), 'production_outputs', ['tenant_id'], unique=False)
    op.create_table('production_scraps',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('mo_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('serial_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reason', scrapreason_enum, nullable=True),
    sa.Column('reason_detail', sa.Text(), nullable=True),
    sa.Column('work_center_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('scrapped_at', sa.DateTime(), nullable=True),
    sa.Column('scrapped_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['mo_id'], ['production_manufacturing_orders.id'], ),
    sa.ForeignKeyConstraint(['work_order_id'], ['production_work_orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_scrap_mo', 'production_scraps', ['tenant_id', 'mo_id'], unique=False)
    op.create_index('idx_scrap_product', 'production_scraps', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_scrap_reason', 'production_scraps', ['tenant_id', 'reason'], unique=False)
    op.create_index(op.f('ix_production_scraps_tenant_id'), 'production_scraps', ['tenant_id'], unique=False)
    op.create_table('production_wo_time_entries',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('entry_type', sa.String(length=20), nullable=False),
    sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('duration_minutes', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('quantity_produced', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_scrapped', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('scrap_reason', scrapreason_enum, nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['work_order_id'], ['production_work_orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wo_time', 'production_wo_time_entries', ['tenant_id', 'work_order_id', 'start_time'], unique=False)
    op.create_index(op.f('ix_production_wo_time_entries_tenant_id'), 'production_wo_time_entries', ['tenant_id'], unique=False)
    op.create_table('accounting_reconciliation_history',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('entry_line_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reconciliation_type', sa.String(length=50), nullable=False),
    sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('match_details', postgresql.JSON(), nullable=True),
    sa.Column('transaction_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('document_amount', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('difference', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('validated_at', sa.DateTime(), nullable=True),
    sa.Column('is_cancelled', sa.Boolean(), nullable=True),
    sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('cancellation_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['accounting_documents.id'], ),
    sa.ForeignKeyConstraint(['entry_line_id'], ['journal_entry_lines.id'], ),
    sa.ForeignKeyConstraint(['rule_id'], ['accounting_reconciliation_rules.id'], ),
    sa.ForeignKeyConstraint(['transaction_id'], ['accounting_synced_transactions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reconhist_document', 'accounting_reconciliation_history', ['document_id'], unique=False)
    op.create_index('idx_reconhist_tenant', 'accounting_reconciliation_history', ['tenant_id'], unique=False)
    op.create_index('idx_reconhist_transaction', 'accounting_reconciliation_history', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_accounting_reconciliation_history_tenant_id'), 'accounting_reconciliation_history', ['tenant_id'], unique=False)
    op.create_table('inventory_movement_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('movement_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('line_number', sa.Integer(), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('serial_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('from_location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('to_location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['from_location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id'], ),
    sa.ForeignKeyConstraint(['movement_id'], ['inventory_movements.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.ForeignKeyConstraint(['serial_id'], ['inventory_serial_numbers.id'], ),
    sa.ForeignKeyConstraint(['to_location_id'], ['inventory_locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_movement_lines_movement', 'inventory_movement_lines', ['movement_id'], unique=False)
    op.create_index('idx_movement_lines_product', 'inventory_movement_lines', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_movement_lines_tenant', 'inventory_movement_lines', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_movement_lines_tenant_id'), 'inventory_movement_lines', ['tenant_id'], unique=False)
    op.create_table('inventory_picking_lines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('picking_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('quantity_demanded', sa.Numeric(precision=15, scale=4), nullable=False),
    sa.Column('quantity_picked', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('serial_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('is_picked', sa.Boolean(), nullable=True),
    sa.Column('picked_at', sa.DateTime(), nullable=True),
    sa.Column('picked_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ),
    sa.ForeignKeyConstraint(['lot_id'], ['inventory_lots.id'], ),
    sa.ForeignKeyConstraint(['picking_id'], ['inventory_pickings.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
    sa.ForeignKeyConstraint(['serial_id'], ['inventory_serial_numbers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_picking_lines_picking', 'inventory_picking_lines', ['picking_id'], unique=False)
    op.create_index('idx_picking_lines_product', 'inventory_picking_lines', ['tenant_id', 'product_id'], unique=False)
    op.create_index('idx_picking_lines_tenant', 'inventory_picking_lines', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lines_tenant_id'), 'inventory_picking_lines', ['tenant_id'], unique=False)
    op.create_table('maintenance_failures',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('failure_number', sa.String(length=50), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('component_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('failure_type', failuretype_enum, nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('symptoms', sa.Text(), nullable=True),
    sa.Column('failure_date', sa.DateTime(), nullable=False),
    sa.Column('detected_date', sa.DateTime(), nullable=True),
    sa.Column('reported_date', sa.DateTime(), nullable=True),
    sa.Column('resolved_date', sa.DateTime(), nullable=True),
    sa.Column('production_stopped', sa.Boolean(), nullable=True),
    sa.Column('downtime_hours', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('production_loss_units', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('estimated_cost_impact', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('reported_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('resolution', sa.Text(), nullable=True),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('corrective_action', sa.Text(), nullable=True),
    sa.Column('preventive_action', sa.Text(), nullable=True),
    sa.Column('meter_reading', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('attachments', postgresql.JSONB(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ),
    sa.ForeignKeyConstraint(['component_id'], ['maintenance_asset_components.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_failure_asset', 'maintenance_failures', ['tenant_id', 'asset_id'], unique=False)
    op.create_index('idx_failure_date', 'maintenance_failures', ['tenant_id', 'failure_date'], unique=False)
    op.create_index('idx_failure_tenant', 'maintenance_failures', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_failures_tenant_id'), 'maintenance_failures', ['tenant_id'], unique=False)
    op.create_table('maintenance_failure_causes',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('failure_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('cause_category', sa.String(length=100), nullable=True),
    sa.Column('cause_description', sa.Text(), nullable=False),
    sa.Column('is_root_cause', sa.Boolean(), nullable=True),
    sa.Column('probability', sa.String(length=20), nullable=True),
    sa.Column('recommended_action', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['failure_id'], ['maintenance_failures.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_failure_cause_failure', 'maintenance_failure_causes', ['failure_id'], unique=False)
    op.create_index('idx_failure_cause_tenant', 'maintenance_failure_causes', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_failure_causes_tenant_id'), 'maintenance_failure_causes', ['tenant_id'], unique=False)
    op.create_table('maintenance_work_orders',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('wo_number', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('maintenance_type', maintenancetype_enum, nullable=False),
    sa.Column('priority', workorderpriority_enum, nullable=True),
    sa.Column('status', maintenanceworkorderstatus_enum, nullable=True),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('component_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=True),
    sa.Column('source_reference', sa.String(length=100), nullable=True),
    sa.Column('maintenance_plan_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('failure_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('request_date', sa.DateTime(), nullable=True),
    sa.Column('request_description', sa.Text(), nullable=True),
    sa.Column('scheduled_start_date', sa.DateTime(), nullable=True),
    sa.Column('scheduled_end_date', sa.DateTime(), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('actual_start_date', sa.DateTime(), nullable=True),
    sa.Column('actual_end_date', sa.DateTime(), nullable=True),
    sa.Column('downtime_hours', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('external_vendor_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('work_instructions', sa.Text(), nullable=True),
    sa.Column('safety_precautions', sa.Text(), nullable=True),
    sa.Column('tools_required', postgresql.JSONB(), nullable=True),
    sa.Column('certifications_required', postgresql.JSONB(), nullable=True),
    sa.Column('location_description', sa.String(length=200), nullable=True),
    sa.Column('completion_notes', sa.Text(), nullable=True),
    sa.Column('completed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('verification_required', sa.Boolean(), nullable=True),
    sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('verified_date', sa.DateTime(), nullable=True),
    sa.Column('estimated_labor_hours', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('estimated_labor_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('estimated_parts_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('estimated_other_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_labor_hours', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('actual_labor_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_parts_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('actual_other_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('meter_reading_end', sa.Numeric(precision=15, scale=4), nullable=True),
    sa.Column('attachments', postgresql.JSONB(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['maintenance_assets.id'], ),
    sa.ForeignKeyConstraint(['component_id'], ['maintenance_asset_components.id'], ),
    sa.ForeignKeyConstraint(['failure_id'], ['maintenance_failures.id'], ),
    sa.ForeignKeyConstraint(['maintenance_plan_id'], ['maintenance_plans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wo_asset', 'maintenance_work_orders', ['tenant_id', 'asset_id'], unique=False)
    op.create_index('idx_wo_number', 'maintenance_work_orders', ['tenant_id', 'wo_number'], unique=False)
    op.create_index('idx_wo_priority', 'maintenance_work_orders', ['tenant_id', 'priority'], unique=False)
    op.create_index('idx_wo_scheduled', 'maintenance_work_orders', ['tenant_id', 'scheduled_start_date'], unique=False)
    op.create_index('idx_wo_status', 'maintenance_work_orders', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_wo_tenant', 'maintenance_work_orders', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_maintenance_work_orders_tenant_id'), 'maintenance_work_orders', ['tenant_id'], unique=False)
    op.create_table('maintenance_part_requests',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('request_number', sa.String(length=50), nullable=False),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('spare_part_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('part_description', sa.String(length=300), nullable=False),
    sa.Column('quantity_requested', sa.Numeric(precision=12, scale=3), nullable=False),
    sa.Column('quantity_approved', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('quantity_issued', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('unit', sa.String(length=50), nullable=True),
    sa.Column('priority', workorderpriority_enum, nullable=True),
    sa.Column('required_date', sa.Date(), nullable=True),
    sa.Column('status', partrequeststatus_enum, nullable=True),
    sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('request_date', sa.DateTime(), nullable=True),
    sa.Column('request_reason', sa.Text(), nullable=True),
    sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('approved_date', sa.DateTime(), nullable=True),
    sa.Column('issued_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('issued_date', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['spare_part_id'], ['maintenance_spare_parts.id'], ),
    sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_part_req_tenant', 'maintenance_part_requests', ['tenant_id'], unique=False)
    op.create_index('idx_part_req_wo', 'maintenance_part_requests', ['work_order_id'], unique=False)
    op.create_index(op.f('ix_maintenance_part_requests_tenant_id'), 'maintenance_part_requests', ['tenant_id'], unique=False)
    op.create_table('maintenance_wo_labor',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('technician_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('technician_name', sa.String(length=200), nullable=True),
    sa.Column('work_date', sa.Date(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('hours_worked', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.Column('overtime_hours', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('labor_type', sa.String(length=50), nullable=True),
    sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('work_description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wo_labor_tenant', 'maintenance_wo_labor', ['tenant_id'], unique=False)
    op.create_index('idx_wo_labor_wo', 'maintenance_wo_labor', ['work_order_id'], unique=False)
    op.create_index(op.f('ix_maintenance_wo_labor_tenant_id'), 'maintenance_wo_labor', ['tenant_id'], unique=False)
    op.create_table('maintenance_wo_parts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('spare_part_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('part_code', sa.String(length=100), nullable=True),
    sa.Column('part_description', sa.String(length=300), nullable=False),
    sa.Column('quantity_planned', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('quantity_used', sa.Numeric(precision=12, scale=3), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('total_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=True),
    sa.Column('source_reference', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['spare_part_id'], ['maintenance_spare_parts.id'], ),
    sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wo_part_tenant', 'maintenance_wo_parts', ['tenant_id'], unique=False)
    op.create_index('idx_wo_part_wo', 'maintenance_wo_parts', ['work_order_id'], unique=False)
    op.create_index(op.f('ix_maintenance_wo_parts_tenant_id'), 'maintenance_wo_parts', ['tenant_id'], unique=False)
    op.create_table('maintenance_wo_tasks',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', sa.String(length=50), nullable=False),
    sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('plan_task_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('estimated_minutes', sa.Integer(), nullable=True),
    sa.Column('actual_minutes', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('completed_date', sa.DateTime(), nullable=True),
    sa.Column('completed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('result', sa.Text(), nullable=True),
    sa.Column('issues_found', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['plan_task_id'], ['maintenance_plan_tasks.id'], ),
    sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_wo_task_tenant', 'maintenance_wo_tasks', ['tenant_id'], unique=False)
    op.create_index('idx_wo_task_wo', 'maintenance_wo_tasks', ['work_order_id'], unique=False)
    op.create_index(op.f('ix_maintenance_wo_tasks_tenant_id'), 'maintenance_wo_tasks', ['tenant_id'], unique=False)
    op.drop_index('idx_check_results_category', table_name='qc_check_results')
    op.drop_index('idx_check_results_status', table_name='qc_check_results')
    op.drop_index('idx_check_results_validation', table_name='qc_check_results')
    op.drop_index('ix_qc_check_results_tenant_id', table_name='qc_check_results')
    op.drop_table('qc_check_results')
    op.drop_index('idx_module_registry_status', table_name='qc_module_registry')
    op.drop_index('idx_module_registry_tenant_code', table_name='qc_module_registry')
    op.drop_index('ix_qc_module_registry_tenant_id', table_name='qc_module_registry')
    op.drop_table('qc_module_registry')
    op.drop_index('idx_qc_dashboards_tenant_owner', table_name='qc_dashboards')
    op.drop_index('ix_qc_dashboards_tenant_id', table_name='qc_dashboards')
    op.drop_table('qc_dashboards')
    op.drop_index('idx_qc_alerts_severity', table_name='qc_alerts')
    op.drop_index('idx_qc_alerts_tenant_unresolved', table_name='qc_alerts')
    op.drop_index('ix_qc_alerts_tenant_id', table_name='qc_alerts')
    op.drop_table('qc_alerts')
    op.drop_index('idx_validations_status', table_name='qc_validations')
    op.drop_index('idx_validations_tenant_module', table_name='qc_validations')
    op.drop_index('ix_qc_validations_tenant_id', table_name='qc_validations')
    op.drop_table('qc_validations')
    op.drop_index('idx_system_settings_id', table_name='system_settings')
    op.drop_table('system_settings')
    op.drop_index('idx_qc_rules_category', table_name='qc_rules')
    op.drop_index('idx_qc_rules_tenant_code', table_name='qc_rules')
    op.drop_index('ix_qc_rules_tenant_id', table_name='qc_rules')
    op.drop_table('qc_rules')
    op.drop_index('idx_test_runs_tenant_module', table_name='qc_test_runs')
    op.drop_index('idx_test_runs_type', table_name='qc_test_runs')
    op.drop_index('ix_qc_test_runs_tenant_id', table_name='qc_test_runs')
    op.drop_table('qc_test_runs')
    op.drop_index('idx_qc_templates_tenant_code', table_name='qc_templates')
    op.drop_index('ix_qc_templates_tenant_id', table_name='qc_templates')
    op.drop_table('qc_templates')
    op.drop_index('idx_qc_metrics_module', table_name='qc_metrics')
    op.drop_index('idx_qc_metrics_tenant_date', table_name='qc_metrics')
    op.drop_index('ix_qc_metrics_tenant_id', table_name='qc_metrics')
    op.drop_table('qc_metrics')
    op.drop_constraint('fk_finding_capa', 'quality_audit_findings', type_='foreignkey')
    op.drop_constraint('fk_cert_audit_quality_audit', 'quality_certification_audits', type_='foreignkey')
    op.drop_constraint('fk_qc_template', 'quality_controls', type_='foreignkey')
    op.drop_constraint('fk_qc_nc', 'quality_controls', type_='foreignkey')
    op.drop_constraint('fk_claim_capa', 'quality_customer_claims', type_='foreignkey')
    op.drop_constraint('fk_claim_nc', 'quality_customer_claims', type_='foreignkey')
    op.drop_constraint('fk_nc_capa', 'quality_non_conformances', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('fk_nc_capa', 'quality_non_conformances', 'quality_capas', ['capa_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_claim_nc', 'quality_customer_claims', 'quality_non_conformances', ['nc_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_claim_capa', 'quality_customer_claims', 'quality_capas', ['capa_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_qc_nc', 'quality_controls', 'quality_non_conformances', ['nc_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_qc_template', 'quality_controls', 'quality_control_templates', ['template_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_cert_audit_quality_audit', 'quality_certification_audits', 'quality_audits', ['quality_audit_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_finding_capa', 'quality_audit_findings', 'quality_capas', ['capa_id'], ['id'], ondelete='SET NULL')
    op.create_table('qc_metrics',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('module_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('metric_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('modules_total', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('modules_validated', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('modules_production', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('modules_failed', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('avg_overall_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('avg_architecture_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('avg_security_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('avg_performance_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('avg_code_quality_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('avg_testing_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('avg_documentation_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('total_tests_run', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_tests_passed', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('avg_coverage', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('total_checks_run', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_checks_passed', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('critical_issues', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('blocker_issues', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('score_trend', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('score_delta', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['module_id'], ['qc_module_registry.id'], name='fk_metric_module', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='qc_metrics_pkey')
    )
    op.create_index('ix_qc_metrics_tenant_id', 'qc_metrics', ['tenant_id'], unique=False)
    op.create_index('idx_qc_metrics_tenant_date', 'qc_metrics', ['tenant_id', 'metric_date'], unique=False)
    op.create_index('idx_qc_metrics_module', 'qc_metrics', ['tenant_id', 'module_id'], unique=False)
    op.create_table('qc_templates',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('rules', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('is_system', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='qc_templates_pkey')
    )
    op.create_index('ix_qc_templates_tenant_id', 'qc_templates', ['tenant_id'], unique=False)
    op.create_index('idx_qc_templates_tenant_code', 'qc_templates', ['tenant_id', 'code'], unique=True)
    op.create_table('qc_test_runs',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('module_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('validation_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('test_type', qctesttype_enum, autoincrement=False, nullable=False),
    sa.Column('test_suite', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('started_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('completed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('duration_seconds', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('status', qccheckstatus_enum, autoincrement=False, nullable=False),
    sa.Column('total_tests', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('passed_tests', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('failed_tests', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('skipped_tests', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('error_tests', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('coverage_percent', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('failed_test_details', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('output_log', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('triggered_by', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('triggered_user', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['module_id'], ['qc_module_registry.id'], name='fk_test_run_module', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['validation_id'], ['qc_validations.id'], name='fk_test_run_validation', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name='qc_test_runs_pkey')
    )
    op.create_index('ix_qc_test_runs_tenant_id', 'qc_test_runs', ['tenant_id'], unique=False)
    op.create_index('idx_test_runs_type', 'qc_test_runs', ['tenant_id', 'test_type'], unique=False)
    op.create_index('idx_test_runs_tenant_module', 'qc_test_runs', ['tenant_id', 'module_id'], unique=False)
    op.create_table('qc_rules',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('category', qcrulecategory_enum, autoincrement=False, nullable=False),
    sa.Column('severity', qcruleseverity_enum, autoincrement=False, nullable=False),
    sa.Column('applies_to_modules', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('applies_to_phases', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('check_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('check_config', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('threshold_value', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('threshold_operator', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('is_system', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='qc_rules_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_qc_rules_tenant_id', 'qc_rules', ['tenant_id'], unique=False)
    op.create_index('idx_qc_rules_tenant_code', 'qc_rules', ['tenant_id', 'code'], unique=True)
    op.create_index('idx_qc_rules_category', 'qc_rules', ['tenant_id', 'category'], unique=False)
    op.create_table('system_settings',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('bootstrap_locked', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False, comment='Once True, initial setup cannot be re-run'),
    sa.Column('maintenance_mode', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False, comment='Platform-wide maintenance mode'),
    sa.Column('maintenance_message', sa.TEXT(), autoincrement=False, nullable=True, comment='Message displayed during maintenance'),
    sa.Column('platform_version', sa.VARCHAR(length=20), server_default=sa.text("'1.0.0'::character varying"), autoincrement=False, nullable=False),
    sa.Column('demo_mode_enabled', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False, comment='Enable demo/cockpit mode'),
    sa.Column('registration_enabled', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False, comment='Allow new tenant registration'),
    sa.Column('global_api_rate_limit', sa.INTEGER(), server_default=sa.text('10000'), autoincrement=False, nullable=False, comment='Platform-wide API rate limit per hour'),
    sa.Column('extra_settings', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='Additional settings as key-value pairs'),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(length=100), autoincrement=False, nullable=True, comment='User/system that made the last change'),
    sa.PrimaryKeyConstraint('id', name='system_settings_pkey')
    )
    op.create_index('idx_system_settings_id', 'system_settings', ['id'], unique=False)
    op.create_table('qc_validations',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('module_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('validation_phase', validationphase_enum, autoincrement=False, nullable=False),
    sa.Column('started_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('completed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('started_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('status', qccheckstatus_enum, autoincrement=False, nullable=False),
    sa.Column('overall_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('total_rules', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('passed_rules', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('failed_rules', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('skipped_rules', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('blocked_rules', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('category_scores', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('report_summary', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('report_details', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['module_id'], ['qc_module_registry.id'], name='fk_validation_module', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='qc_validations_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_qc_validations_tenant_id', 'qc_validations', ['tenant_id'], unique=False)
    op.create_index('idx_validations_tenant_module', 'qc_validations', ['tenant_id', 'module_id'], unique=False)
    op.create_index('idx_validations_status', 'qc_validations', ['tenant_id', 'status'], unique=False)
    op.create_table('qc_alerts',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('module_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('validation_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('check_result_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('alert_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('severity', qcruleseverity_enum, autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('message', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('details', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('is_read', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('is_resolved', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('resolved_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('resolved_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('resolution_notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['check_result_id'], ['qc_check_results.id'], name='fk_alert_check_result', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['module_id'], ['qc_module_registry.id'], name='fk_alert_module', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['validation_id'], ['qc_validations.id'], name='fk_alert_validation', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name='qc_alerts_pkey')
    )
    op.create_index('ix_qc_alerts_tenant_id', 'qc_alerts', ['tenant_id'], unique=False)
    op.create_index('idx_qc_alerts_tenant_unresolved', 'qc_alerts', ['tenant_id', 'is_resolved'], unique=False)
    op.create_index('idx_qc_alerts_severity', 'qc_alerts', ['tenant_id', 'severity'], unique=False)
    op.create_table('qc_dashboards',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('layout', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('widgets', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('filters', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('is_default', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('is_public', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('owner_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('shared_with', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('auto_refresh', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('refresh_interval', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='qc_dashboards_pkey')
    )
    op.create_index('ix_qc_dashboards_tenant_id', 'qc_dashboards', ['tenant_id'], unique=False)
    op.create_index('idx_qc_dashboards_tenant_owner', 'qc_dashboards', ['tenant_id', 'owner_id'], unique=False)
    op.create_table('qc_module_registry',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('module_code', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('module_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('module_version', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('module_type', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('dependencies', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('status', qcmodulestatus_enum, autoincrement=False, nullable=False),
    sa.Column('overall_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('architecture_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('security_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('performance_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('code_quality_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('testing_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('documentation_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('total_checks', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('passed_checks', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('failed_checks', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('blocked_checks', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('last_qc_run', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('validated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('validated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('production_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='qc_module_registry_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_qc_module_registry_tenant_id', 'qc_module_registry', ['tenant_id'], unique=False)
    op.create_index('idx_module_registry_tenant_code', 'qc_module_registry', ['tenant_id', 'module_code'], unique=True)
    op.create_index('idx_module_registry_status', 'qc_module_registry', ['tenant_id', 'status'], unique=False)
    op.create_table('qc_check_results',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tenant_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('validation_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('rule_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('rule_code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('rule_name', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('category', qcrulecategory_enum, autoincrement=False, nullable=False),
    sa.Column('severity', qcruleseverity_enum, autoincrement=False, nullable=False),
    sa.Column('status', qccheckstatus_enum, autoincrement=False, nullable=False),
    sa.Column('executed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('duration_ms', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('expected_value', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('actual_value', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('message', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('error_details', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('recommendation', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('evidence', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['rule_id'], ['qc_rules.id'], name='fk_check_result_rule', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['validation_id'], ['qc_validations.id'], name='fk_check_result_validation', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='qc_check_results_pkey')
    )
    op.create_index('ix_qc_check_results_tenant_id', 'qc_check_results', ['tenant_id'], unique=False)
    op.create_index('idx_check_results_validation', 'qc_check_results', ['validation_id'], unique=False)
    op.create_index('idx_check_results_status', 'qc_check_results', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_check_results_category', 'qc_check_results', ['tenant_id', 'category'], unique=False)
    op.drop_index(op.f('ix_maintenance_wo_tasks_tenant_id'), table_name='maintenance_wo_tasks')
    op.drop_index('idx_wo_task_wo', table_name='maintenance_wo_tasks')
    op.drop_index('idx_wo_task_tenant', table_name='maintenance_wo_tasks')
    op.drop_table('maintenance_wo_tasks')
    op.drop_index(op.f('ix_maintenance_wo_parts_tenant_id'), table_name='maintenance_wo_parts')
    op.drop_index('idx_wo_part_wo', table_name='maintenance_wo_parts')
    op.drop_index('idx_wo_part_tenant', table_name='maintenance_wo_parts')
    op.drop_table('maintenance_wo_parts')
    op.drop_index(op.f('ix_maintenance_wo_labor_tenant_id'), table_name='maintenance_wo_labor')
    op.drop_index('idx_wo_labor_wo', table_name='maintenance_wo_labor')
    op.drop_index('idx_wo_labor_tenant', table_name='maintenance_wo_labor')
    op.drop_table('maintenance_wo_labor')
    op.drop_index(op.f('ix_maintenance_part_requests_tenant_id'), table_name='maintenance_part_requests')
    op.drop_index('idx_part_req_wo', table_name='maintenance_part_requests')
    op.drop_index('idx_part_req_tenant', table_name='maintenance_part_requests')
    op.drop_table('maintenance_part_requests')
    op.drop_index(op.f('ix_maintenance_work_orders_tenant_id'), table_name='maintenance_work_orders')
    op.drop_index('idx_wo_tenant', table_name='maintenance_work_orders')
    op.drop_index('idx_wo_status', table_name='maintenance_work_orders')
    op.drop_index('idx_wo_scheduled', table_name='maintenance_work_orders')
    op.drop_index('idx_wo_priority', table_name='maintenance_work_orders')
    op.drop_index('idx_wo_number', table_name='maintenance_work_orders')
    op.drop_index('idx_wo_asset', table_name='maintenance_work_orders')
    op.drop_table('maintenance_work_orders')
    op.drop_index(op.f('ix_maintenance_failure_causes_tenant_id'), table_name='maintenance_failure_causes')
    op.drop_index('idx_failure_cause_tenant', table_name='maintenance_failure_causes')
    op.drop_index('idx_failure_cause_failure', table_name='maintenance_failure_causes')
    op.drop_table('maintenance_failure_causes')
    op.drop_index(op.f('ix_maintenance_failures_tenant_id'), table_name='maintenance_failures')
    op.drop_index('idx_failure_tenant', table_name='maintenance_failures')
    op.drop_index('idx_failure_date', table_name='maintenance_failures')
    op.drop_index('idx_failure_asset', table_name='maintenance_failures')
    op.drop_table('maintenance_failures')
    op.drop_index(op.f('ix_inventory_picking_lines_tenant_id'), table_name='inventory_picking_lines')
    op.drop_index('idx_picking_lines_tenant', table_name='inventory_picking_lines')
    op.drop_index('idx_picking_lines_product', table_name='inventory_picking_lines')
    op.drop_index('idx_picking_lines_picking', table_name='inventory_picking_lines')
    op.drop_table('inventory_picking_lines')
    op.drop_index(op.f('ix_inventory_movement_lines_tenant_id'), table_name='inventory_movement_lines')
    op.drop_index('idx_movement_lines_tenant', table_name='inventory_movement_lines')
    op.drop_index('idx_movement_lines_product', table_name='inventory_movement_lines')
    op.drop_index('idx_movement_lines_movement', table_name='inventory_movement_lines')
    op.drop_table('inventory_movement_lines')
    op.drop_index(op.f('ix_accounting_reconciliation_history_tenant_id'), table_name='accounting_reconciliation_history')
    op.drop_index('idx_reconhist_transaction', table_name='accounting_reconciliation_history')
    op.drop_index('idx_reconhist_tenant', table_name='accounting_reconciliation_history')
    op.drop_index('idx_reconhist_document', table_name='accounting_reconciliation_history')
    op.drop_table('accounting_reconciliation_history')
    op.drop_index(op.f('ix_production_wo_time_entries_tenant_id'), table_name='production_wo_time_entries')
    op.drop_index('idx_wo_time', table_name='production_wo_time_entries')
    op.drop_table('production_wo_time_entries')
    op.drop_index(op.f('ix_production_scraps_tenant_id'), table_name='production_scraps')
    op.drop_index('idx_scrap_reason', table_name='production_scraps')
    op.drop_index('idx_scrap_product', table_name='production_scraps')
    op.drop_index('idx_scrap_mo', table_name='production_scraps')
    op.drop_table('production_scraps')
    op.drop_index(op.f('ix_production_outputs_tenant_id'), table_name='production_outputs')
    op.drop_index('idx_output_product', table_name='production_outputs')
    op.drop_index('idx_output_mo', table_name='production_outputs')
    op.drop_table('production_outputs')
    op.drop_index(op.f('ix_production_material_consumptions_tenant_id'), table_name='production_material_consumptions')
    op.drop_index('idx_consumption_product', table_name='production_material_consumptions')
    op.drop_index('idx_consumption_mo', table_name='production_material_consumptions')
    op.drop_table('production_material_consumptions')
    op.drop_index(op.f('ix_maintenance_spare_part_stock_tenant_id'), table_name='maintenance_spare_part_stock')
    op.drop_index('idx_spare_stock_tenant', table_name='maintenance_spare_part_stock')
    op.drop_index('idx_spare_stock_part', table_name='maintenance_spare_part_stock')
    op.drop_table('maintenance_spare_part_stock')
    op.drop_index(op.f('ix_maintenance_asset_components_tenant_id'), table_name='maintenance_asset_components')
    op.drop_index('idx_component_tenant', table_name='maintenance_asset_components')
    op.drop_index('idx_component_asset', table_name='maintenance_asset_components')
    op.drop_table('maintenance_asset_components')
    op.drop_index(op.f('ix_inventory_serial_numbers_tenant_id'), table_name='inventory_serial_numbers')
    op.drop_index('idx_serials_tenant', table_name='inventory_serial_numbers')
    op.drop_index('idx_serials_status', table_name='inventory_serial_numbers')
    op.drop_index('idx_serials_product', table_name='inventory_serial_numbers')
    op.drop_table('inventory_serial_numbers')
    op.drop_index(op.f('ix_inventory_count_lines_tenant_id'), table_name='inventory_count_lines')
    op.drop_index('idx_count_lines_tenant', table_name='inventory_count_lines')
    op.drop_index('idx_count_lines_product', table_name='inventory_count_lines')
    op.drop_index('idx_count_lines_count', table_name='inventory_count_lines')
    op.drop_table('inventory_count_lines')
    op.drop_index(op.f('ix_bank_transactions_tenant_id'), table_name='bank_transactions')
    op.drop_index('ix_bank_trans_tenant_type', table_name='bank_transactions')
    op.drop_index('ix_bank_trans_tenant_date', table_name='bank_transactions')
    op.drop_index('ix_bank_trans_tenant_account', table_name='bank_transactions')
    op.drop_table('bank_transactions')
    op.drop_index(op.f('ix_bank_statement_lines_tenant_id'), table_name='bank_statement_lines')
    op.drop_index('ix_bank_lines_tenant_status', table_name='bank_statement_lines')
    op.drop_index('ix_bank_lines_tenant_statement', table_name='bank_statement_lines')
    op.drop_table('bank_statement_lines')
    op.drop_index(op.f('ix_accounting_synced_transactions_tenant_id'), table_name='accounting_synced_transactions')
    op.drop_index('idx_syncedtrans_tenant', table_name='accounting_synced_transactions')
    op.drop_index('idx_syncedtrans_recon', table_name='accounting_synced_transactions')
    op.drop_index('idx_syncedtrans_date', table_name='accounting_synced_transactions')
    op.drop_index('idx_syncedtrans_account', table_name='accounting_synced_transactions')
    op.drop_table('accounting_synced_transactions')
    op.drop_index(op.f('ix_accounting_ocr_results_tenant_id'), table_name='accounting_ocr_results')
    op.drop_index('idx_ocr_tenant_doc', table_name='accounting_ocr_results')
    op.drop_table('accounting_ocr_results')
    op.drop_index(op.f('ix_accounting_auto_entries_tenant_id'), table_name='accounting_auto_entries')
    op.drop_index('idx_autoentry_tenant_review', table_name='accounting_auto_entries')
    op.drop_index('idx_autoentry_tenant_doc', table_name='accounting_auto_entries')
    op.drop_index('idx_autoentry_tenant_confidence', table_name='accounting_auto_entries')
    op.drop_table('accounting_auto_entries')
    op.drop_index(op.f('ix_accounting_alerts_tenant_id'), table_name='accounting_alerts')
    op.drop_index('idx_alert_tenant_unresolved', table_name='accounting_alerts')
    op.drop_index('idx_alert_tenant_type', table_name='accounting_alerts')
    op.drop_index('idx_alert_tenant', table_name='accounting_alerts')
    op.drop_index('idx_alert_entity', table_name='accounting_alerts')
    op.drop_table('accounting_alerts')
    op.drop_index(op.f('ix_accounting_ai_classifications_tenant_id'), table_name='accounting_ai_classifications')
    op.drop_index('idx_aiclass_tenant_doc', table_name='accounting_ai_classifications')
    op.drop_index('idx_aiclass_tenant_confidence', table_name='accounting_ai_classifications')
    op.drop_table('accounting_ai_classifications')
    op.drop_index(op.f('ix_production_work_orders_tenant_id'), table_name='production_work_orders')
    op.drop_index('idx_wo_wc', table_name='production_work_orders')
    op.drop_index('idx_wo_mo', table_name='production_work_orders')
    op.drop_table('production_work_orders')
    op.drop_index(op.f('ix_production_plan_lines_tenant_id'), table_name='production_plan_lines')
    op.drop_index('idx_plan_line_product', table_name='production_plan_lines')
    op.drop_index('idx_plan_line', table_name='production_plan_lines')
    op.drop_table('production_plan_lines')
    op.drop_index(op.f('ix_maintenance_spare_parts_tenant_id'), table_name='maintenance_spare_parts')
    op.drop_index('idx_spare_tenant', table_name='maintenance_spare_parts')
    op.drop_index('idx_spare_code', table_name='maintenance_spare_parts')
    op.drop_table('maintenance_spare_parts')
    op.drop_index(op.f('ix_maintenance_plan_tasks_tenant_id'), table_name='maintenance_plan_tasks')
    op.drop_index('idx_mplan_task_tenant', table_name='maintenance_plan_tasks')
    op.drop_index('idx_mplan_task_plan', table_name='maintenance_plan_tasks')
    op.drop_table('maintenance_plan_tasks')
    op.drop_index(op.f('ix_journal_entry_lines_tenant_id'), table_name='journal_entry_lines')
    op.drop_index('ix_entry_lines_tenant_reconcile', table_name='journal_entry_lines')
    op.drop_index('ix_entry_lines_tenant_entry', table_name='journal_entry_lines')
    op.drop_index('ix_entry_lines_tenant_account', table_name='journal_entry_lines')
    op.drop_table('journal_entry_lines')
    op.drop_index(op.f('ix_inventory_stock_levels_tenant_id'), table_name='inventory_stock_levels')
    op.drop_index('idx_stock_levels_warehouse', table_name='inventory_stock_levels')
    op.drop_index('idx_stock_levels_tenant', table_name='inventory_stock_levels')
    op.drop_index('idx_stock_levels_product', table_name='inventory_stock_levels')
    op.drop_table('inventory_stock_levels')
    op.drop_index(op.f('ix_inventory_replenishment_rules_tenant_id'), table_name='inventory_replenishment_rules')
    op.drop_index('idx_replenishment_tenant', table_name='inventory_replenishment_rules')
    op.drop_index('idx_replenishment_product', table_name='inventory_replenishment_rules')
    op.drop_table('inventory_replenishment_rules')
    op.drop_index(op.f('ix_inventory_lots_tenant_id'), table_name='inventory_lots')
    op.drop_index('idx_lots_tenant', table_name='inventory_lots')
    op.drop_index('idx_lots_status', table_name='inventory_lots')
    op.drop_index('idx_lots_product', table_name='inventory_lots')
    op.drop_index('idx_lots_expiry', table_name='inventory_lots')
    op.drop_table('inventory_lots')
    op.drop_index(op.f('ix_compliance_actions_tenant_id'), table_name='compliance_actions')
    op.drop_index('ix_action_tenant_status', table_name='compliance_actions')
    op.drop_table('compliance_actions')
    op.drop_index(op.f('ix_bank_statements_tenant_id'), table_name='bank_statements')
    op.drop_index('ix_bank_statements_tenant_date', table_name='bank_statements')
    op.drop_index('ix_bank_statements_tenant_account', table_name='bank_statements')
    op.drop_table('bank_statements')
    op.drop_index(op.f('ix_accounting_synced_bank_accounts_tenant_id'), table_name='accounting_synced_bank_accounts')
    op.drop_index('idx_syncedacc_tenant', table_name='accounting_synced_bank_accounts')
    op.drop_index('idx_syncedacc_connection', table_name='accounting_synced_bank_accounts')
    op.drop_table('accounting_synced_bank_accounts')
    op.drop_index(op.f('ix_accounting_documents_tenant_id'), table_name='accounting_documents')
    op.drop_index('idx_accdocs_tenant_type', table_name='accounting_documents')
    op.drop_index('idx_accdocs_tenant_status', table_name='accounting_documents')
    op.drop_index('idx_accdocs_tenant_payment', table_name='accounting_documents')
    op.drop_index('idx_accdocs_tenant_partner', table_name='accounting_documents')
    op.drop_index('idx_accdocs_tenant_date', table_name='accounting_documents')
    op.drop_index('idx_accdocs_tenant', table_name='accounting_documents')
    op.drop_index('idx_accdocs_reference', table_name='accounting_documents')
    op.drop_index('idx_accdocs_file_hash', table_name='accounting_documents')
    op.drop_table('accounting_documents')
    op.drop_index(op.f('ix_production_manufacturing_orders_tenant_id'), table_name='production_manufacturing_orders')
    op.drop_index('idx_mo_tenant', table_name='production_manufacturing_orders')
    op.drop_index('idx_mo_status', table_name='production_manufacturing_orders')
    op.drop_index('idx_mo_product', table_name='production_manufacturing_orders')
    op.drop_index('idx_mo_dates', table_name='production_manufacturing_orders')
    op.drop_table('production_manufacturing_orders')
    op.drop_index(op.f('ix_production_bom_lines_tenant_id'), table_name='production_bom_lines')
    op.drop_index('idx_bom_line', table_name='production_bom_lines')
    op.drop_table('production_bom_lines')
    op.drop_index(op.f('ix_maintenance_plans_tenant_id'), table_name='maintenance_plans')
    op.drop_index('idx_mplan_tenant', table_name='maintenance_plans')
    op.drop_index('idx_mplan_code', table_name='maintenance_plans')
    op.drop_table('maintenance_plans')
    op.drop_index(op.f('ix_maintenance_meter_readings_tenant_id'), table_name='maintenance_meter_readings')
    op.drop_index('idx_reading_tenant', table_name='maintenance_meter_readings')
    op.drop_index('idx_reading_meter', table_name='maintenance_meter_readings')
    op.drop_index('idx_reading_date', table_name='maintenance_meter_readings')
    op.drop_table('maintenance_meter_readings')
    op.drop_index(op.f('ix_journal_entries_tenant_id'), table_name='journal_entries')
    op.drop_index('ix_entries_tenant_status', table_name='journal_entries')
    op.drop_index('ix_entries_tenant_number', table_name='journal_entries')
    op.drop_index('ix_entries_tenant_journal', table_name='journal_entries')
    op.drop_index('ix_entries_tenant_date', table_name='journal_entries')
    op.drop_table('journal_entries')
    op.drop_index(op.f('ix_inventory_products_tenant_id'), table_name='inventory_products')
    op.drop_index('idx_products_tenant', table_name='inventory_products')
    op.drop_index('idx_products_status', table_name='inventory_products')
    op.drop_index('idx_products_sku', table_name='inventory_products')
    op.drop_index('idx_products_category', table_name='inventory_products')
    op.drop_index('idx_products_barcode', table_name='inventory_products')
    op.drop_table('inventory_products')
    op.drop_index(op.f('ix_inventory_movements_tenant_id'), table_name='inventory_movements')
    op.drop_index('idx_movements_type', table_name='inventory_movements')
    op.drop_index('idx_movements_tenant', table_name='inventory_movements')
    op.drop_index('idx_movements_status', table_name='inventory_movements')
    op.drop_index('idx_movements_reference', table_name='inventory_movements')
    op.drop_index('idx_movements_date', table_name='inventory_movements')
    op.drop_table('inventory_movements')
    op.drop_index(op.f('ix_inventory_counts_tenant_id'), table_name='inventory_counts')
    op.drop_index('idx_counts_warehouse', table_name='inventory_counts')
    op.drop_index('idx_counts_tenant', table_name='inventory_counts')
    op.drop_index('idx_counts_status', table_name='inventory_counts')
    op.drop_table('inventory_counts')
    op.drop_index('ix_reports_tenant_type', table_name='financial_reports')
    op.drop_index('ix_reports_tenant_dates', table_name='financial_reports')
    op.drop_index(op.f('ix_financial_reports_tenant_id'), table_name='financial_reports')
    op.drop_table('financial_reports')
    op.drop_index(op.f('ix_compliance_training_completions_tenant_id'), table_name='compliance_training_completions')
    op.drop_index('ix_completion_tenant_user', table_name='compliance_training_completions')
    op.drop_table('compliance_training_completions')
    op.drop_index('ix_gap_tenant_open', table_name='compliance_gaps')
    op.drop_index(op.f('ix_compliance_gaps_tenant_id'), table_name='compliance_gaps')
    op.drop_table('compliance_gaps')
    op.drop_index('ix_finding_tenant_severity', table_name='compliance_audit_findings')
    op.drop_index(op.f('ix_compliance_audit_findings_tenant_id'), table_name='compliance_audit_findings')
    op.drop_table('compliance_audit_findings')
    op.drop_index(op.f('ix_bank_accounts_tenant_id'), table_name='bank_accounts')
    op.drop_index('ix_bank_accounts_tenant_iban', table_name='bank_accounts')
    op.drop_index('ix_bank_accounts_tenant', table_name='bank_accounts')
    op.drop_table('bank_accounts')
    op.drop_index(op.f('ix_production_wc_capacity_tenant_id'), table_name='production_wc_capacity')
    op.drop_index('idx_wc_cap_date', table_name='production_wc_capacity')
    op.drop_table('production_wc_capacity')
    op.drop_index(op.f('ix_production_routing_operations_tenant_id'), table_name='production_routing_operations')
    op.drop_index('idx_routing_op', table_name='production_routing_operations')
    op.drop_table('production_routing_operations')
    op.drop_index(op.f('ix_production_maintenance_schedules_tenant_id'), table_name='production_maintenance_schedules')
    op.drop_index('idx_maint_wc', table_name='production_maintenance_schedules')
    op.drop_index('idx_maint_next', table_name='production_maintenance_schedules')
    op.drop_table('production_maintenance_schedules')
    op.drop_index(op.f('ix_production_bom_tenant_id'), table_name='production_bom')
    op.drop_index('idx_bom_tenant', table_name='production_bom')
    op.drop_index('idx_bom_product', table_name='production_bom')
    op.drop_table('production_bom')
    op.drop_index(op.f('ix_maintenance_kpis_tenant_id'), table_name='maintenance_kpis')
    op.drop_index('idx_mkpi_tenant', table_name='maintenance_kpis')
    op.drop_index('idx_mkpi_period', table_name='maintenance_kpis')
    op.drop_index('idx_mkpi_asset', table_name='maintenance_kpis')
    op.drop_table('maintenance_kpis')
    op.drop_index(op.f('ix_maintenance_asset_meters_tenant_id'), table_name='maintenance_asset_meters')
    op.drop_index('idx_meter_tenant', table_name='maintenance_asset_meters')
    op.drop_index('idx_meter_asset', table_name='maintenance_asset_meters')
    op.drop_table('maintenance_asset_meters')
    op.drop_index(op.f('ix_maintenance_asset_documents_tenant_id'), table_name='maintenance_asset_documents')
    op.drop_index('idx_asset_doc_tenant', table_name='maintenance_asset_documents')
    op.drop_index('idx_asset_doc_asset', table_name='maintenance_asset_documents')
    op.drop_table('maintenance_asset_documents')
    op.drop_index('ix_journals_tenant_type', table_name='journals')
    op.drop_index(op.f('ix_journals_tenant_id'), table_name='journals')
    op.drop_index('ix_journals_tenant_code', table_name='journals')
    op.drop_table('journals')
    op.drop_index(op.f('ix_inventory_valuations_tenant_id'), table_name='inventory_valuations')
    op.drop_index('idx_valuations_warehouse', table_name='inventory_valuations')
    op.drop_index('idx_valuations_tenant', table_name='inventory_valuations')
    op.drop_index('idx_valuations_date', table_name='inventory_valuations')
    op.drop_table('inventory_valuations')
    op.drop_index(op.f('ix_inventory_pickings_tenant_id'), table_name='inventory_pickings')
    op.drop_index('idx_pickings_tenant', table_name='inventory_pickings')
    op.drop_index('idx_pickings_status', table_name='inventory_pickings')
    op.drop_index('idx_pickings_reference', table_name='inventory_pickings')
    op.drop_index('idx_pickings_assigned', table_name='inventory_pickings')
    op.drop_table('inventory_pickings')
    op.drop_index(op.f('ix_inventory_locations_tenant_id'), table_name='inventory_locations')
    op.drop_index('idx_locations_warehouse', table_name='inventory_locations')
    op.drop_index('idx_locations_tenant', table_name='inventory_locations')
    op.drop_index('idx_locations_barcode', table_name='inventory_locations')
    op.drop_table('inventory_locations')
    op.drop_index('ix_fiscal_periods_tenant_year', table_name='fiscal_periods')
    op.drop_index('ix_fiscal_periods_tenant_number', table_name='fiscal_periods')
    op.drop_index(op.f('ix_fiscal_periods_tenant_id'), table_name='fiscal_periods')
    op.drop_table('fiscal_periods')
    op.drop_index(op.f('ix_compliance_trainings_tenant_id'), table_name='compliance_trainings')
    op.drop_table('compliance_trainings')
    op.drop_index('ix_risk_tenant_level', table_name='compliance_risks')
    op.drop_index(op.f('ix_compliance_risks_tenant_id'), table_name='compliance_risks')
    op.drop_table('compliance_risks')
    op.drop_index('ix_requirement_tenant_status', table_name='compliance_requirements')
    op.drop_index(op.f('ix_compliance_requirements_tenant_id'), table_name='compliance_requirements')
    op.drop_table('compliance_requirements')
    op.drop_index(op.f('ix_compliance_policy_acknowledgments_tenant_id'), table_name='compliance_policy_acknowledgments')
    op.drop_index('ix_acknowledgment_tenant_user', table_name='compliance_policy_acknowledgments')
    op.drop_table('compliance_policy_acknowledgments')
    op.drop_index('ix_incident_tenant_status', table_name='compliance_incidents')
    op.drop_index(op.f('ix_compliance_incidents_tenant_id'), table_name='compliance_incidents')
    op.drop_table('compliance_incidents')
    op.drop_index('ix_document_tenant_type', table_name='compliance_documents')
    op.drop_index(op.f('ix_compliance_documents_tenant_id'), table_name='compliance_documents')
    op.drop_table('compliance_documents')
    op.drop_index(op.f('ix_compliance_audits_tenant_id'), table_name='compliance_audits')
    op.drop_index('ix_audit_tenant_status', table_name='compliance_audits')
    op.drop_table('compliance_audits')
    op.drop_index(op.f('ix_compliance_assessments_tenant_id'), table_name='compliance_assessments')
    op.drop_index('ix_assessment_tenant_status', table_name='compliance_assessments')
    op.drop_table('compliance_assessments')
    op.drop_index(op.f('ix_cash_flow_categories_tenant_id'), table_name='cash_flow_categories')
    op.drop_index('ix_cash_categories_tenant_code', table_name='cash_flow_categories')
    op.drop_table('cash_flow_categories')
    op.drop_index(op.f('ix_accounting_email_processing_logs_tenant_id'), table_name='accounting_email_processing_logs')
    op.drop_index('idx_emaillog_tenant', table_name='accounting_email_processing_logs')
    op.drop_index('idx_emaillog_status', table_name='accounting_email_processing_logs')
    op.drop_index('idx_emaillog_inbox', table_name='accounting_email_processing_logs')
    op.drop_table('accounting_email_processing_logs')
    op.drop_index(op.f('ix_accounting_chart_mappings_tenant_id'), table_name='accounting_chart_mappings')
    op.drop_index('idx_chartmap_tenant', table_name='accounting_chart_mappings')
    op.drop_table('accounting_chart_mappings')
    op.drop_index(op.f('ix_accounting_bank_sync_sessions_tenant_id'), table_name='accounting_bank_sync_sessions')
    op.drop_index('idx_banksync_tenant', table_name='accounting_bank_sync_sessions')
    op.drop_index('idx_banksync_status', table_name='accounting_bank_sync_sessions')
    op.drop_index('idx_banksync_connection', table_name='accounting_bank_sync_sessions')
    op.drop_table('accounting_bank_sync_sessions')
    op.drop_index(op.f('ix_users_tenant_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index('idx_users_tenant_id', table_name='users')
    op.drop_index('idx_users_tenant_email', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_treasury_forecasts_tenant_id'), table_name='treasury_forecasts')
    op.drop_index(op.f('ix_treasury_forecasts_id'), table_name='treasury_forecasts')
    op.drop_index('idx_treasury_tenant', table_name='treasury_forecasts')
    op.drop_index('idx_treasury_red', table_name='treasury_forecasts')
    op.drop_index('idx_treasury_created', table_name='treasury_forecasts')
    op.drop_table('treasury_forecasts')
    op.drop_index(op.f('ix_tenants_tenant_id'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_id'), table_name='tenants')
    op.drop_table('tenants')
    op.drop_index(op.f('ix_tenant_usage_tenant_id'), table_name='tenant_usage')
    op.drop_index(op.f('ix_tenant_usage_id'), table_name='tenant_usage')
    op.drop_index(op.f('ix_tenant_usage_date'), table_name='tenant_usage')
    op.drop_table('tenant_usage')
    op.drop_index(op.f('ix_tenant_subscriptions_tenant_id'), table_name='tenant_subscriptions')
    op.drop_index(op.f('ix_tenant_subscriptions_id'), table_name='tenant_subscriptions')
    op.drop_table('tenant_subscriptions')
    op.drop_index(op.f('ix_tenant_settings_tenant_id'), table_name='tenant_settings')
    op.drop_index(op.f('ix_tenant_settings_id'), table_name='tenant_settings')
    op.drop_table('tenant_settings')
    op.drop_index(op.f('ix_tenant_onboarding_tenant_id'), table_name='tenant_onboarding')
    op.drop_index(op.f('ix_tenant_onboarding_id'), table_name='tenant_onboarding')
    op.drop_table('tenant_onboarding')
    op.drop_index(op.f('ix_tenant_modules_tenant_id'), table_name='tenant_modules')
    op.drop_index(op.f('ix_tenant_modules_id'), table_name='tenant_modules')
    op.drop_table('tenant_modules')
    op.drop_index(op.f('ix_tenant_invitations_id'), table_name='tenant_invitations')
    op.drop_index(op.f('ix_tenant_invitations_email'), table_name='tenant_invitations')
    op.drop_table('tenant_invitations')
    op.drop_index(op.f('ix_tenant_events_tenant_id'), table_name='tenant_events')
    op.drop_index(op.f('ix_tenant_events_id'), table_name='tenant_events')
    op.drop_index(op.f('ix_tenant_events_event_type'), table_name='tenant_events')
    op.drop_table('tenant_events')
    op.drop_index(op.f('ix_red_decision_workflows_tenant_id'), table_name='red_decision_workflows')
    op.drop_index(op.f('ix_red_decision_workflows_id'), table_name='red_decision_workflows')
    op.drop_index(op.f('ix_red_decision_workflows_decision_id'), table_name='red_decision_workflows')
    op.drop_index('idx_red_workflow_tenant', table_name='red_decision_workflows')
    op.drop_index('idx_red_workflow_decision_step', table_name='red_decision_workflows')
    op.drop_index('idx_red_workflow_decision', table_name='red_decision_workflows')
    op.drop_table('red_decision_workflows')
    op.drop_index(op.f('ix_red_decision_reports_tenant_id'), table_name='red_decision_reports')
    op.drop_index(op.f('ix_red_decision_reports_id'), table_name='red_decision_reports')
    op.drop_index(op.f('ix_red_decision_reports_decision_id'), table_name='red_decision_reports')
    op.drop_index('idx_report_tenant', table_name='red_decision_reports')
    op.drop_index('idx_report_decision', table_name='red_decision_reports')
    op.drop_table('red_decision_reports')
    op.drop_index(op.f('ix_production_work_centers_tenant_id'), table_name='production_work_centers')
    op.drop_index('idx_wc_tenant', table_name='production_work_centers')
    op.drop_index('idx_wc_status', table_name='production_work_centers')
    op.drop_table('production_work_centers')
    op.drop_index(op.f('ix_production_routings_tenant_id'), table_name='production_routings')
    op.drop_index('idx_routing_tenant', table_name='production_routings')
    op.drop_index('idx_routing_product', table_name='production_routings')
    op.drop_table('production_routings')
    op.drop_index(op.f('ix_production_plans_tenant_id'), table_name='production_plans')
    op.drop_index('idx_plan_tenant', table_name='production_plans')
    op.drop_index('idx_plan_dates', table_name='production_plans')
    op.drop_table('production_plans')
    op.drop_index(op.f('ix_maintenance_contracts_tenant_id'), table_name='maintenance_contracts')
    op.drop_index('idx_mcontract_tenant', table_name='maintenance_contracts')
    op.drop_index('idx_mcontract_code', table_name='maintenance_contracts')
    op.drop_table('maintenance_contracts')
    op.drop_index(op.f('ix_maintenance_assets_tenant_id'), table_name='maintenance_assets')
    op.drop_index('idx_asset_tenant', table_name='maintenance_assets')
    op.drop_index('idx_asset_status', table_name='maintenance_assets')
    op.drop_index('idx_asset_location', table_name='maintenance_assets')
    op.drop_index('idx_asset_code', table_name='maintenance_assets')
    op.drop_index('idx_asset_category', table_name='maintenance_assets')
    op.drop_table('maintenance_assets')
    op.drop_index(op.f('ix_items_tenant_id'), table_name='items')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_index('idx_items_tenant_id', table_name='items')
    op.drop_index('idx_items_tenant_created', table_name='items')
    op.drop_table('items')
    op.drop_index(op.f('ix_inventory_warehouses_tenant_id'), table_name='inventory_warehouses')
    op.drop_index('idx_warehouses_tenant', table_name='inventory_warehouses')
    op.drop_table('inventory_warehouses')
    op.drop_index(op.f('ix_inventory_categories_tenant_id'), table_name='inventory_categories')
    op.drop_index('idx_categories_tenant', table_name='inventory_categories')
    op.drop_index('idx_categories_parent', table_name='inventory_categories')
    op.drop_table('inventory_categories')
    op.drop_index(op.f('ix_fiscal_years_tenant_id'), table_name='fiscal_years')
    op.drop_index('ix_fiscal_years_tenant_dates', table_name='fiscal_years')
    op.drop_index('ix_fiscal_years_tenant_code', table_name='fiscal_years')
    op.drop_table('fiscal_years')
    op.drop_index(op.f('ix_decisions_tenant_id'), table_name='decisions')
    op.drop_index(op.f('ix_decisions_id'), table_name='decisions')
    op.drop_index('idx_decisions_validated', table_name='decisions')
    op.drop_index('idx_decisions_tenant_id', table_name='decisions')
    op.drop_index('idx_decisions_level', table_name='decisions')
    op.drop_index('idx_decisions_entity', table_name='decisions')
    op.drop_table('decisions')
    op.drop_index(op.f('ix_core_audit_journal_user_id'), table_name='core_audit_journal')
    op.drop_index(op.f('ix_core_audit_journal_tenant_id'), table_name='core_audit_journal')
    op.drop_index(op.f('ix_core_audit_journal_id'), table_name='core_audit_journal')
    op.drop_index('idx_core_audit_user_id', table_name='core_audit_journal')
    op.drop_index('idx_core_audit_tenant_user', table_name='core_audit_journal')
    op.drop_index('idx_core_audit_tenant_id', table_name='core_audit_journal')
    op.drop_index('idx_core_audit_created_at', table_name='core_audit_journal')
    op.drop_table('core_audit_journal')
    op.drop_index('ix_report_tenant_type', table_name='compliance_reports')
    op.drop_index(op.f('ix_compliance_reports_tenant_id'), table_name='compliance_reports')
    op.drop_table('compliance_reports')
    op.drop_index('ix_regulation_tenant_type', table_name='compliance_regulations')
    op.drop_index(op.f('ix_compliance_regulations_tenant_id'), table_name='compliance_regulations')
    op.drop_table('compliance_regulations')
    op.drop_index('ix_policy_tenant_active', table_name='compliance_policies')
    op.drop_index(op.f('ix_compliance_policies_tenant_id'), table_name='compliance_policies')
    op.drop_table('compliance_policies')
    op.drop_index('ix_forecasts_tenant_date', table_name='cash_forecasts')
    op.drop_index(op.f('ix_cash_forecasts_tenant_id'), table_name='cash_forecasts')
    op.drop_table('cash_forecasts')
    op.drop_index('ix_accounts_tenant_type', table_name='accounts')
    op.drop_index('ix_accounts_tenant_parent', table_name='accounts')
    op.drop_index(op.f('ix_accounts_tenant_id'), table_name='accounts')
    op.drop_index('ix_accounts_tenant_code', table_name='accounts')
    op.drop_table('accounts')
    op.drop_index(op.f('ix_accounting_user_preferences_tenant_id'), table_name='accounting_user_preferences')
    op.drop_table('accounting_user_preferences')
    op.drop_index('idx_univchart_type', table_name='accounting_universal_chart')
    op.drop_index('idx_univchart_parent', table_name='accounting_universal_chart')
    op.drop_index('idx_univchart_code', table_name='accounting_universal_chart')
    op.drop_table('accounting_universal_chart')
    op.drop_index(op.f('ix_accounting_tax_configurations_tenant_id'), table_name='accounting_tax_configurations')
    op.drop_index('idx_taxconfig_tenant', table_name='accounting_tax_configurations')
    op.drop_index('idx_taxconfig_country', table_name='accounting_tax_configurations')
    op.drop_table('accounting_tax_configurations')
    op.drop_index(op.f('ix_accounting_reconciliation_rules_tenant_id'), table_name='accounting_reconciliation_rules')
    op.drop_index('idx_reconrule_tenant_active', table_name='accounting_reconciliation_rules')
    op.drop_index('idx_reconrule_tenant', table_name='accounting_reconciliation_rules')
    op.drop_table('accounting_reconciliation_rules')
    op.drop_index(op.f('ix_accounting_email_inboxes_tenant_id'), table_name='accounting_email_inboxes')
    op.drop_index('idx_emailinbox_tenant', table_name='accounting_email_inboxes')
    op.drop_table('accounting_email_inboxes')
    op.drop_index(op.f('ix_accounting_dashboard_metrics_tenant_id'), table_name='accounting_dashboard_metrics')
    op.drop_index('idx_dashmetrics_tenant', table_name='accounting_dashboard_metrics')
    op.drop_index('idx_dashmetrics_date', table_name='accounting_dashboard_metrics')
    op.drop_table('accounting_dashboard_metrics')
    op.drop_index(op.f('ix_accounting_bank_connections_tenant_id'), table_name='accounting_bank_connections')
    op.drop_index('idx_bankconn_tenant_status', table_name='accounting_bank_connections')
    op.drop_index('idx_bankconn_tenant', table_name='accounting_bank_connections')
    op.drop_table('accounting_bank_connections')
    # ### end Alembic commands ###
