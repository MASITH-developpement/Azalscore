"""
AZALS - UUID Base Module
========================
Module obligatoire pour tous les modèles ORM.
GARANTIT que TOUTES les PK et FK sont en UUID.

RÈGLE ARCHITECTURALE NON NÉGOCIABLE:
- Toute PK = UUID (jamais Integer/BigInteger)
- Toute FK = UUID (jamais Integer/BigInteger)
- AUCUN autoincrement, AUCUNE Sequence

Usage:
    from app.db import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        # id est automatiquement UUID via UUIDMixin
        # Définir uniquement les autres colonnes

Pour les FK:
    from app.db import uuid_fk_column

    class Child(Base):
        __tablename__ = "children"
        parent_id = uuid_fk_column("parents.id", nullable=False)
"""

import uuid as uuid_module

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declared_attr


def uuid_column(primary_key: bool = False,
                default=None,
                nullable: bool = True,
                index: bool = False,
                unique: bool = False) -> Column:
    """
    Crée une colonne UUID standard.

    Args:
        primary_key: Si True, c'est une clé primaire
        default: Valeur par défaut (uuid.uuid4 par défaut pour PK)
        nullable: Si la colonne peut être NULL
        index: Si un index doit être créé
        unique: Si la valeur doit être unique

    Returns:
        Column UUID correctement configurée
    """
    if primary_key:
        return Column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=default or uuid_module.uuid4,
            nullable=False,
            index=True
        )

    return Column(
        PG_UUID(as_uuid=True),
        default=default,
        nullable=nullable,
        index=index,
        unique=unique
    )


def uuid_fk_column(foreign_key: str,
                   nullable: bool = True,
                   index: bool = True,
                   ondelete: str = "CASCADE") -> Column:
    """
    Crée une colonne UUID avec ForeignKey.

    Args:
        foreign_key: Référence FK (ex: "users.id", "tenants.id")
        nullable: Si la colonne peut être NULL
        index: Si un index doit être créé
        ondelete: Action on delete (CASCADE, SET NULL, etc.)

    Returns:
        Column UUID FK correctement configurée

    Exemples:
        parent_id = uuid_fk_column("parents.id")
        user_id = uuid_fk_column("users.id", nullable=False)
        tenant_id = uuid_fk_column("tenants.id", nullable=False, ondelete="CASCADE")
    """
    return Column(
        PG_UUID(as_uuid=True),
        ForeignKey(foreign_key, ondelete=ondelete),
        nullable=nullable,
        index=index
    )


class UUIDMixin:
    """
    Mixin obligatoire fournissant une PK UUID.

    TOUTES les classes ORM héritant de Base incluent automatiquement ce mixin.
    La colonne 'id' est UUID, jamais Integer/BigInteger.

    Usage:
        class MyModel(Base):
            __tablename__ = "my_table"
            # id est automatiquement fourni par UUIDMixin
            name = Column(String(255))
    """

    @declared_attr
    def id(cls):
        """
        Clé primaire UUID.
        Générée automatiquement avec uuid4.
        """
        return Column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=uuid_module.uuid4,
            nullable=False,
            index=True
        )


class UUIDForeignKey:
    """
    Classe utilitaire pour créer des FK UUID standardisées.

    Usage:
        class Child(Base):
            __tablename__ = "children"
            parent_id = UUIDForeignKey.to("parents.id")
            user_id = UUIDForeignKey.to("users.id", nullable=False)
    """

    @staticmethod
    def to(target: str,
           nullable: bool = True,
           index: bool = True,
           ondelete: str = "CASCADE") -> Column:
        """
        Crée une FK UUID vers la table cible.

        Args:
            target: Table.colonne cible (ex: "users.id")
            nullable: Si la FK peut être NULL
            index: Si un index doit être créé
            ondelete: Action on delete

        Returns:
            Column UUID FK
        """
        return uuid_fk_column(target, nullable=nullable, index=index, ondelete=ondelete)


# Aliases pour compatibilité
UUID = PG_UUID(as_uuid=True)
