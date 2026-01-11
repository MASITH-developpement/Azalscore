"""CREATE SYSTEM_SETTINGS TABLE

Revision ID: system_settings_001
Revises: users_password_cols_001
Create Date: 2026-01-11

DESCRIPTION:
============
Migration to create the system_settings table for global platform configuration.
This table stores platform-wide settings that are not tenant-specific.

KEY SETTINGS:
- bootstrap_locked: Prevents re-running initial setup (one-time lock)
- maintenance_mode: Platform-wide maintenance flag
- demo_mode_enabled: Controls demo/cockpit visibility
- registration_enabled: Controls new tenant signup

USAGE:
This table is used by the bootstrap_production.py script to ensure
the initial setup can only run once.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'system_settings_001'
down_revision = 'users_password_cols_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create system_settings table for global platform configuration."""

    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if 'system_settings' in tables:
        print("  [INFO] Table 'system_settings' already exists - skipping creation")
        return

    # Detect if we're using PostgreSQL or SQLite
    dialect = conn.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Use UUID and JSONB
        op.create_table(
            'system_settings',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('bootstrap_locked', sa.Boolean(), nullable=False, server_default='false',
                      comment='Once True, initial setup cannot be re-run'),
            sa.Column('maintenance_mode', sa.Boolean(), nullable=False, server_default='false',
                      comment='Platform-wide maintenance mode'),
            sa.Column('maintenance_message', sa.Text(), nullable=True,
                      comment='Message displayed during maintenance'),
            sa.Column('platform_version', sa.String(20), nullable=False, server_default='1.0.0'),
            sa.Column('demo_mode_enabled', sa.Boolean(), nullable=False, server_default='false',
                      comment='Enable demo/cockpit mode'),
            sa.Column('registration_enabled', sa.Boolean(), nullable=False, server_default='true',
                      comment='Allow new tenant registration'),
            sa.Column('global_api_rate_limit', sa.Integer(), nullable=False, server_default='10000',
                      comment='Platform-wide API rate limit per hour'),
            sa.Column('extra_settings', JSONB(), nullable=True,
                      comment='Additional settings as key-value pairs'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('updated_by', sa.String(100), nullable=True,
                      comment='User/system that made the last change'),
        )
    else:
        # SQLite: Use String for UUID and Text for JSON
        op.create_table(
            'system_settings',
            sa.Column('id', sa.String(36), primary_key=True, nullable=False),
            sa.Column('bootstrap_locked', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('maintenance_mode', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('maintenance_message', sa.Text(), nullable=True),
            sa.Column('platform_version', sa.String(20), nullable=False, server_default='1.0.0'),
            sa.Column('demo_mode_enabled', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('registration_enabled', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('global_api_rate_limit', sa.Integer(), nullable=False, server_default='10000'),
            sa.Column('extra_settings', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('updated_by', sa.String(100), nullable=True),
        )

    # Create index on id
    op.create_index('idx_system_settings_id', 'system_settings', ['id'])

    print("  [OK] Table 'system_settings' created successfully")


def downgrade() -> None:
    """Drop system_settings table."""

    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if 'system_settings' not in tables:
        print("  [INFO] Table 'system_settings' does not exist - skipping drop")
        return

    # Drop index first
    try:
        op.drop_index('idx_system_settings_id', table_name='system_settings')
    except Exception:
        pass

    # Drop table
    op.drop_table('system_settings')

    print("  [OK] Table 'system_settings' dropped successfully")
