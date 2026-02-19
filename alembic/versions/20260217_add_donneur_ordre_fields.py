"""Add extended fields to int_donneurs_ordre

Revision ID: add_donneur_ordre_fields
Revises:
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_donneur_ordre_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adresse de facturation
    op.add_column('int_donneurs_ordre', sa.Column('adresse_facturation', sa.Text(), nullable=True))
    
    # Facturation et rapports
    op.add_column('int_donneurs_ordre', sa.Column('delai_paiement', sa.Integer(), nullable=True, server_default='30'))
    op.add_column('int_donneurs_ordre', sa.Column('email_rapport', sa.String(255), nullable=True))
    
    # Contact commercial
    op.add_column('int_donneurs_ordre', sa.Column('contact_commercial_nom', sa.String(255), nullable=True))
    op.add_column('int_donneurs_ordre', sa.Column('contact_commercial_email', sa.String(255), nullable=True))
    op.add_column('int_donneurs_ordre', sa.Column('contact_commercial_telephone', sa.String(50), nullable=True))
    
    # Contact comptabilité
    op.add_column('int_donneurs_ordre', sa.Column('contact_comptabilite_nom', sa.String(255), nullable=True))
    op.add_column('int_donneurs_ordre', sa.Column('contact_comptabilite_email', sa.String(255), nullable=True))
    op.add_column('int_donneurs_ordre', sa.Column('contact_comptabilite_telephone', sa.String(50), nullable=True))
    
    # Contact technique
    op.add_column('int_donneurs_ordre', sa.Column('contact_technique_nom', sa.String(255), nullable=True))
    op.add_column('int_donneurs_ordre', sa.Column('contact_technique_email', sa.String(255), nullable=True))
    op.add_column('int_donneurs_ordre', sa.Column('contact_technique_telephone', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('int_donneurs_ordre', 'contact_technique_telephone')
    op.drop_column('int_donneurs_ordre', 'contact_technique_email')
    op.drop_column('int_donneurs_ordre', 'contact_technique_nom')
    op.drop_column('int_donneurs_ordre', 'contact_comptabilite_telephone')
    op.drop_column('int_donneurs_ordre', 'contact_comptabilite_email')
    op.drop_column('int_donneurs_ordre', 'contact_comptabilite_nom')
    op.drop_column('int_donneurs_ordre', 'contact_commercial_telephone')
    op.drop_column('int_donneurs_ordre', 'contact_commercial_email')
    op.drop_column('int_donneurs_ordre', 'contact_commercial_nom')
    op.drop_column('int_donneurs_ordre', 'email_rapport')
    op.drop_column('int_donneurs_ordre', 'delai_paiement')
    op.drop_column('int_donneurs_ordre', 'adresse_facturation')
