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

    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if 'users' not in tables:
        print("  [INFO] Table 'users' not found - skipping password columns migration")
        return

    # Vérifier si les colonnes existent déjà
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'must_change_password' not in columns:
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
    else:
        print("  [INFO] Column 'must_change_password' already exists")

    if 'password_changed_at' not in columns:
        op.add_column(
            'users',
            sa.Column(
                'password_changed_at',
                sa.DateTime(),
                nullable=True
            )
        )
    else:
        print("  [INFO] Column 'password_changed_at' already exists")


def downgrade() -> None:
    """Remove password management columns from users table."""

    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if 'users' not in tables:
        return

    # Suppression des index (avec try/except pour robustesse)
    try:
        op.drop_index('idx_users_tenant_must_change', table_name='users')
    except Exception:
        pass

    try:
        op.drop_index('idx_users_must_change_password', table_name='users')
    except Exception:
        pass

    # Suppression des colonnes
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'password_changed_at' in columns:
        op.drop_column('users', 'password_changed_at')

    if 'must_change_password' in columns:
        op.drop_column('users', 'must_change_password')
