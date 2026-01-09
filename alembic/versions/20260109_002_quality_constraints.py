"""QUALITY CONSTRAINTS - Add Foreign Keys to Quality module tables

Revision ID: quality_constraints_002
Revises: quality_bootstrap_001
Create Date: 2026-01-09

DESCRIPTION:
============
Migration pour ajouter les ForeignKey au module Quality (M7) et QC Central (T4).
- Ajoute TOUTES les ForeignKey internes au module Quality
- Ajoute les ON DELETE appropriés
- Aucune FK vers des tables externes (inventory_products) pour éviter les dépendances circulaires
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'quality_constraints_002'
down_revision = 'quality_bootstrap_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add foreign key constraints to Quality module tables."""

    # ========================================================================
    # MODULE QUALITY (M7) - FOREIGN KEYS INTERNES
    # ========================================================================

    # quality_non_conformances -> quality_capas
    op.create_foreign_key(
        'fk_nc_capa',
        'quality_non_conformances', 'quality_capas',
        ['capa_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_nc_actions -> quality_non_conformances
    op.create_foreign_key(
        'fk_nc_action_nc',
        'quality_nc_actions', 'quality_non_conformances',
        ['nc_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_control_template_items -> quality_control_templates
    op.create_foreign_key(
        'fk_qcti_template',
        'quality_control_template_items', 'quality_control_templates',
        ['template_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_controls -> quality_control_templates
    op.create_foreign_key(
        'fk_qc_template',
        'quality_controls', 'quality_control_templates',
        ['template_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_controls -> quality_non_conformances
    op.create_foreign_key(
        'fk_qc_nc',
        'quality_controls', 'quality_non_conformances',
        ['nc_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_control_lines -> quality_controls
    op.create_foreign_key(
        'fk_qcl_control',
        'quality_control_lines', 'quality_controls',
        ['control_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_control_lines -> quality_control_template_items
    op.create_foreign_key(
        'fk_qcl_template_item',
        'quality_control_lines', 'quality_control_template_items',
        ['template_item_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_audit_findings -> quality_audits
    op.create_foreign_key(
        'fk_finding_audit',
        'quality_audit_findings', 'quality_audits',
        ['audit_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_audit_findings -> quality_capas
    op.create_foreign_key(
        'fk_finding_capa',
        'quality_audit_findings', 'quality_capas',
        ['capa_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_capa_actions -> quality_capas
    op.create_foreign_key(
        'fk_capa_action_capa',
        'quality_capa_actions', 'quality_capas',
        ['capa_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_customer_claims -> quality_non_conformances
    op.create_foreign_key(
        'fk_claim_nc',
        'quality_customer_claims', 'quality_non_conformances',
        ['nc_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_customer_claims -> quality_capas
    op.create_foreign_key(
        'fk_claim_capa',
        'quality_customer_claims', 'quality_capas',
        ['capa_id'], ['id'],
        ondelete='SET NULL'
    )

    # quality_claim_actions -> quality_customer_claims
    op.create_foreign_key(
        'fk_claim_action_claim',
        'quality_claim_actions', 'quality_customer_claims',
        ['claim_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_indicator_measurements -> quality_indicators
    op.create_foreign_key(
        'fk_qim_indicator',
        'quality_indicator_measurements', 'quality_indicators',
        ['indicator_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_certification_audits -> quality_certifications
    op.create_foreign_key(
        'fk_cert_audit_cert',
        'quality_certification_audits', 'quality_certifications',
        ['certification_id'], ['id'],
        ondelete='CASCADE'
    )

    # quality_certification_audits -> quality_audits
    op.create_foreign_key(
        'fk_cert_audit_quality_audit',
        'quality_certification_audits', 'quality_audits',
        ['quality_audit_id'], ['id'],
        ondelete='SET NULL'
    )

    # ========================================================================
    # MODULE QC CENTRAL (T4) - FOREIGN KEYS INTERNES
    # ========================================================================

    # qc_validations -> qc_module_registry
    op.create_foreign_key(
        'fk_validation_module',
        'qc_validations', 'qc_module_registry',
        ['module_id'], ['id'],
        ondelete='CASCADE'
    )

    # qc_check_results -> qc_validations
    op.create_foreign_key(
        'fk_check_result_validation',
        'qc_check_results', 'qc_validations',
        ['validation_id'], ['id'],
        ondelete='CASCADE'
    )

    # qc_check_results -> qc_rules
    op.create_foreign_key(
        'fk_check_result_rule',
        'qc_check_results', 'qc_rules',
        ['rule_id'], ['id'],
        ondelete='SET NULL'
    )

    # qc_test_runs -> qc_module_registry
    op.create_foreign_key(
        'fk_test_run_module',
        'qc_test_runs', 'qc_module_registry',
        ['module_id'], ['id'],
        ondelete='CASCADE'
    )

    # qc_test_runs -> qc_validations
    op.create_foreign_key(
        'fk_test_run_validation',
        'qc_test_runs', 'qc_validations',
        ['validation_id'], ['id'],
        ondelete='SET NULL'
    )

    # qc_metrics -> qc_module_registry
    op.create_foreign_key(
        'fk_metric_module',
        'qc_metrics', 'qc_module_registry',
        ['module_id'], ['id'],
        ondelete='CASCADE'
    )

    # qc_alerts -> qc_module_registry
    op.create_foreign_key(
        'fk_alert_module',
        'qc_alerts', 'qc_module_registry',
        ['module_id'], ['id'],
        ondelete='CASCADE'
    )

    # qc_alerts -> qc_validations
    op.create_foreign_key(
        'fk_alert_validation',
        'qc_alerts', 'qc_validations',
        ['validation_id'], ['id'],
        ondelete='SET NULL'
    )

    # qc_alerts -> qc_check_results
    op.create_foreign_key(
        'fk_alert_check_result',
        'qc_alerts', 'qc_check_results',
        ['check_result_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Drop all foreign key constraints from Quality module tables."""

    # ========================================================================
    # MODULE QC CENTRAL (T4) - DROP FK
    # ========================================================================

    op.drop_constraint('fk_alert_check_result', 'qc_alerts', type_='foreignkey')
    op.drop_constraint('fk_alert_validation', 'qc_alerts', type_='foreignkey')
    op.drop_constraint('fk_alert_module', 'qc_alerts', type_='foreignkey')
    op.drop_constraint('fk_metric_module', 'qc_metrics', type_='foreignkey')
    op.drop_constraint('fk_test_run_validation', 'qc_test_runs', type_='foreignkey')
    op.drop_constraint('fk_test_run_module', 'qc_test_runs', type_='foreignkey')
    op.drop_constraint('fk_check_result_rule', 'qc_check_results', type_='foreignkey')
    op.drop_constraint('fk_check_result_validation', 'qc_check_results', type_='foreignkey')
    op.drop_constraint('fk_validation_module', 'qc_validations', type_='foreignkey')

    # ========================================================================
    # MODULE QUALITY (M7) - DROP FK
    # ========================================================================

    op.drop_constraint('fk_cert_audit_quality_audit', 'quality_certification_audits', type_='foreignkey')
    op.drop_constraint('fk_cert_audit_cert', 'quality_certification_audits', type_='foreignkey')
    op.drop_constraint('fk_qim_indicator', 'quality_indicator_measurements', type_='foreignkey')
    op.drop_constraint('fk_claim_action_claim', 'quality_claim_actions', type_='foreignkey')
    op.drop_constraint('fk_claim_capa', 'quality_customer_claims', type_='foreignkey')
    op.drop_constraint('fk_claim_nc', 'quality_customer_claims', type_='foreignkey')
    op.drop_constraint('fk_capa_action_capa', 'quality_capa_actions', type_='foreignkey')
    op.drop_constraint('fk_finding_capa', 'quality_audit_findings', type_='foreignkey')
    op.drop_constraint('fk_finding_audit', 'quality_audit_findings', type_='foreignkey')
    op.drop_constraint('fk_qcl_template_item', 'quality_control_lines', type_='foreignkey')
    op.drop_constraint('fk_qcl_control', 'quality_control_lines', type_='foreignkey')
    op.drop_constraint('fk_qc_nc', 'quality_controls', type_='foreignkey')
    op.drop_constraint('fk_qc_template', 'quality_controls', type_='foreignkey')
    op.drop_constraint('fk_qcti_template', 'quality_control_template_items', type_='foreignkey')
    op.drop_constraint('fk_nc_action_nc', 'quality_nc_actions', type_='foreignkey')
    op.drop_constraint('fk_nc_capa', 'quality_non_conformances', type_='foreignkey')
