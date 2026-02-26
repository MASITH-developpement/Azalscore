"""Ajouter champs planification aux configs Odoo.

Revision ID: 20260214_odoo_scheduling
Revises: tenant_modules_enabled
Create Date: 2026-02-14 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260214_odoo_scheduling'
down_revision = 'tenant_modules_enabled'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajouter les colonnes de planification a odoo_connection_configs."""

    # Ajouter la colonne schedule_mode avec ENUM
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE odoo_schedule_mode AS ENUM ('disabled', 'cron', 'interval');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.add_column(
        'odoo_connection_configs',
        sa.Column(
            'schedule_mode',
            sa.Enum('disabled', 'cron', 'interval', name='odoo_schedule_mode'),
            nullable=False,
            server_default='disabled'
        )
    )

    # Ajouter les autres colonnes de planification
    op.add_column(
        'odoo_connection_configs',
        sa.Column('schedule_cron_expression', sa.String(100), nullable=True)
    )

    op.add_column(
        'odoo_connection_configs',
        sa.Column('schedule_interval_minutes', sa.Integer(), nullable=True)
    )

    op.add_column(
        'odoo_connection_configs',
        sa.Column('schedule_timezone', sa.String(50), nullable=False, server_default='Europe/Paris')
    )

    op.add_column(
        'odoo_connection_configs',
        sa.Column('schedule_paused', sa.Boolean(), nullable=False, server_default='false')
    )

    op.add_column(
        'odoo_connection_configs',
        sa.Column('next_scheduled_run', sa.DateTime(), nullable=True)
    )

    op.add_column(
        'odoo_connection_configs',
        sa.Column('last_scheduled_run', sa.DateTime(), nullable=True)
    )

    op.add_column(
        'odoo_connection_configs',
        sa.Column('import_options', sa.JSON(), nullable=True, server_default='{}')
    )

    # Creer l'index pour les queries du scheduler
    op.create_index(
        'idx_odoo_config_schedule',
        'odoo_connection_configs',
        ['is_active', 'schedule_mode', 'schedule_paused'],
        unique=False
    )


def downgrade() -> None:
    """Supprimer les colonnes de planification."""

    op.drop_index('idx_odoo_config_schedule', table_name='odoo_connection_configs')

    op.drop_column('odoo_connection_configs', 'import_options')
    op.drop_column('odoo_connection_configs', 'last_scheduled_run')
    op.drop_column('odoo_connection_configs', 'next_scheduled_run')
    op.drop_column('odoo_connection_configs', 'schedule_paused')
    op.drop_column('odoo_connection_configs', 'schedule_timezone')
    op.drop_column('odoo_connection_configs', 'schedule_interval_minutes')
    op.drop_column('odoo_connection_configs', 'schedule_cron_expression')
    op.drop_column('odoo_connection_configs', 'schedule_mode')

    # Supprimer le type ENUM
    op.execute("DROP TYPE IF EXISTS odoo_schedule_mode")
