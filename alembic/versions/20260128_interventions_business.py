"""interventions_business_upgrade - Add DRAFT, BLOQUEE states + blocage columns

Revision ID: interventions_biz_v2
Revises: 20260124_accounting_module
Create Date: 2026-01-28

Adds DRAFT and BLOQUEE enum values to interventionstatut.
Adds motif_blocage, date_blocage, date_deblocage columns to int_interventions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'interventions_biz_v2'
down_revision: Union[str, None] = 'accounting_module_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enum expansion ---
    # PostgreSQL ALTER TYPE to add new values
    op.execute("ALTER TYPE interventionstatut ADD VALUE IF NOT EXISTS 'DRAFT' BEFORE 'A_PLANIFIER'")
    op.execute("ALTER TYPE interventionstatut ADD VALUE IF NOT EXISTS 'BLOQUEE' AFTER 'EN_COURS'")

    # --- New columns for blocage workflow ---
    op.add_column('int_interventions', sa.Column('motif_blocage', sa.Text(), nullable=True))
    op.add_column('int_interventions', sa.Column('date_blocage', sa.DateTime(), nullable=True))
    op.add_column('int_interventions', sa.Column('date_deblocage', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('int_interventions', 'date_deblocage')
    op.drop_column('int_interventions', 'date_blocage')
    op.drop_column('int_interventions', 'motif_blocage')
    # Note: PostgreSQL does not support removing values from enum types
