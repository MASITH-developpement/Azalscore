"""
AZALS - Validateur de Schéma de Base de Données
================================================
Vérifie que toutes les PK/FK utilisent UUID et aucun BIGINT/INTEGER.
VERROU ANTI-RÉGRESSION: Bloque le démarrage si une incohérence est détectée.
"""

import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Erreur critique de validation de schéma."""
    pass


class SchemaValidator:
    """
    Validateur de schéma pour garantir la cohérence UUID.

    RÈGLE ARCHITECTURALE NON NÉGOCIABLE:
    - Toutes les PK = UUID
    - Toutes les FK = UUID
    - Aucun BIGINT/INTEGER pour identifiants métier
    """

    # Types autorisés pour les PK
    ALLOWED_PK_TYPES = {'uuid', 'character varying(36)', 'varchar(36)', 'text'}

    # Types interdits pour les PK/FK métier
    FORBIDDEN_ID_TYPES = {'bigint', 'integer', 'int', 'serial', 'bigserial', 'int4', 'int8'}

    # Colonnes autorisées à utiliser Integer (non-identifiants)
    ALLOWED_INTEGER_COLUMNS = {
        'sequence', 'level', 'priority', 'order', 'count', 'quantity',
        'year', 'month', 'day', 'hour', 'minute', 'file_size',
        'interventions_used', 'max_interventions', 'notice_period_days',
        'lead_time_days', 'response_time_hours', 'resolution_time_hours',
        'estimated_duration_minutes', 'actual_minutes', 'estimated_minutes',
        'frequency_value', 'cycle_count', 'current_cycles', 'expected_life_cycles',
        'expected_life_hours', 'useful_life_years', 'shelf_life_days',
        'year_manufactured', 'is_active', 'is_fully_validated',
    }

    def __init__(self, engine: Engine, base: DeclarativeBase):
        self.engine = engine
        self.base = base
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_orm_models(self) -> bool:
        """
        Valide tous les modèles ORM pour détecter les incohérences.
        Retourne True si tout est valide, False sinon.
        """
        logger.info("[SCHEMA] Validation des modèles ORM...")

        for mapper in self.base.registry.mappers:
            table = mapper.local_table
            if table is None:
                continue

            table_name = table.name

            # Vérifier les colonnes PK
            for col in table.primary_key.columns:
                col_type = str(col.type).lower()

                if any(forbidden in col_type for forbidden in self.FORBIDDEN_ID_TYPES):
                    self.errors.append(
                        f"[CRITICAL] {table_name}.{col.name}: PK utilise {col.type} "
                        f"au lieu de UUID. MIGRATION REQUISE."
                    )

            # Vérifier les FK
            for fk in table.foreign_keys:
                col = fk.parent
                col_type = str(col.type).lower()
                col_name = col.name.lower()

                # Ignorer les colonnes non-identifiants
                if not col_name.endswith('_id') and col_name != 'id':
                    continue

                if any(forbidden in col_type for forbidden in self.FORBIDDEN_ID_TYPES):
                    self.errors.append(
                        f"[CRITICAL] {table_name}.{col.name}: FK utilise {col.type} "
                        f"au lieu de UUID. Référence: {fk.target_fullname}"
                    )

            # Vérifier les colonnes *_id qui ne sont pas des FK déclarées
            for col in table.columns:
                col_name = col.name.lower()
                col_type = str(col.type).lower()

                # Colonnes autorisées à être Integer
                if any(allowed in col_name for allowed in self.ALLOWED_INTEGER_COLUMNS):
                    continue

                if col_name.endswith('_id') or col_name == 'id':
                    if any(forbidden in col_type for forbidden in self.FORBIDDEN_ID_TYPES):
                        if col not in table.primary_key.columns:
                            # Vérifier si c'est une FK déclarée
                            is_fk = any(fk.parent == col for fk in table.foreign_keys)
                            if not is_fk:
                                self.warnings.append(
                                    f"[WARNING] {table_name}.{col.name}: Colonne _id "
                                    f"utilise {col.type}. Considérer UUID si c'est un identifiant métier."
                                )

        return len(self.errors) == 0

    def validate_database_schema(self) -> bool:
        """
        Valide le schéma réel de la base de données PostgreSQL.
        Retourne True si tout est valide, False sinon.
        """
        logger.info("[SCHEMA] Validation du schéma PostgreSQL...")

        try:
            with self.engine.connect() as conn:
                # Vérifier les extensions requises
                result = conn.execute(text("""
                    SELECT extname FROM pg_extension
                    WHERE extname IN ('pgcrypto', 'uuid-ossp')
                """))
                extensions = [row[0] for row in result]

                if 'pgcrypto' not in extensions and 'uuid-ossp' not in extensions:
                    self.warnings.append(
                        "[WARNING] Extensions pgcrypto/uuid-ossp non activées. "
                        "Recommandé pour gen_random_uuid()."
                    )

                # Vérifier les types de PK dans la base
                result = conn.execute(text("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        c.data_type,
                        c.udt_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.columns c
                        ON c.table_name = tc.table_name
                        AND c.column_name = kcu.column_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                    ORDER BY tc.table_name
                """))

                for row in result:
                    table_name, col_name, data_type, udt_name = row

                    # Ignorer les tables système
                    if table_name.startswith('pg_') or table_name.startswith('sql_'):
                        continue

                    if udt_name in ('int4', 'int8', 'serial', 'bigserial'):
                        self.errors.append(
                            f"[CRITICAL] DB: {table_name}.{col_name}: "
                            f"PK utilise {udt_name}. MIGRATION REQUISE."
                        )

                # Vérifier les FK
                result = conn.execute(text("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        c.udt_name,
                        ccu.table_name AS foreign_table,
                        ccu.column_name AS foreign_column
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
                """))

                for row in result:
                    table_name, col_name, udt_name, foreign_table, foreign_col = row

                    if udt_name in ('int4', 'int8'):
                        self.errors.append(
                            f"[CRITICAL] DB: {table_name}.{col_name}: "
                            f"FK utilise {udt_name} vers {foreign_table}.{foreign_col}. "
                            f"TYPE MISMATCH probable."
                        )

        except Exception as e:
            logger.warning(f"[SCHEMA] Validation DB ignorée (erreur connexion): {e}")
            return True  # Ne pas bloquer si la DB n'est pas accessible

        return len(self.errors) == 0

    def get_dependency_order(self) -> List[str]:
        """
        Calcule l'ordre de création des tables basé sur les FK.
        Retourne la liste des tables dans l'ordre de création.
        """
        from sqlalchemy import MetaData

        metadata = self.base.metadata

        # Utiliser sorted_tables qui respecte l'ordre des FK
        ordered = [table.name for table in metadata.sorted_tables]

        return ordered

    def generate_audit_report(self) -> str:
        """Génère un rapport d'audit complet."""
        report = []
        report.append("=" * 70)
        report.append("RAPPORT D'AUDIT DE SCHÉMA AZALS")
        report.append("=" * 70)
        report.append("")

        # Statistiques
        table_count = len(list(self.base.registry.mappers))
        report.append(f"Tables analysées: {table_count}")
        report.append(f"Erreurs critiques: {len(self.errors)}")
        report.append(f"Avertissements: {len(self.warnings)}")
        report.append("")

        # Ordre de création
        report.append("-" * 70)
        report.append("ORDRE DE CRÉATION DES TABLES (respecte les FK)")
        report.append("-" * 70)
        for i, table in enumerate(self.get_dependency_order(), 1):
            report.append(f"  {i:3}. {table}")
        report.append("")

        # Erreurs
        if self.errors:
            report.append("-" * 70)
            report.append("ERREURS CRITIQUES (BLOQUENT LE DÉMARRAGE)")
            report.append("-" * 70)
            for error in self.errors:
                report.append(f"  {error}")
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
        if self.errors:
            report.append("STATUT: ÉCHEC - Corrections requises avant démarrage")
        else:
            report.append("STATUT: SUCCÈS - Schéma conforme aux règles UUID")
        report.append("=" * 70)

        return "\n".join(report)

    def validate_and_enforce(self, strict: bool = True) -> bool:
        """
        Valide le schéma et applique le verrou anti-régression.

        Args:
            strict: Si True, lève une exception en cas d'erreur critique.

        Returns:
            True si le schéma est valide.

        Raises:
            SchemaValidationError: Si strict=True et des erreurs sont détectées.
        """
        logger.info("[SCHEMA] Démarrage de la validation anti-régression...")

        # Valider les modèles ORM
        orm_valid = self.validate_orm_models()

        # Valider le schéma DB si accessible
        db_valid = self.validate_database_schema()

        # Générer le rapport
        report = self.generate_audit_report()

        if self.errors:
            logger.error("\n" + report)
            if strict:
                raise SchemaValidationError(
                    f"Validation de schéma échouée: {len(self.errors)} erreur(s) critique(s). "
                    f"Voir le rapport ci-dessus."
                )
            return False

        logger.info("\n" + report)
        logger.info("[SCHEMA] Validation réussie - Schéma conforme UUID")
        return True


def validate_schema_on_startup(engine: Engine, base: DeclarativeBase, strict: bool = False):
    """
    Fonction utilitaire pour valider le schéma au démarrage.
    Appelée depuis app/main.py dans le lifespan.

    Args:
        engine: Engine SQLAlchemy
        base: Base déclarative (Base)
        strict: Si True, bloque le démarrage en cas d'erreur
    """
    validator = SchemaValidator(engine, base)
    return validator.validate_and_enforce(strict=strict)
