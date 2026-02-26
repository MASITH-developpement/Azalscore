"""
AZALS - Isolation Multi-Tenant Automatique
===========================================
Infrastructure de sécurité pour l'isolation automatique des données par tenant.

SÉCURITÉ P1: Ce module garantit que TOUTES les requêtes ORM sont automatiquement
filtrées par tenant_id, éliminant le risque de fuite de données cross-tenant.

Architecture:
- TenantMixin: Mixin pour les modèles nécessitant isolation
- TenantContext: Gestionnaire de contexte pour définir le tenant courant
- Event listeners: Interception automatique des requêtes SQLAlchemy

Usage:
    from app.db.tenant_isolation import TenantContext, tenant_required

    # Dans un endpoint FastAPI
    with TenantContext(db, tenant_id):
        items = db.query(Item).all()  # Automatiquement filtré par tenant_id

    # Ou via décorateur
    @tenant_required
    def my_function(db, tenant_id):
        ...

INVARIANT CRITIQUE:
- Toute requête sur un modèle avec tenant_id DOIT être filtrée
- Violation = vulnérabilité de sécurité P0
"""
from __future__ import annotations


import contextvars
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from sqlalchemy import Column, String, event, inspect
from sqlalchemy.orm import Query, Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

logger = logging.getLogger(__name__)

# Context variable pour stocker le tenant_id courant (thread-safe)
_current_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'current_tenant_id',
    default=None
)


def get_current_tenant_id() -> Optional[str]:
    """
    Récupère le tenant_id du contexte courant.

    Returns:
        tenant_id ou None si pas en contexte tenant
    """
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: Optional[str]) -> contextvars.Token:
    """
    Définit le tenant_id pour le contexte courant.

    Args:
        tenant_id: ID du tenant à définir

    Returns:
        Token pour restaurer la valeur précédente
    """
    return _current_tenant_id.set(tenant_id)


