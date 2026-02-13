"""UI Events - Table pour audit trail et analytics décisionnel

Revision ID: ui_events_001
Revises: performance_indexes_001
Create Date: 2026-02-13

Table ui_events pour:
- Analyse comportement utilisateurs (module BI)
- Optimisation UX décisionnel
- Tracking adoption modules
- Audit trail complet
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'ui_events_001'
down_revision = 'performance_indexes_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer la table ui_events."""
    op.create_table(
        'ui_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('component', sa.String(200), nullable=True),
        sa.Column('action', sa.String(200), nullable=True),
        sa.Column('target', sa.String(500), nullable=True),
        sa.Column('event_data', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )

    # Index composite pour requêtes fréquentes
    op.create_index(
        'idx_ui_events_tenant_type',
        'ui_events',
        ['tenant_id', 'event_type']
    )
    op.create_index(
        'idx_ui_events_tenant_user',
        'ui_events',
        ['tenant_id', 'user_id']
    )
    op.create_index(
        'idx_ui_events_timestamp',
        'ui_events',
        ['timestamp']
    )


def downgrade() -> None:
    """Supprimer la table ui_events."""
    op.drop_index('idx_ui_events_timestamp', table_name='ui_events')
    op.drop_index('idx_ui_events_tenant_user', table_name='ui_events')
    op.drop_index('idx_ui_events_tenant_type', table_name='ui_events')
    op.drop_table('ui_events')
