#!/usr/bin/env python3
"""
AZALS - Script de Reset Database UUID
=====================================

Script de nettoyage CONTROLE et SECURISE de la base de donnees
pour migration vers architecture UUID-only.

PREREQUIS OBLIGATOIRE:
    export AZALS_DB_RESET_UUID=true

USAGE:
    python scripts/reset_database_uuid.py

COMPORTEMENT:
    1. Verifie la variable d'environnement AZALS_DB_RESET_UUID
    2. Se connecte a PostgreSQL
    3. Liste toutes les tables du schema public
    4. Supprime les tables une par une avec CASCADE
    5. Log chaque operation
    6. Recree les tables via ORM avec UUID

SECURITE:
    - AUCUNE action sans AZALS_DB_RESET_UUID=true
    - AUCUN bypass des FK
    - AUCUNE modification des extensions
    - Log complet de chaque operation

AVERTISSEMENT:
    CE SCRIPT DETRUIT TOUTES LES DONNEES.
    A utiliser UNIQUEMENT pour migration initiale ou environnement de dev.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Tuple

# Ajouter le repertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DatabaseResetError(Exception):
    """Erreur lors du reset de la base de donnees."""
    pass


class UUIDDatabaseReset:
    """
    Gestionnaire de reset de base de donnees pour migration UUID.

    Cette classe gere le nettoyage controle de la base de donnees
    PostgreSQL pour permettre la recreation avec des UUID.
    """

    ENV_VAR_NAME = "AZALS_DB_RESET_UUID"
    REQUIRED_VALUE = "true"

    def __init__(self):
        self.engine = None
        self.tables_dropped: List[str] = []
        self.tables_created: List[str] = []
        self.start_time = None

    def verify_environment(self) -> bool:
        """
        Verifie que la variable d'environnement de securite est definie.

        Returns:
            bool: True si autorise, False sinon

        Raises:
            DatabaseResetError: Si la variable n'est pas correctement definie
        """
        env_value = os.environ.get(self.ENV_VAR_NAME, "").lower().strip()

        if env_value != self.REQUIRED_VALUE:
            raise DatabaseResetError(
                f"\n"
                f"{'='*60}\n"
                f"ERREUR: Reset de base de donnees NON AUTORISE\n"
                f"{'='*60}\n"
                f"\n"
                f"Pour effectuer un reset UUID de la base de donnees,\n"
                f"vous devez definir la variable d'environnement:\n"
                f"\n"
                f"    export {self.ENV_VAR_NAME}={self.REQUIRED_VALUE}\n"
                f"\n"
                f"ATTENTION: Cette operation DETRUIT TOUTES LES DONNEES.\n"
                f"A utiliser uniquement pour:\n"
                f"  - Migration initiale vers UUID\n"
                f"  - Environnement de developpement\n"
                f"  - CI/CD avec base ephemere\n"
                f"\n"
                f"{'='*60}\n"
            )

        logger.info(f"[SECURITY] Variable {self.ENV_VAR_NAME} validee")
        return True

    def connect(self) -> None:
        """
        Etablit la connexion a PostgreSQL.

        Raises:
            DatabaseResetError: Si la connexion echoue
        """
        try:
            from app.core.config import get_settings
            settings = get_settings()

            self.engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                echo=False
            )

            # Test de connexion
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"[DB] Connecte a PostgreSQL: {version[:50]}...")

        except Exception as e:
            raise DatabaseResetError(f"Impossible de se connecter a PostgreSQL: {e}")

    def get_public_tables(self) -> List[str]:
        """
        Liste toutes les tables du schema public.

        Returns:
            List[str]: Liste des noms de tables
        """
        inspector = inspect(self.engine)
        tables = inspector.get_table_names(schema='public')
        logger.info(f"[SCAN] {len(tables)} tables detectees dans schema public")
        return tables

    def detect_bigint_tables(self) -> List[Tuple[str, str, str]]:
        """
        Detecte les tables avec des colonnes identifiants en BIGINT/INT.

        Returns:
            List[Tuple[str, str, str]]: Liste de (table, colonne, type)
        """
        violations = []

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
              AND (
                  c.column_name = 'id'
                  OR c.column_name LIKE '%_id'
              )
            ORDER BY c.table_name, c.column_name
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                violations.append((row[0], row[1], row[2]))

        if violations:
            logger.warning(f"[DETECT] {len(violations)} colonnes BIGINT/INT detectees")
            for table, col, dtype in violations[:10]:
                logger.warning(f"  - {table}.{col}: {dtype}")
            if len(violations) > 10:
                logger.warning(f"  ... et {len(violations) - 10} autres")
        else:
            logger.info("[DETECT] Aucune colonne BIGINT/INT detectee - base deja conforme UUID")

        return violations

    def drop_all_tables(self) -> int:
        """
        Supprime toutes les tables du schema public.

        Returns:
            int: Nombre de tables supprimees

        Note:
            Utilise DROP TABLE ... CASCADE pour gerer les FK.
            Ne touche PAS aux extensions PostgreSQL.
        """
        tables = self.get_public_tables()

        if not tables:
            logger.info("[DROP] Aucune table a supprimer")
            return 0

        logger.info(f"[DROP] Debut suppression de {len(tables)} tables...")

        with self.engine.connect() as conn:
            # Desactiver les contraintes FK temporairement pour la session
            # Note: On n'utilise PAS session_replication_role comme demande

            for table_name in tables:
                try:
                    # Echapper le nom de table pour securite
                    safe_name = table_name.replace('"', '""')
                    drop_sql = text(f'DROP TABLE IF EXISTS "{safe_name}" CASCADE')

                    conn.execute(drop_sql)
                    self.tables_dropped.append(table_name)
                    logger.info(f"  [OK] Table supprimee: {table_name}")

                except SQLAlchemyError as e:
                    logger.error(f"  [FAIL] Erreur sur {table_name}: {e}")
                    # Continuer avec les autres tables

            conn.commit()

        logger.info(f"[DROP] {len(self.tables_dropped)} tables supprimees")
        return len(self.tables_dropped)

    def recreate_tables_from_orm(self) -> int:
        """
        Recree toutes les tables depuis les modeles ORM.

        Returns:
            int: Nombre de tables creees

        Raises:
            DatabaseResetError: Si le chargement des modeles echoue
        """
        logger.info("[CREATE] Chargement des modeles ORM...")

        try:
            from app.db import Base, load_all_models, verify_models_loaded

            # Charger tous les modeles
            modules_count = load_all_models()
            verify_models_loaded()

            table_count = len(Base.metadata.tables)
            logger.info(f"[CREATE] {modules_count} modules charges, {table_count} tables ORM")

            if table_count == 0:
                raise DatabaseResetError(
                    "ERREUR CRITIQUE: Aucun modele ORM charge. "
                    "Verifiez que les modeles heritent de app.db.Base"
                )

            # Creer toutes les tables
            logger.info("[CREATE] Creation des tables via Base.metadata.create_all()...")
            Base.metadata.create_all(bind=self.engine)

            # Verifier les tables creees
            created_tables = self.get_public_tables()
            self.tables_created = created_tables

            logger.info(f"[CREATE] {len(created_tables)} tables creees avec succes")

            return len(created_tables)

        except ImportError as e:
            raise DatabaseResetError(f"Impossible d'importer les modules ORM: {e}")

    def validate_uuid_compliance(self) -> bool:
        """
        Valide que toutes les colonnes identifiants sont en UUID.

        Returns:
            bool: True si conforme, False sinon

        Raises:
            DatabaseResetError: Si des violations sont detectees
        """
        logger.info("[VALIDATE] Verification conformite UUID...")

        violations = self.detect_bigint_tables()

        if violations:
            error_msg = (
                f"\n"
                f"{'='*60}\n"
                f"ECHEC VALIDATION UUID\n"
                f"{'='*60}\n"
                f"\n"
                f"{len(violations)} colonnes identifiants non-UUID detectees:\n"
            )
            for table, col, dtype in violations[:20]:
                error_msg += f"  - {table}.{col}: {dtype}\n"
            if len(violations) > 20:
                error_msg += f"  ... et {len(violations) - 20} autres\n"
            error_msg += f"\n{'='*60}\n"

            raise DatabaseResetError(error_msg)

        logger.info("[VALIDATE] SUCCES: Toutes les colonnes identifiants sont UUID")
        return True

    def generate_report(self) -> str:
        """
        Genere un rapport de l'operation.

        Returns:
            str: Rapport formate
        """
        duration = datetime.now() - self.start_time if self.start_time else None
        duration_str = f"{duration.total_seconds():.2f}s" if duration else "N/A"

        report = f"""
{'='*60}
RAPPORT RESET DATABASE UUID
{'='*60}