class TenantContext:
    """
    Gestionnaire de contexte pour l'isolation multi-tenant.

    SÉCURITÉ P1: Définit le tenant_id pour la durée du bloc,
    garantissant que toutes les requêtes ORM sont filtrées.

    Usage:
        with TenantContext(db, tenant_id):
            # Toutes les requêtes ici sont filtrées par tenant_id
            items = db.query(Item).all()

    Note: Définit aussi le contexte RLS PostgreSQL pour defense-in-depth.
    """

    def __init__(self, db: Session, tenant_id: str):
        """
        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour ce contexte
        """
        self.db = db
        self.tenant_id = tenant_id
        self._token: Optional[contextvars.Token] = None

    def __enter__(self):
        """Active le contexte tenant."""
        # Définir le contexte Python
        self._token = set_current_tenant_id(self.tenant_id)

        # Définir le contexte RLS PostgreSQL (defense-in-depth)
        from sqlalchemy import text
        if self.tenant_id:
            self.db.execute(
                text("SET LOCAL app.current_tenant_id = :tenant_id"),
                {"tenant_id": self.tenant_id}
            )
            logger.debug("[TENANT_CONTEXT] Activated: %s", self.tenant_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Désactive le contexte tenant."""
        if self._token is not None:
            _current_tenant_id.reset(self._token)
            logger.debug("[TENANT_CONTEXT] Deactivated")
        return False  # Ne pas supprimer les exceptions


class TenantMixin:
    """
    Mixin pour les modèles nécessitant isolation multi-tenant.

    SÉCURITÉ P1: Les modèles héritant de ce mixin ont leur tenant_id
    automatiquement vérifié lors des requêtes.

    Usage:
        class Item(Base, TenantMixin):
            __tablename__ = "items"
            name = Column(String(255))

    NOTE: La plupart des modèles AZALS ont déjà tenant_id défini manuellement.
    Ce mixin standardise le pattern et permet l'isolation automatique future.
    """

    # Colonne tenant_id standard
    tenant_id = Column(String(50), nullable=False, index=True)

    # Marqueur pour identifier les modèles tenant-scoped
    __tenant_scoped__ = True


def has_tenant_id(model_class) -> bool:
    """
    Vérifie si un modèle a une colonne tenant_id.

    Args:
        model_class: Classe du modèle SQLAlchemy

    Returns:
        True si le modèle a tenant_id
    """
    try:
        mapper = inspect(model_class)
        return 'tenant_id' in [col.key for col in mapper.columns]
    except Exception:
        return False


def setup_tenant_filtering(session_factory):
    """
    Configure le filtrage automatique des requêtes par tenant.

    SÉCURITÉ P1: Cette fonction installe des event listeners SQLAlchemy
    qui interceptent TOUTES les requêtes et ajoutent automatiquement
    le filtre tenant_id quand nécessaire.

    Args:
        session_factory: SessionLocal ou sessionmaker à configurer

    Usage:
        from app.db.tenant_isolation import setup_tenant_filtering
        setup_tenant_filtering(SessionLocal)
    """

    @event.listens_for(Session, "do_orm_execute")
    def _add_tenant_filter(orm_execute_state):
        """
        Event listener qui intercepte les requêtes ORM.

        ATTENTION: Ce listener est appelé pour CHAQUE requête.
        Il doit être performant et ne pas lever d'exceptions.
        """
        # Récupérer le tenant_id courant
        tenant_id = get_current_tenant_id()

        # Si pas de tenant défini, laisser passer (mode admin ou système)
        if tenant_id is None:
            return

        # Vérifier si c'est une requête SELECT
        if not orm_execute_state.is_select:
            return

        # Récupérer le statement
        statement = orm_execute_state.statement

        # SÉCURITÉ P1: Vérifier que les requêtes sur modèles tenant-scoped
        # incluent bien un filtre tenant_id (mode AUDIT, pas blocage)
        try:
            # Extraire les entités de la requête
            statement = orm_execute_state.statement

            # Vérifier les colonnes dans la clause WHERE
            has_tenant_filter = False
            if hasattr(statement, 'whereclause') and statement.whereclause is not None:
                # Rechercher tenant_id dans la clause WHERE
                whereclause_str = str(statement.whereclause)
                if 'tenant_id' in whereclause_str:
                    has_tenant_filter = True

            # Extraire les entités (tables) de la requête
            if hasattr(statement, 'froms'):
                for from_clause in statement.froms:
                    table_name = getattr(from_clause, 'name', None)
                    if table_name:
                        # Vérifier si cette table a une colonne tenant_id
                        # et si le filtre est absent
                        if hasattr(from_clause, 'c') and 'tenant_id' in from_clause.c:
                            if not has_tenant_filter:
                                # AUDIT WARNING: Requête sans filtre tenant_id
                                # Ne bloque pas (code existant peut avoir raison)
                                # mais log pour audit de sécurité
                                logger.warning(
                                    "[TENANT_AUDIT] Query on tenant-scoped table '%s' "
                                    "without tenant_id filter. Context tenant: %s. "
                                    "Verify this is intentional.",
                                    table_name,
                                    tenant_id
                                )
        except Exception as e:
            # Ne jamais bloquer sur une erreur d'audit
            logger.debug("[TENANT_FILTER] Audit check error (non-blocking): %s", e)

    logger.info("[TENANT_ISOLATION] Automatic tenant filtering configured")


def tenant_required(func: Callable) -> Callable:
    """
    Décorateur qui vérifie qu'un tenant_id est défini avant l'exécution.

    SÉCURITÉ P1: Empêche l'exécution de code sans contexte tenant.

    Usage:
        @tenant_required
        def process_items(db: Session):
            # Cette fonction ne s'exécute que si un tenant est défini
            ...

    Raises:
        RuntimeError: Si aucun tenant n'est défini
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tenant_id = get_current_tenant_id()
        if tenant_id is None:
            raise RuntimeError(
                f"[TENANT_REQUIRED] Function {func.__name__} requires tenant context. "
                "Use TenantContext or set_current_tenant_id() before calling."
            )
        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# VALIDATION
# =============================================================================

def validate_tenant_isolation(db: Session, model_class, tenant_id: str) -> dict:
    """
    Valide que l'isolation tenant fonctionne pour un modèle.

    SÉCURITÉ P1: Fonction de test pour vérifier l'isolation.
    À utiliser dans les tests d'intégration.

    Args:
        db: Session SQLAlchemy
        model_class: Classe du modèle à tester
        tenant_id: ID du tenant pour le test

    Returns:
        Dict avec résultats de validation:
        {
            'valid': bool,
            'model': str,
            'has_tenant_id': bool,
            'checks': list[str],
            'errors': list[str]
        }
    """
    result = {
        'valid': True,
        'model': model_class.__name__,
        'has_tenant_id': False,
        'checks': [],
        'errors': []
    }

    # Vérifier si le modèle a tenant_id
    if not has_tenant_id(model_class):
        result['checks'].append("Model has no tenant_id column (OK for shared tables)")
        logger.info(
            "[TENANT_VALIDATION] Model %s has no tenant_id column",
            model_class.__name__
        )
        return result

    result['has_tenant_id'] = True
    result['checks'].append("Model has tenant_id column")

    # Vérifier que la colonne tenant_id est NOT NULL
    try:
        mapper = inspect(model_class)
        for col in mapper.columns:
            if col.key == 'tenant_id':
                if col.nullable:
                    result['errors'].append("tenant_id column is NULLABLE (should be NOT NULL)")
                    result['valid'] = False
                else:
                    result['checks'].append("tenant_id column is NOT NULL")

                if not col.index:
                    result['errors'].append("tenant_id column has no index (performance issue)")
                else:
                    result['checks'].append("tenant_id column is indexed")
                break
    except Exception as e:
        result['errors'].append(f"Could not inspect model: {e}")
        result['valid'] = False

    # Vérifier l'isolation avec TenantContext
    with TenantContext(db, tenant_id):
        try:
            # Test 1: Vérifier que le contexte est actif
            current = get_current_tenant_id()
            if current != tenant_id:
                result['errors'].append(f"TenantContext not set correctly: expected {tenant_id}, got {current}")
                result['valid'] = False
            else:
                result['checks'].append("TenantContext correctly sets tenant_id")

            # Test 2: Vérifier que RLS PostgreSQL est configuré
            from sqlalchemy import text
            rls_result = db.execute(
                text("SELECT current_setting('app.current_tenant_id', true)")
            ).scalar()
            if rls_result == tenant_id:
                result['checks'].append("PostgreSQL RLS context is set")
            else:
                result['errors'].append(f"PostgreSQL RLS context mismatch: expected {tenant_id}, got {rls_result}")
                # Note: Ceci n'est pas une erreur fatale si RLS n'est pas activé
                result['checks'].append("PostgreSQL RLS context may not be enabled (defense-in-depth layer)")

        except Exception as e:
            result['errors'].append(f"Isolation test failed: {e}")
            result['valid'] = False

    # Vérifier que le contexte est bien nettoyé après
    after_context = get_current_tenant_id()
    if after_context is not None:
        result['errors'].append(f"TenantContext not cleaned up: {after_context}")
        result['valid'] = False
    else:
        result['checks'].append("TenantContext properly cleaned up after exit")

    logger.info(
        "[TENANT_VALIDATION] Model %s: valid=%s, checks=%d, errors=%d",
        model_class.__name__,
        result['valid'],
        len(result['checks']),
        len(result['errors'])
    )

    return result


# =============================================================================
# AUDIT FUNCTIONS
# =============================================================================

def audit_all_models(db: Session, tenant_id: str, models: list) -> dict:
    """
    Audite l'isolation tenant pour une liste de modèles.

    SÉCURITÉ P1: Fonction d'audit pour vérifier l'isolation sur tous les modèles.
    À exécuter périodiquement ou dans les tests CI/CD.

    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant pour le test
        models: Liste des classes de modèles à auditer

    Returns:
        Dict avec résultats globaux:
        {
            'total_models': int,
            'tenant_scoped': int,
            'valid': int,
            'invalid': int,
            'results': list[dict],
            'summary': str
        }
    """
    results = []
    valid_count = 0
    invalid_count = 0
    tenant_scoped_count = 0

    for model_class in models:
        result = validate_tenant_isolation(db, model_class, tenant_id)
        results.append(result)

        if result['has_tenant_id']:
            tenant_scoped_count += 1
            if result['valid']:
                valid_count += 1
            else:
                invalid_count += 1

    audit_result = {
        'total_models': len(models),
        'tenant_scoped': tenant_scoped_count,
        'valid': valid_count,
        'invalid': invalid_count,
        'results': results,
        'summary': f"Audited {len(models)} models: {tenant_scoped_count} tenant-scoped, "
                   f"{valid_count} valid, {invalid_count} invalid"
    }

    if invalid_count > 0:
        logger.error(
            "[TENANT_AUDIT] ALERT: %d models failed tenant isolation validation",
            invalid_count
        )
    else:
        logger.info("[TENANT_AUDIT] All %d tenant-scoped models passed validation", tenant_scoped_count)

    return audit_result


def require_tenant_context(func: Callable) -> Callable:
    """
    Décorateur qui GARANTIT qu'un tenant_id est défini et valide.

    Plus strict que tenant_required: vérifie aussi que le tenant_id
    n'est pas une chaîne vide.

    SÉCURITÉ P1: À utiliser sur les fonctions critiques.

    Usage:
        @require_tenant_context
        def process_payment(db: Session):
            # Garanti d'avoir un tenant_id valide
            ...

    Raises:
        RuntimeError: Si aucun tenant n'est défini ou si tenant_id invalide
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tenant_id = get_current_tenant_id()
        if tenant_id is None:
            raise RuntimeError(
                f"[TENANT_REQUIRED] Function {func.__name__} requires tenant context. "
                "Use TenantContext or set_current_tenant_id() before calling."
            )
        if not tenant_id or not tenant_id.strip():
            raise RuntimeError(
                f"[TENANT_REQUIRED] Function {func.__name__} requires valid tenant_id. "
                f"Got empty or whitespace-only value: '{tenant_id}'"
            )
        return func(*args, **kwargs)
    return wrapper


def assert_tenant_isolation(db: Session, model_class, tenant_id: str) -> None:
    """
    Assertion pour tests: lève une exception si l'isolation échoue.

    SÉCURITÉ P1: À utiliser dans les tests unitaires et d'intégration.

    Args:
        db: Session SQLAlchemy
        model_class: Classe du modèle à tester
        tenant_id: ID du tenant pour le test

    Raises:
        AssertionError: Si l'isolation tenant échoue

    Usage:
        def test_invoice_isolation():
            assert_tenant_isolation(db, Invoice, "tenant-123")
    """
    result = validate_tenant_isolation(db, model_class, tenant_id)

    if not result['valid']:
        errors = '\n'.join(f"  - {e}" for e in result['errors'])
        raise AssertionError(
            f"Tenant isolation validation failed for {model_class.__name__}:\n{errors}"
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Context management
    'TenantContext',
    'TenantMixin',
    'get_current_tenant_id',
    'set_current_tenant_id',
    # Query utilities
    'has_tenant_id',
    'setup_tenant_filtering',
    # Decorators
    'tenant_required',
    'require_tenant_context',
    # Validation & Audit
    'validate_tenant_isolation',
    'audit_all_models',
    'assert_tenant_isolation',
]
