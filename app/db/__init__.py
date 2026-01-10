"""
AZALS - Database Module
=======================
Module de base de donnees unifie avec support UUID obligatoire.

EXPORTS PRINCIPAUX:
- Base: Classe de base ORM avec UUIDMixin integre
- load_all_models: Fonction pour charger tous les modeles ORM
- verify_models_loaded: Verification que les modeles sont charges

USAGE:
    from app.db import Base, load_all_models
    load_all_models()  # Charger tous les modeles avant operations DB
"""

from app.db.uuid_base import UUIDMixin, UUIDForeignKey, uuid_column, uuid_fk_column
from app.db.base import Base
from app.db.model_loader import (
    load_all_models,
    verify_models_loaded,
    get_loaded_table_count,
    get_loaded_modules
)

__all__ = [
    # Base ORM
    'Base',
    # UUID utilities
    'UUIDMixin',
    'UUIDForeignKey',
    'uuid_column',
    'uuid_fk_column',
    # Model loader
    'load_all_models',
    'verify_models_loaded',
    'get_loaded_table_count',
    'get_loaded_modules'
]
