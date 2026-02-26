"""Add default_view column to users and iam_users tables

Revision ID: 20260217_users_default_view
Revises: 20260217_france_einvoicing_2026
Create Date: 2026-02-17

Adds default_view column to allow admins to configure user's default landing page.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260217_users_default_view'
down_revision = '20260217_einvoicing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add default_view column to users and iam_users tables."""
    # Add to core users table
    op.add_column(
        'users',
        sa.Column('default_view', sa.String(50), nullable=True,
                  comment='Vue par défaut après connexion (cockpit, admin, saisie, etc.)')
    )

    # Add to IAM users table
    op.add_column(
        'iam_users',
        sa.Column('default_view', sa.String(50), nullable=True,
                  comment='Vue par défaut après connexion (cockpit, admin, saisie, etc.)')
    )


def downgrade() -> None:
    """Remove default_view column from users and iam_users tables."""
    op.drop_column('iam_users', 'default_view')
    op.drop_column('users', 'default_view')
