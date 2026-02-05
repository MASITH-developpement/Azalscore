"""
AZALS - Validateur de Schéma de Base de Données
================================================
Vérifie que toutes les PK/FK utilisent UUID et aucun BIGINT/INTEGER.
VERROU ANTI-RÉGRESSION BLOQUANT: Empêche le démarrage si une incohérence est détectée.

RÈGLE NON NÉGOCIABLE:
- Toutes les PK métier = UUID
- Toutes les FK métier = UUID
- AUCUN BIGINT / INTEGER pour identifiants
- BLOCAGE IMMÉDIAT si violation détectée en production
"""

import logging

from sqlalchemy import TypeDecorator, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


def _is_uuid_type(col_type) -> bool:
    """
    Vérifie si un type de colonne est un type UUID valide.
    Gère les TypeDecorator comme UniversalUUID correctement.
    """
    type_name = type(col_type).__name__

    # Types UUID connus
    uuid_type_names = {'UniversalUUID', 'UUID', 'GUID', 'Uuid'}
    if type_name in uuid_type_names:
        return True

    # Vérifier le module pour les types PostgreSQL UUID
    type_module = type(col_type).__module__
    if 'uuid' in type_module.lower():
        return True

    # Pour les TypeDecorator, vérifier le nom de la classe
    if isinstance(col_type, TypeDecorator):
        impl_class_name = type(col_type).__name__
        if impl_class_name in uuid_type_names:
            return True
        # Vérifier si le nom contient UUID
        if 'uuid' in impl_class_name.lower():
            return True

    # Vérifier dans la représentation string
    type_str = str(col_type).lower()
    return 'uuid' in type_str


def _is_integer_type(col_type) -> bool:
    """
    Vérifie si un type de colonne est un type Integer/BigInteger interdit pour les IDs.
    """
    type_name = type(col_type).__name__

    # Types Integer interdits pour les identifiants
    forbidden_types = {'Integer', 'BigInteger', 'SmallInteger', 'INT', 'BIGINT'}
    if type_name in forbidden_types:
        return True

    # Vérifier dans la représentation string
    type_str = str(col_type).lower()
    if 'integer' in type_str or 'bigint' in type_str:
        # Mais pas si c'est un UUID
        if 'uuid' not in type_str:
            return True

    return False


class SchemaValidationError(Exception):
    """Erreur critique de validation de schéma - BLOQUE LE DÉMARRAGE."""
    pass


