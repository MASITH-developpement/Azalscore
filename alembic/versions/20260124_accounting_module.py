"""MODULE ACCOUNTING - Accounting: Create accounting tables

Revision ID: accounting_module_001
Revises: purchases_module_001
Create Date: 2026-01-24

Tables:
- accounting_fiscal_years: Exercices comptables
- accounting_chart_of_accounts: Plan comptable
- accounting_journal_entries: Écritures comptables
- accounting_journal_entry_lines: Lignes d'écritures
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'accounting_module_001'
down_revision = 'purchases_module_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create accounting module tables."""

    # ==========================================================================
    # Table accounting_fiscal_years - Exercices comptables
    # ==========================================================================
    op.create_table(
        'accounting_fiscal_years',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),

        # Période
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),

        # Statut
        sa.Column('status', sa.Enum('OPEN', 'CLOSED', 'ARCHIVED',
                                     name='accounting_fiscalyearstatus'),
                 nullable=False, server_default='OPEN'),

        # Clôture
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['closed_by'], ['users.id']),
        sa.CheckConstraint('end_date > start_date', name='check_fiscal_year_period'),
        sa.Index('idx_accounting_fiscal_years_tenant_id', 'tenant_id'),
        sa.Index('idx_accounting_fiscal_years_code', 'tenant_id', 'code', unique=True),
        sa.Index('idx_accounting_fiscal_years_period', 'start_date', 'end_date'),
        sa.Index('idx_accounting_fiscal_years_status', 'status'),
    )

    # ==========================================================================
    # Table accounting_chart_of_accounts - Plan comptable
    # ==========================================================================
    op.create_table(
        'accounting_chart_of_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('account_number', sa.String(20), nullable=False),
        sa.Column('account_label', sa.String(255), nullable=False),

        # Classification
        sa.Column('account_type', sa.Enum('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE', 'SPECIAL',
                                          name='accounting_accounttype'), nullable=False),
        sa.Column('account_class', sa.String(1), nullable=False),
        sa.Column('parent_account', sa.String(20), nullable=True),

        # Comportement
        sa.Column('is_auxiliary', sa.Boolean(), server_default='false'),
        sa.Column('requires_analytics', sa.Boolean(), server_default='false'),

        # Solde
        sa.Column('opening_balance_debit', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('opening_balance_credit', sa.Numeric(15, 2), server_default='0.00'),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_accounting_coa_tenant_id', 'tenant_id'),
        sa.Index('idx_accounting_coa_account_number', 'tenant_id', 'account_number', unique=True),
        sa.Index('idx_accounting_coa_type', 'account_type'),
        sa.Index('idx_accounting_coa_class', 'account_class'),
    )

    # ==========================================================================
    # Table accounting_journal_entries - Écritures comptables
    # ==========================================================================
    op.create_table(
        'accounting_journal_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('entry_number', sa.String(50), nullable=False),
        sa.Column('piece_number', sa.String(50), nullable=False),

        # Journal
        sa.Column('journal_code', sa.String(10), nullable=False),
        sa.Column('journal_label', sa.String(100), nullable=True),

        # Exercice
        sa.Column('fiscal_year_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Date et période
        sa.Column('entry_date', sa.DateTime(), nullable=False),
        sa.Column('posting_date', sa.DateTime(), nullable=True),
        sa.Column('period', sa.String(7), nullable=False),

        # Libellé
        sa.Column('label', sa.Text(), nullable=False),

        # Origine (traçabilité)
        sa.Column('document_type', sa.String(50), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Statut
        sa.Column('status', sa.Enum('DRAFT', 'POSTED', 'VALIDATED', 'CANCELLED',
                                     name='accounting_entrystatus'),
                 nullable=False, server_default='DRAFT'),

        # Équilibre (calculé depuis lignes)
        sa.Column('total_debit', sa.Numeric(15, 2), server_default='0.00', nullable=False),
        sa.Column('total_credit', sa.Numeric(15, 2), server_default='0.00', nullable=False),
        sa.Column('is_balanced', sa.Boolean(), server_default='false', nullable=False),

        # Currency
        sa.Column('currency', sa.String(3), server_default='EUR'),

        # Validation
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('posted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fiscal_year_id'], ['accounting_fiscal_years.id']),
        sa.ForeignKeyConstraint(['posted_by'], ['users.id']),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id']),
        sa.CheckConstraint('total_debit >= 0', name='check_total_debit_positive'),
        sa.CheckConstraint('total_credit >= 0', name='check_total_credit_positive'),
        sa.Index('idx_accounting_entries_tenant_id', 'tenant_id'),
        sa.Index('idx_accounting_entries_number', 'tenant_id', 'entry_number', unique=True),
        sa.Index('idx_accounting_entries_journal', 'journal_code'),
        sa.Index('idx_accounting_entries_fiscal_year', 'fiscal_year_id'),
        sa.Index('idx_accounting_entries_date', 'entry_date'),
        sa.Index('idx_accounting_entries_period', 'period'),
        sa.Index('idx_accounting_entries_status', 'status'),
        sa.Index('idx_accounting_entries_document', 'document_type', 'document_id'),
    )

    # ==========================================================================
    # Table accounting_journal_entry_lines - Lignes d'écritures
    # ==========================================================================
    op.create_table(
        'accounting_journal_entry_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Relation écriture
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),

        # Compte
        sa.Column('account_number', sa.String(20), nullable=False),
        sa.Column('account_label', sa.String(255), nullable=False),

        # Libellé
        sa.Column('label', sa.Text(), nullable=True),

        # Montants
        sa.Column('debit', sa.Numeric(15, 2), server_default='0.00', nullable=False),
        sa.Column('credit', sa.Numeric(15, 2), server_default='0.00', nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR'),

        # Analytique (optionnel)
        sa.Column('analytics_code', sa.String(50), nullable=True),
        sa.Column('analytics_label', sa.String(255), nullable=True),

        # Auxiliaire (optionnel pour comptes tiers)
        sa.Column('auxiliary_code', sa.String(50), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entry_id'], ['accounting_journal_entries.id'], ondelete='CASCADE'),
        sa.CheckConstraint('debit >= 0', name='check_debit_positive'),
        sa.CheckConstraint('credit >= 0', name='check_credit_positive'),
        sa.CheckConstraint('NOT (debit > 0 AND credit > 0)', name='check_debit_or_credit_only'),
        sa.Index('idx_accounting_entry_lines_tenant_id', 'tenant_id'),
        sa.Index('idx_accounting_entry_lines_entry', 'entry_id'),
        sa.Index('idx_accounting_entry_lines_account', 'account_number'),
        sa.Index('idx_accounting_entry_lines_analytics', 'analytics_code'),
    )


def downgrade() -> None:
    """Drop accounting module tables."""
    op.drop_table('accounting_journal_entry_lines')
    op.drop_table('accounting_journal_entries')
    op.drop_table('accounting_chart_of_accounts')
    op.drop_table('accounting_fiscal_years')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS accounting_fiscalyearstatus')
    op.execute('DROP TYPE IF EXISTS accounting_accounttype')
    op.execute('DROP TYPE IF EXISTS accounting_entrystatus')
