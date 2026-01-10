"""ADD PASSWORD MANAGEMENT COLUMNS TO USERS TABLE

Revision ID: users_password_cols_001
Revises: quality_constraints_002
Create Date: 2026-01-10

DESCRIPTION:
============
Migration pour ajouter les colonnes de gestion du mot de passe à la table users.
Ces colonnes sont définies dans l'ORM User mais manquantes en base PostgreSQL.

COLONNES AJOUTÉES:
- must_change_password (INTEGER, default 0) : Force le changement au prochain login
- password_changed_at (TIMESTAMP, nullable) : Date du dernier changement de mot de passe

CORRECTION:
Résout l'erreur: psycopg2.errors.UndefinedColumn:
"la colonne users.must_change_password n'existe pas"
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'users_password_cols_001'
down_revision = 'quality_constraints_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add password management columns to users table."""

    # Vérification et ajout de must_change_password
    # Type INTEGER pour compatibilité SQLite (0/1 au lieu de BOOLEAN)
    op.add_column(
        'users',
        sa.Column(
            'must_change_password',
            sa.Integer(),
            nullable=False,
            server_default='0'
        )
    )

    # Ajout de password_changed_at
    op.add_column(
        'users',
        sa.Column(
            'password_changed_at',
            sa.DateTime(),
            nullable=True
        )
    )

    # Index pour optimiser les requêtes sur must_change_password
    op.create_index(
        'idx_users_must_change_password',
        'users',
        ['must_change_password']
    )

    # Index composite tenant_id + must_change_password
    op.create_index(
        'idx_users_tenant_must_change',
        'users',
        ['tenant_id', 'must_change_password']
    )


def downgrade() -> None:
    """Remove password management columns from users table."""

    # Suppression des index
    op.drop_index('idx_users_tenant_must_change', table_name='users')
    op.drop_index('idx_users_must_change_password', table_name='users')

    # Suppression des colonnes
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'must_change_password')