Date:           {datetime.now().isoformat()}
Duree:          {duration_str}

SUPPRESSION:
  Tables supprimees:     {len(self.tables_dropped)}

RECREATION:
  Tables ORM creees:     {len(self.tables_created)}

STATUT: {'UUID FULL COMPLIANCE' if self.tables_created else 'INCOMPLET'}

{'='*60}
"""
        return report

    def run(self) -> bool:
        """
        Execute le workflow complet de reset.

        Returns:
            bool: True si succes, False sinon
        """
        self.start_time = datetime.now()

        logger.info("="*60)
        logger.info("AZALS - RESET DATABASE UUID")
        logger.info("="*60)

        try:
            # 1. Verification securite
            self.verify_environment()

            # 2. Connexion
            self.connect()

            # 3. Detection etat actuel
            current_violations = self.detect_bigint_tables()

            if not current_violations and self.get_public_tables():
                logger.info("[INFO] Base deja conforme UUID - reset optionnel")
                # On continue quand meme si demande explicitement

            # 4. Confirmation interactive (sauf CI)
            if os.environ.get("CI") != "true" and sys.stdin.isatty():
                tables = self.get_public_tables()
                print(f"\n>>> {len(tables)} tables seront SUPPRIMEES <<<")
                print(">>> TOUTES LES DONNEES SERONT PERDUES <<<\n")
                confirm = input("Confirmer le reset (tapez 'RESET'): ")
                if confirm != "RESET":
                    logger.info("[ABORT] Reset annule par l'utilisateur")
                    return False

            # 5. Suppression
            self.drop_all_tables()

            # 6. Recreation
            self.recreate_tables_from_orm()

            # 7. Validation
            self.validate_uuid_compliance()

            # 8. Rapport
            report = self.generate_report()
            logger.info(report)

            logger.info("[SUCCESS] Reset UUID termine avec succes")
            return True

        except DatabaseResetError as e:
            logger.error(str(e))
            return False
        except Exception as e:
            logger.exception(f"[FATAL] Erreur inattendue: {e}")
            return False


def main():
    """Point d'entree principal."""
    reset = UUIDDatabaseReset()
    success = reset.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
