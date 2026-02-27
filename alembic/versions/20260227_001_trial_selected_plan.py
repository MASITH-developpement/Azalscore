"""Add selected_plan to trial_registrations

Revision ID: 20260227_001
Revises: 20260225_001_social_publications
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260227_001'
down_revision = '20260225_001_social_publications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'trial_registrations',
        sa.Column('selected_plan', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('trial_registrations', 'selected_plan')