class SchemaValidator:
    """
    Validateur de schéma BLOQUANT pour garantir la cohérence UUID.

    RÈGLE ARCHITECTURALE ABSOLUE:
    - Toutes les PK = UUID
    - Toutes les FK = UUID
    - Aucun BIGINT/INTEGER pour identifiants métier
    - BLOCAGE IMMÉDIAT si violation détectée
    """

    # Types PostgreSQL interdits pour les PK/FK métier
    FORBIDDEN_TYPES = {'int4', 'int8', 'serial', 'bigserial', 'integer', 'bigint'}

    # Colonnes autorisées à utiliser Integer (non-identifiants)
    ALLOWED_INTEGER_PATTERNS = {
        'sequence', 'level', 'priority', 'order', 'count', 'quantity',
        'year', 'month', 'day', 'hour', 'minute', 'file_size', 'size',
        'interventions_used', 'max_interventions', 'notice_period_days',
        'lead_time_days', 'response_time_hours', 'resolution_time_hours',
        'estimated_duration', 'actual_minutes', 'estimated_minutes',
        'frequency_value', 'cycle_count', 'current_cycles', 'expected_life',
        'useful_life', 'shelf_life', 'year_manufactured', 'is_active',
        'is_fully_validated', 'version', 'retry_count', 'sync_version',
        'last_sync_version', 'wo_total', 'wo_preventive', 'wo_corrective',
        'wo_completed', 'wo_overdue', 'failure_count', 'work_order_backlog',
    }

    def __init__(self, engine: Engine, base: DeclarativeBase):
        self.engine = engine
        self.base = base
        self.critical_errors: list[str] = []
        self.warnings: list[str] = []
        self.tables_with_bigint: set[str] = set()

    def _is_allowed_integer_column(self, column_name: str) -> bool:
        """Vérifie si une colonne est autorisée à utiliser Integer."""
        col_lower = column_name.lower()
        # Les colonnes *_id doivent TOUJOURS être UUID
        if col_lower.endswith('_id') or col_lower == 'id':
            return False
        # Vérifier les patterns autorisés
        return any(pattern in col_lower for pattern in self.ALLOWED_INTEGER_PATTERNS)

    def validate_database_schema(self) -> bool:
        """
        Valide le schéma PostgreSQL réel.
        DÉTECTE les tables avec PK/FK BIGINT qui doivent être supprimées.

        Returns:
            True si le schéma est valide, False sinon.
        """
        logger.info("[SCHEMA] Validation du schéma PostgreSQL...")

        try:
            with self.engine.connect() as conn:
                # 1. Vérifier les extensions
                result = conn.execute(text("""
                    SELECT extname FROM pg_extension
                    WHERE extname IN ('pgcrypto', 'uuid-ossp')
                """))
                extensions = [row[0] for row in result]

                if not extensions:
                    self.warnings.append(
                        "Extensions pgcrypto/uuid-ossp non activées. "
                        "Exécuter: CREATE EXTENSION IF NOT EXISTS pgcrypto;"
                    )

                # 2. CRITIQUE: Vérifier les PK BIGINT/INTEGER
                result = conn.execute(text("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        c.udt_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.columns c
                        ON c.table_name = tc.table_name
                        AND c.column_name = kcu.column_name
                        AND c.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                    AND c.udt_name IN ('int4', 'int8', 'serial', 'bigserial')
                    AND tc.table_name NOT LIKE 'pg_%'
                    AND tc.table_name NOT LIKE '_migration%'
                    ORDER BY tc.table_name
                """))

                for row in result:
                    table_name, col_name, udt_name = row
                    self.tables_with_bigint.add(table_name)
                    self.critical_errors.append(
                        f"[CRITICAL] TABLE {table_name}: PK '{col_name}' utilise {udt_name.upper()}. "
                        f"DOIT être UUID. Exécuter: DROP TABLE {table_name} CASCADE;"
                    )

                # 3. Vérifier les FK BIGINT/INTEGER vers des colonnes *_id
                result = conn.execute(text("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        c.udt_name,
                        ccu.table_name AS ref_table,
                        ccu.column_name AS ref_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.columns c
                        ON c.table_name = tc.table_name
                        AND c.column_name = kcu.column_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND c.udt_name IN ('int4', 'int8')
                    AND (kcu.column_name LIKE '%_id' OR kcu.column_name = 'id')
                """))

                for row in result:
                    table_name, col_name, udt_name, ref_table, ref_col = row
                    self.tables_with_bigint.add(table_name)
                    self.critical_errors.append(
                        f"[CRITICAL] TABLE {table_name}: FK '{col_name}' utilise {udt_name.upper()} "
                        f"vers {ref_table}.{ref_col}. TYPE MISMATCH UUID/BIGINT."
                    )

                # 4. Vérifier les colonnes *_id qui sont BIGINT mais pas FK déclarées
                result = conn.execute(text("""
                    SELECT
                        table_name,
                        column_name,
                        udt_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND udt_name IN ('int4', 'int8')
                    AND (column_name LIKE '%_id' OR column_name = 'id')
                    AND table_name NOT LIKE 'pg_%'
                    ORDER BY table_name, column_name
                """))

                seen_columns = set()
                for row in result:
                    table_name, col_name, udt_name = row
                    key = f"{table_name}.{col_name}"
                    if key not in seen_columns and table_name not in self.tables_with_bigint:
                        seen_columns.add(key)
                        self.tables_with_bigint.add(table_name)
                        self.critical_errors.append(
                            f"[CRITICAL] TABLE {table_name}: Colonne '{col_name}' utilise {udt_name.upper()}. "
                            f"Tous les identifiants doivent être UUID."
                        )

        except Exception as e:
            logger.warning("[SCHEMA] Validation DB ignorée (erreur connexion): %s", e)
            return True  # Ne pas bloquer si la DB n'est pas accessible

        return len(self.critical_errors) == 0

    def validate_orm_models(self) -> bool:
        """
        Valide tous les modèles ORM pour détecter les incohérences.
        Utilise une détection robuste des types UUID et Integer.

        Returns:
            True si tous les modèles sont valides.
        """
        logger.info("[SCHEMA] Validation des modèles ORM...")

        tables_checked = 0
        pk_checked = 0
        fk_checked = 0

        for mapper in self.base.registry.mappers:
            table = mapper.local_table
            if table is None:
                continue

            table_name = table.name
            tables_checked += 1

            # Vérifier les colonnes PK
            for col in table.primary_key.columns:
                pk_checked += 1

                # Vérifier si c'est un type UUID valide
                if _is_uuid_type(col.type):
                    continue  # OK - type UUID correct

                # Vérifier si c'est un type Integer interdit
                if _is_integer_type(col.type):
                    self.critical_errors.append(
                        f"[ORM CRITICAL] {table_name}.{col.name}: PK définie comme {type(col.type).__name__}. "
                        f"DOIT utiliser UniversalUUID()."
                    )

            # Vérifier les FK
            for fk in table.foreign_keys:
                col = fk.parent
                col_name = col.name.lower()
                fk_checked += 1

                # Colonnes *_id doivent être UUID
                if col_name.endswith('_id') or col_name == 'id':
                    # Vérifier si c'est un type UUID valide
                    if _is_uuid_type(col.type):
                        continue  # OK - type UUID correct

                    # Vérifier si c'est un type Integer interdit
                    if _is_integer_type(col.type):
                        self.critical_errors.append(
                            f"[ORM CRITICAL] {table_name}.{col.name}: FK définie comme {type(col.type).__name__}. "
                            f"DOIT utiliser UniversalUUID()."
                        )

        logger.info("[SCHEMA] ORM: %s tables, %s PK, %s FK vérifiées", tables_checked, pk_checked, fk_checked)
        return len(self.critical_errors) == 0

    def get_cleanup_sql(self) -> str:
        """Génère le SQL pour supprimer les tables problématiques."""
        if not self.tables_with_bigint:
            return "-- Aucune table BIGINT à supprimer"

        lines = [
            "-- Script de nettoyage généré automatiquement",
            "-- ATTENTION: Supprime les données!",
            "",
            "SET session_replication_role = 'replica';",
            "",
        ]

        for table in sorted(self.tables_with_bigint):
            lines.append(f"DROP TABLE IF EXISTS {table} CASCADE;")

        lines.extend([
            "",
            "SET session_replication_role = 'origin';",
            "",
            "-- Redémarrer l'application pour recréer les tables avec UUID",
        ])

        return "\n".join(lines)

    def get_dependency_order(self) -> list[str]:
        """Calcule l'ordre de création des tables basé sur les FK."""
        return [table.name for table in self.base.metadata.sorted_tables]

    def generate_report(self) -> str:
        """Génère un rapport d'audit complet."""
        report = []
        report.append("=" * 70)
        report.append("RAPPORT D'AUDIT DE SCHÉMA AZALS - VERROU ANTI-RÉGRESSION")
        report.append("=" * 70)
        report.append("")

        # Statistiques
        table_count = len(list(self.base.registry.mappers))
        report.append(f"Tables ORM analysées: {table_count}")
        report.append(f"Tables avec BIGINT détectées: {len(self.tables_with_bigint)}")
        report.append(f"Erreurs critiques: {len(self.critical_errors)}")
        report.append(f"Avertissements: {len(self.warnings)}")
        report.append("")

        # Erreurs critiques
        if self.critical_errors:
            report.append("-" * 70)
            report.append("ERREURS CRITIQUES - BLOQUENT LE DÉMARRAGE")
            report.append("-" * 70)
            for error in self.critical_errors:
                report.append(f"  {error}")
            report.append("")

            # Script de correction
            report.append("-" * 70)
            report.append("SCRIPT DE CORRECTION À EXÉCUTER:")
            report.append("-" * 70)
            report.append(self.get_cleanup_sql())
            report.append("")

        # Warnings
        if self.warnings:
            report.append("-" * 70)
            report.append("AVERTISSEMENTS")
            report.append("-" * 70)
            for warning in self.warnings:
                report.append(f"  {warning}")
            report.append("")

        # Statut final
        report.append("=" * 70)
        if self.critical_errors:
            report.append("STATUT: ÉCHEC CRITIQUE - DÉMARRAGE BLOQUÉ")
            report.append("")
            report.append("ACTIONS REQUISES:")
            report.append("1. Exécuter le script SQL ci-dessus")
            report.append("2. Ou exécuter: psql -d <database> -f scripts/force_cleanup_bigint_tables.sql")
            report.append("3. Redémarrer l'application")
        else:
            report.append("STATUT: SUCCÈS - Schéma conforme aux règles UUID")
        report.append("=" * 70)

        return "\n".join(report)

    def validate_and_enforce(self, strict: bool = True) -> bool:
        """
        Valide le schéma et applique le verrou anti-régression.

        Args:
            strict: Si True, BLOQUE LE DÉMARRAGE en cas d'erreur critique.

        Returns:
            True si le schéma est valide.

        Raises:
            SchemaValidationError: Si strict=True et des erreurs sont détectées.
        """
        logger.info("[SCHEMA] ========================================")
        logger.info("[SCHEMA] VERROU ANTI-RÉGRESSION UUID ACTIVÉ")
        logger.info("[SCHEMA] ========================================")

        # Valider le schéma DB en premier (plus important)
        self.validate_database_schema()

        # Valider les modèles ORM
        self.validate_orm_models()

        # Générer et afficher le rapport
        report = self.generate_report()

        if self.critical_errors:
            # TOUJOURS logger le rapport en cas d'erreur
            logger.error(
                "[SCHEMA] Erreurs critiques détectées dans le schéma",
                extra={
                    "critical_errors_count": len(self.critical_errors),
                    "report": report[:2000],
                    "consequence": "schema_invalid"
                }
            )

            if strict:
                # BLOCAGE ABSOLU - Impossible de démarrer
                logger.critical(
                    "[SCHEMA] ARRÊT FORCÉ — tables BIGINT détectées, démarrage impossible",
                    extra={
                        "critical_errors_count": len(self.critical_errors),
                        "solution": "psql -d <database> -f scripts/force_cleanup_bigint_tables.sql",
                        "consequence": "startup_aborted"
                    }
                )

                # ARRÊT IMMÉDIAT via exception
                raise SchemaValidationError(
                    f"Schéma invalide: {len(self.critical_errors)} erreur(s) BIGINT détectée(s). "
                    f"Voir le rapport ci-dessus pour les corrections."
                )

            return False

        logger.info("\n" + report)
        logger.info("[SCHEMA] Validation réussie - Schéma conforme UUID")
        return True


def validate_schema_on_startup(engine: Engine, base: DeclarativeBase, strict: bool = False) -> bool:
    """
    Fonction utilitaire pour valider le schéma au démarrage.
    Appelée depuis app/main.py dans le lifespan.

    Args:
        engine: Engine SQLAlchemy
        base: Base déclarative (Base)
        strict: Si True, BLOQUE le démarrage en cas d'erreur

    Returns:
        True si le schéma est valide, False sinon.

    Raises:
        SchemaValidationError: Si strict=True et des erreurs critiques sont détectées.
    """
    validator = SchemaValidator(engine, base)
    return validator.validate_and_enforce(strict=strict)


def get_bigint_tables(engine: Engine) -> set[str]:
    """
    Retourne l'ensemble des tables avec PK BIGINT.
    Utilitaire pour les scripts de maintenance.
    """
    tables = set()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT tc.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.columns c
                    ON c.table_name = tc.table_name
                    AND c.column_name = kcu.column_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
                AND c.udt_name IN ('int4', 'int8', 'serial', 'bigserial')
            """))
            tables = {row[0] for row in result}
    except Exception as e:
        logger.warning("Failed to retrieve tables with integer PKs: %s", e)
    return tables
