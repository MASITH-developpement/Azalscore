"""Add ui_style column to web_user_preferences

Revision ID: 20260220_ui_style
Revises: 20260217_users_default_view
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260220_ui_style'
down_revision = '20260217_users_default_view'
branch_labels = None
depends_on = None


def upgrade():
    # Créer l'enum UIStyle
    ui_style_enum = sa.Enum('CLASSIC', 'MODERN', 'GLASS', name='uistyle')
    ui_style_enum.create(op.get_bind(), checkfirst=True)

    # Ajouter la colonne ui_style avec valeur par défaut CLASSIC
    op.add_column(
        'web_user_preferences',
        sa.Column('ui_style', ui_style_enum, nullable=True, server_default='CLASSIC')
    )


def downgrade():
    # Supprimer la colonne
    op.drop_column('web_user_preferences', 'ui_style')

    # Supprimer l'enum (optionnel, peut échouer si utilisé ailleurs)
    ui_style_enum = sa.Enum('CLASSIC', 'MODERN', 'GLASS', name='uistyle')
    ui_style_enum.drop(op.get_bind(), checkfirst=True)
