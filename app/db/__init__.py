"""
AZALS - Database Module
=======================
Module de base de données unifié avec support UUID obligatoire.
"""

from app.db.uuid_base import UUIDMixin, UUIDForeignKey, uuid_column, uuid_fk_column
from app.db.base import Base

__all__ = ['Base', 'UUIDMixin', 'UUIDForeignKey', 'uuid_column', 'uuid_fk_column']
