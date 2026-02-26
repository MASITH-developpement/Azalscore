"""
AZALS - Loader Central des Modeles ORM
======================================
Module CRITIQUE pour le chargement de TOUS les modeles ORM
AVANT toute operation de base de donnees.

OBJECTIF:
- Garantir que Base.metadata.tables contient TOUS les modeles
- Permettre a create_all() de creer TOUTES les tables
- Permettre au verrou UUID de valider TOUTES les tables

USAGE OBLIGATOIRE dans main.py:
    from app.db.model_loader import load_all_models
    load_all_models()  # AVANT create_all() et validation

NE JAMAIS:
- Conditionner cet import
- Importer les modeles "a la volee"
- Bypasser ce loader
"""

import importlib
import logging
import pkgutil

logger = logging.getLogger(__name__)

# Registre des modules charges pour eviter les doublons
_loaded_modules: set[str] = set()
_models_loaded: bool = False


def load_all_models() -> int:
    """
    Charge TOUS les modeles ORM de l'application.

    Cette fonction DOIT etre appelee AVANT:
    - Base.metadata.create_all()
    - Toute validation de schema
    - Tout acces aux tables

    Returns:
        int: Nombre de modules charges

    Raises:
        RuntimeError: Si aucun modele n'est trouve (echec critique)
    """
    global _models_loaded, _loaded_modules

    if _models_loaded:
        logger.debug("Modeles deja charges, skip")
        return len(_loaded_modules)

    # 1. Charger les modeles core en premier
    _load_core_models()

    # 2. Charger tous les modules metier
    _load_module_models()

    # 3. Validation BLOQUANTE
    # Import direct depuis app.db.base pour eviter import circulaire
    from app.db.base import Base
    table_count = len(Base.metadata.tables)

    if table_count == 0:
        raise RuntimeError(
            "ERREUR CRITIQUE: Aucun modele ORM charge. "
            "Verifiez que les modeles heritent de app.db.Base"
        )

    _models_loaded = True

    logger.info(
        "[MODEL_LOADER] Chargement termine: "
        f"{len(_loaded_modules)} modules, {table_count} tables ORM"
    )

    return len(_loaded_modules)


def _load_core_models() -> None:
    """
    Charge les modeles du core (app.core.models) et app.models.
    Ces modeles sont prioritaires (User, Decision, WebsiteVisitor, etc.)
    """
    global _loaded_modules

    try:
        # Import explicite des modeles core
        import app.core.models
        _loaded_modules.add("app.core.models")
        logger.debug("[MODEL_LOADER] Core models charges")
    except ImportError as e:
        logger.warning("[MODEL_LOADER] Impossible de charger core.models: %s", e)

    try:
        # Import explicite des modeles app.models (Website tracking, etc.)
        import app.models
        _loaded_modules.add("app.models")
        logger.debug("[MODEL_LOADER] App models charges (website tracking)")
    except ImportError as e:
        logger.warning("[MODEL_LOADER] Impossible de charger app.models: %s", e)


def _load_module_models() -> None:
    """
    Charge dynamiquement les modules models.py de app.modules.

    IMPORTANT: Utilise glob pour trouver les fichiers models.py
    sans declencher l'import des packages __init__.py.
    Cela evite les erreurs de double definition SQLAlchemy.
    """
    global _loaded_modules
    import os
    import sys

    try:
        import app.modules
        modules_path = app.modules.__path__[0]
    except (ImportError, IndexError) as e:
        logger.error("[MODEL_LOADER] Package app.modules introuvable: %s", e)
        return

    # Scanner les fichiers models.py avec os.walk (pas d'import automatique)
    models_to_load = []
    for root, _dirs, files in os.walk(modules_path):
        if 'models.py' in files:
            # Convertir le chemin en nom de module avec préfixe 'app.'
            rel_path = os.path.relpath(root, os.path.dirname(modules_path))
            module_name = 'app.' + rel_path.replace(os.sep, '.') + '.models'
            models_to_load.append(module_name)

    # Charger chaque module models.py
    for module_name in sorted(models_to_load):
        if module_name in _loaded_modules:
            continue

        # Verifier si deja charge via sys.modules
        if module_name in sys.modules:
            _loaded_modules.add(module_name)
            continue

        try:
            importlib.import_module(module_name)
            _loaded_modules.add(module_name)
            logger.debug("[MODEL_LOADER] Modeles charges: %s", module_name)

        except ImportError as e:
            logger.warning("[MODEL_LOADER] Skip %s: %s", module_name, e)
        except Exception as e:
            logger.error("[MODEL_LOADER] Erreur %s: %s", module_name, e)


def get_loaded_table_count() -> int:
    """
    Retourne le nombre de tables chargees dans Base.metadata.
    Utile pour les diagnostics.
    """
    # Import direct depuis app.db.base pour eviter import circulaire
    from app.db.base import Base
    return len(Base.metadata.tables)


def get_loaded_modules() -> set[str]:
    """
    Retourne l'ensemble des modules charges.
    Utile pour le debug.
    """
    return _loaded_modules.copy()


def verify_models_loaded() -> None:
    """
    Verification BLOQUANTE que les modeles sont charges.
    A appeler apres load_all_models() pour garantie supplementaire.

    Raises:
        AssertionError: Si aucun modele n'est charge
    """
    # Import direct depuis app.db.base pour eviter import circulaire
    from app.db.base import Base

    table_count = len(Base.metadata.tables)

    assert table_count > 0, (
        f"ERREUR CRITIQUE: Base.metadata.tables est vide ({table_count} tables). "
        f"Verifiez que load_all_models() a ete appele et que les modeles "
        f"heritent correctement de app.db.Base"
    )

    # Verification secondaire: au moins les tables core doivent exister
    expected_core_tables = {'users', 'items', 'decisions', 'core_audit_journal'}
    existing_tables = set(Base.metadata.tables.keys())
    missing_core = expected_core_tables - existing_tables

    if missing_core:
        logger.warning(
            "[MODEL_LOADER] Tables core manquantes: %s. "
            "Verifiez app/core/models.py",
            missing_core
        )


# Export pour usage direct
__all__ = [
    'load_all_models',
    'verify_models_loaded',
    'get_loaded_table_count',
    'get_loaded_modules'
]
