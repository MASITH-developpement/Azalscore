"""
AZALS - Module de Reset Database UUID
=====================================

Module reutilisable pour le reset controle de la base de donnees
vers une architecture UUID-only.

ARCHITECTURE DEFINITIVE - SANS DETTE TECHNIQUE
===============================================

VARIABLES D'ENVIRONNEMENT:
    - AZALS_ENV = dev | test | prod
    - DB_AUTO_RESET_ON_VIOLATION = true | false
    - DB_STRICT_UUID = true | false

LOGIQUE DE DEMARRAGE:
    SI violations UUID detectees:
        SI AZALS_ENV != prod ET DB_AUTO_RESET_ON_VIOLATION == true:
            → reset complet du schema public
            → recreation ORM UUID
            → re-scan UUID
        SINON:
            → erreur fatale bloquante

RESULTAT ATTENDU APRES RESET:
    - Colonnes INT/BIGINT detectees : 0
    - Tables affectees : 0
    - Verrou UUID silencieux
    - Application startup complete

INTERDICTIONS ABSOLUES:
    ❌ Pas de migration partielle
    ❌ Pas de SQL manuel (ALTER COLUMN INT → UUID)
    ❌ Pas de contournement du verrou
    ❌ Pas de reset implicite
    ❌ Pas de reset en PRODUCTION

USAGE INTERNE (depuis main.py):
    from app.db.uuid_reset import UUIDComplianceManager
    manager = UUIDComplianceManager(engine, settings)
    manager.ensure_uuid_compliance()

USAGE EXTERNE (script standalone):
    python scripts/reset_database_uuid.py
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Set
from datetime import datetime

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Fichier sentinel pour empecher les resets multiples
# Ce fichier est cree apres un reset reussi
SENTINEL_FILE = Path(".uuid_reset_done")


class UUIDComplianceError(Exception):
    """Erreur de conformite UUID."""
    pass


class UUIDResetBlockedError(Exception):
    """Reset bloque (production ou non autorise)."""
    pass


def is_reset_already_done() -> bool:
    """
    Verifie si un reset UUID a deja ete effectue.

    Returns:
        True si le fichier sentinel existe
    """
    return SENTINEL_FILE.exists()


def mark_reset_done() -> None:
    """
    Cree le fichier sentinel apres un reset reussi.
    """
    timestamp = datetime.now().isoformat()
    SENTINEL_FILE.write_text(
        f"UUID reset completed at {timestamp}\n"
        f"This file prevents duplicate resets.\n"
        f"Delete this file to allow a new reset.\n"
    )
    logger.info(f"[UUID_RESET] Sentinel file created: {SENTINEL_FILE}")
    print(f"[OK] Fichier sentinel cree: {SENTINEL_FILE}")


def clear_reset_sentinel() -> None:
    """
    Supprime le fichier sentinel (pour tests ou reset manuel).
    """
    if SENTINEL_FILE.exists():
        SENTINEL_FILE.unlink()
        logger.info(f"[UUID_RESET] Sentinel file removed: {SENTINEL_FILE}")


class UUIDComplianceManager:
    """
    Gestionnaire de conformite UUID pour la base de donnees.

    Cette classe gere:
    - Detection des violations UUID (colonnes BIGINT/INT)
    - Reset controle de la base (dev/test uniquement)
    - Verification post-reset
    - Blocage en production
    """

    def __init__(self, engine: Engine, settings):
        """
        Initialise le gestionnaire.

        Args:
            engine: Engine SQLAlchemy connecte a PostgreSQL
            settings: Configuration applicative (get_settings())
        """
        self.engine = engine
        self.settings = settings
        self.violations: List[Tuple[str, str, str]] = []
        self.tables_dropped: List[str] = []
        self.reset_performed: bool = False

    @property
    def is_production(self) -> bool:
        """Verifie si on est en production."""
        return self.settings.environment.lower() == 'production'

    @property
    def is_dev_or_test(self) -> bool:
        """Verifie si on est en dev ou test."""
        return self.settings.environment.lower() in ('development', 'test', 'dev')

    @property
    def reset_authorized(self) -> bool:
        """Verifie si le reset est autorise."""
        return (
            self.settings.db_reset_uuid
            and self.is_dev_or_test
            and not self.is_production
        )

    @property
    def auto_reset_enabled(self) -> bool:
        """Verifie si l'auto-reset est active."""
        return (
            self.settings.db_auto_reset_on_violation
            and self.is_dev_or_test
            and not self.is_production
        )

    def detect_violations(self) -> List[Tuple[str, str, str]]:
        """
        Detecte toutes les colonnes identifiants non-UUID.

        Returns:
            Liste de tuples (table_name, column_name, data_type)
        """
        self.violations = []

        query = text("""
            SELECT
                c.table_name,
                c.column_name,
                c.data_type
            FROM information_schema.columns c
            JOIN information_schema.tables t
                ON c.table_name = t.table_name
                AND c.table_schema = t.table_schema
            WHERE c.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
              AND c.data_type IN ('integer', 'bigint')
              AND (c.column_name = 'id' OR c.column_name LIKE '%_id')
            ORDER BY c.table_name, c.column_name
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                self.violations = [(row[0], row[1], row[2]) for row in result]
        except SQLAlchemyError as e:
            logger.warning(f"[UUID_DETECT] Detection echouee: {e}")

        return self.violations

    def get_all_tables(self) -> List[str]:
        """
        Liste toutes les tables du schema public.

        Returns:
            Liste des noms de tables
        """
        query = text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row[0] for row in result]
        except SQLAlchemyError as e:
            logger.error(f"[UUID_RESET] Impossible de lister les tables: {e}")
            return []

    def drop_all_tables(self) -> int:
        """
        Supprime toutes les tables du schema public.

        Returns:
            Nombre de tables supprimees

        Raises:
            UUIDResetBlockedError: Si reset non autorise
        """
        if self.is_production:
            raise UUIDResetBlockedError(
                "ERREUR FATALE: Reset IMPOSSIBLE en production. "
                "Migrez les donnees manuellement ou utilisez un environnement de dev."
            )

        if not self.reset_authorized and not self.auto_reset_enabled:
            raise UUIDResetBlockedError(
                f"Reset non autorise.\n"
                f"Environnement: {self.settings.environment}\n"
                f"db_reset_uuid: {self.settings.db_reset_uuid}\n"
                f"db_auto_reset_on_violation: {self.settings.db_auto_reset_on_violation}\n\n"
                f"Pour autoriser le reset, definissez:\n"
                f"  export AZALS_ENV=dev\n"
                f"  export DB_AUTO_RESET_ON_VIOLATION=true\n"
                f"OU (pour reset manuel):\n"
                f"  export AZALS_DB_RESET_UUID=true"
            )

        tables = self.get_all_tables()
        self.tables_dropped = []

        if not tables:
            logger.info("[UUID_RESET] Aucune table a supprimer")
            return 0

        logger.info(f"[UUID_RESET] Suppression de {len(tables)} tables...")
        print(f"[UUID_RESET] Suppression de {len(tables)} tables du schema public...")

        with self.engine.connect() as conn:
            for table_name in tables:
                try:
                    # Echapper le nom de table
                    safe_name = table_name.replace('"', '""')
                    conn.execute(text(f'DROP TABLE IF EXISTS "{safe_name}" CASCADE'))
                    self.tables_dropped.append(table_name)
                    # Log explicite de chaque suppression
                    print(f"  [DROP] {table_name}")
                    logger.info(f"[DROP] Table supprimee: {table_name}")
                except SQLAlchemyError as e:
                    logger.warning(f"  [WARN] {table_name}: {e}")

            conn.commit()

        logger.info(f"[UUID_RESET] {len(self.tables_dropped)} tables supprimees")
        return len(self.tables_dropped)

    def recreate_from_orm(self) -> int:
        """
        Recree les tables depuis les modeles ORM.

        Returns:
            Nombre de tables creees
        """
        from app.db.base import Base
        from app.db.model_loader import load_all_models, verify_models_loaded

        # Charger tous les modeles
        modules_loaded = load_all_models()
        verify_models_loaded()

        table_count = len(Base.metadata.tables)
        logger.info(f"[UUID_RESET] {modules_loaded} modules, {table_count} tables ORM")

        # Creer les tables
        Base.metadata.create_all(bind=self.engine)

        # Verifier
        created_tables = self.get_all_tables()
        logger.info(f"[UUID_RESET] {len(created_tables)} tables creees")

        return len(created_tables)

    def verify_uuid_compliance(self) -> bool:
        """
        Verifie que toutes les colonnes identifiants sont UUID.

        Returns:
            True si conforme, False sinon
        """
        violations = self.detect_violations()
        return len(violations) == 0

    def ensure_uuid_compliance(self) -> bool:
        """
        Point d'entree principal: garantit la conformite UUID.

        Cette methode:
        1. Detecte les violations
        2. Si violations et auto-reset actif: reset + recreate
        3. Si violations et mode strict: leve une erreur
        4. Sinon: avertissement et continue

        Returns:
            True si conforme apres traitement

        Raises:
            UUIDComplianceError: Si violations detectees et mode strict
            UUIDResetBlockedError: Si reset bloque en production
        """
        violations = self.detect_violations()

        if not violations:
            logger.info("[UUID] Base conforme - aucune violation detectee")
            return True

        violation_count = len(violations)
        tables_affected = len(set(v[0] for v in violations))

        logger.warning(
            f"[UUID_VIOLATION] {violation_count} colonnes BIGINT/INT "
            f"dans {tables_affected} tables"
        )

        # Afficher les violations
        self._print_violations()

        # Production: blocage immediat
        if self.is_production:
            raise UUIDComplianceError(
                f"ERREUR FATALE: {violation_count} violations UUID detectees en PRODUCTION. "
                f"Le demarrage est BLOQUE. Migrez les donnees ou utilisez un env de dev."
            )

        # Dev/Test avec auto-reset
        if self.auto_reset_enabled:
            # VERROU ANTI-DOUBLE RESET : verifier le fichier sentinel
            if is_reset_already_done():
                logger.warning(
                    "[UUID_RESET] Reset deja effectue (sentinel: .uuid_reset_done). "
                    "Supprimez le fichier pour autoriser un nouveau reset."
                )
                print(f"\n{'='*60}")
                print("[UUID_RESET] RESET DEJA EFFECTUE")
                print(f"{'='*60}")
                print(f"Le fichier sentinel '{SENTINEL_FILE}' existe.")
                print(f"Le reset ne sera pas relance.")
                print(f"")
                print(f"Pour forcer un nouveau reset :")
                print(f"  rm {SENTINEL_FILE}")
                print(f"{'='*60}\n")
                # Lever une erreur car la base est toujours legacy
                raise UUIDComplianceError(
                    f"Base LEGACY avec {violation_count} violations. "
                    f"Reset bloque par sentinel. Supprimez {SENTINEL_FILE} pour re-reset."
                )

            logger.warning("[UUID_RESET] Auto-reset active - execution...")
            print(f"\n{'='*60}")
            print("[UUID_RESET] MODE AUTO-RESET ACTIVE")
            print(f"{'='*60}")
            print(f"Environnement: {self.settings.environment}")
            print(f"Tables a supprimer: {tables_affected}")
            print(f"Violations a corriger: {violation_count}")
            print(f"{'='*60}\n")

            self._execute_reset()
            self.reset_performed = True

            # Creer le fichier sentinel apres reset reussi
            mark_reset_done()

            return True

        # Dev/Test avec reset manuel requis
        if self.settings.db_strict_uuid:
            raise UUIDComplianceError(
                self._get_error_message(violation_count)
            )

        # Mode non-strict: warning seulement
        logger.warning(
            "[UUID_WARN] Mode non-strict: demarrage avec violations. "
            "Certaines operations peuvent echouer."
        )
        return False

    def _execute_reset(self) -> None:
        """Execute le reset complet: drop + recreate."""
        # 1. Supprimer toutes les tables
        dropped = self.drop_all_tables()
        print(f"[OK] {dropped} tables supprimees")

        # 2. Recreer depuis ORM
        created = self.recreate_from_orm()
        print(f"[OK] {created} tables creees avec UUID")

        # 3. Verifier conformite post-reset
        if not self.verify_uuid_compliance():
            remaining = len(self.violations)
            raise UUIDComplianceError(
                f"ECHEC: {remaining} violations restantes apres reset. "
                "Verifiez les modeles ORM."
            )

        # 4. Affichage du resultat conforme aux exigences
        print(f"\n{'='*60}")
        print("[UUID_RESET] RESULTAT POST-RESET")
        print(f"{'='*60}")
        print(f"Colonnes INT/BIGINT detectees : 0")
        print(f"Tables affectees : 0")
        print(f"Verrou UUID : ACTIF (silencieux)")
        print(f"{'='*60}\n")

        logger.info("[UUID_RESET] Reset termine avec succes - base conforme UUID")

    def _print_violations(self) -> None:
        """Affiche les violations detectees."""
        print(f"\n{'='*60}")
        print("[UUID] VIOLATIONS DETECTEES")
        print(f"{'='*60}")
        print(f"Colonnes BIGINT/INT: {len(self.violations)}")
        print(f"Tables affectees: {len(set(v[0] for v in self.violations))}")
        print(f"\nExemples:")
        for table, col, dtype in self.violations[:15]:
            print(f"  - {table}.{col}: {dtype}")
        if len(self.violations) > 15:
            print(f"  ... et {len(self.violations) - 15} autres")
        print(f"{'='*60}\n")

    def _get_error_message(self, violation_count: int) -> str:
        """Genere le message d'erreur avec instructions."""
        return (
            f"\n"
            f"{'='*60}\n"
            f"ERREUR FATALE: BASE INCOMPATIBLE UUID\n"
            f"{'='*60}\n"
            f"\n"
            f"{violation_count} colonnes identifiants en BIGINT/INT detectees.\n"
            f"Environnement actuel: {self.settings.environment}\n"
            f"\n"
            f"SOLUTIONS (dev/test uniquement):\n"
            f"\n"
            f"1. Reset automatique (recommande en dev):\n"
            f"   export AZALS_ENV=dev\n"
            f"   export DB_AUTO_RESET_ON_VIOLATION=true\n"
            f"   # Relancez l'application\n"
            f"\n"
            f"2. Reset manuel:\n"
            f"   export AZALS_DB_RESET_UUID=true\n"
            f"   python scripts/reset_database_uuid.py\n"
            f"\n"
            f"3. Desactiver le mode strict (NON RECOMMANDE):\n"
            f"   export DB_STRICT_UUID=false\n"
            f"\n"
            f"IMPORTANT:\n"
            f"- Aucun reset possible en PRODUCTION\n"
            f"- Pas de migration partielle INT → UUID\n"
            f"- Le verrou UUID reste actif apres reset\n"
            f"\n"
            f"{'='*60}\n"
        )


def reset_database_for_uuid(engine: Engine, settings) -> bool:
    """
    Fonction utilitaire pour reset complet de la base.

    Args:
        engine: Engine SQLAlchemy
        settings: Configuration applicative

    Returns:
        True si reset reussi

    Raises:
        UUIDResetBlockedError: Si reset non autorise
    """
    manager = UUIDComplianceManager(engine, settings)
    manager.drop_all_tables()
    manager.recreate_from_orm()
    return manager.verify_uuid_compliance()
