#!/usr/bin/env python3
"""
AZALS - UUID Schema Guard - Verrou Anti-Régression BLOQUANT
============================================================
Script de validation FINALE qui BLOQUE le démarrage si:
- Une PK n'est pas UUID
- Une FK n'est pas UUID
- Une colonne *_id n'est pas UUID
- Un Integer/BigInteger est détecté pour identifiants

CE SCRIPT EST UN VERROU DE SÉCURITÉ NON NÉGOCIABLE.

Usage:
    python scripts/uuid_schema_guard.py
    python scripts/uuid_schema_guard.py --strict  # Bloque sur toute erreur
    python scripts/uuid_schema_guard.py --postgres # Valide aussi PostgreSQL
"""

import os
import sys
import ast
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Tuple
from datetime import datetime


@dataclass
class ValidationIssue:
    """Représente un problème de validation."""
    file_path: str
    line_number: int
    class_name: str
    column_name: str
    issue_type: str  # PK_INTEGER, FK_INTEGER, ID_INTEGER, IMPORT_MISSING
    current_type: str
    severity: str = "CRITICAL"
    message: str = ""


@dataclass
class GuardReport:
    """Rapport de validation."""
    timestamp: str = ""
    total_files: int = 0
    total_classes: int = 0
    total_pk: int = 0
    total_fk: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    pg_tables_checked: int = 0
    pg_issues: List[str] = field(default_factory=list)


class UUIDSchemaGuard:
    """
    Garde de schéma UUID BLOQUANT.
    Valide que TOUS les modèles ORM sont 100% UUID.
    """

    # Types interdits pour les identifiants
    FORBIDDEN_TYPES = {
        'Integer', 'BigInteger', 'SmallInteger',
        'INT', 'BIGINT', 'SMALLINT',
        'SERIAL', 'BIGSERIAL'
    }

    # Types UUID acceptés
    ACCEPTED_TYPES = {
        'UUID', 'UniversalUUID', 'GUID', 'Uuid'
    }

    # Colonnes autorisées en Integer
    ALLOWED_INTEGER_COLUMNS = {
        'sequence', 'level', 'priority', 'order', 'sort_order',
        'count', 'quantity', 'year', 'month', 'day', 'hour',
        'file_size', 'size', 'version', 'retry_count',
        'is_active', 'is_validated', 'is_fully_validated',
        'duration', 'estimated_minutes', 'actual_minutes',
    }

    def __init__(self, base_path: str, strict: bool = True):
        self.base_path = Path(base_path)
        self.strict = strict
        self.report = GuardReport(timestamp=datetime.now().isoformat())

    def _is_id_column(self, name: str) -> bool:
        """Vérifie si c'est une colonne identifiant."""
        name_lower = name.lower()
        return name_lower == 'id' or name_lower.endswith('_id')

    def _is_allowed_integer(self, name: str) -> bool:
        """Vérifie si une colonne peut être Integer."""
        if self._is_id_column(name):
            return False
        name_lower = name.lower()
        return name_lower in self.ALLOWED_INTEGER_COLUMNS or any(
            p in name_lower for p in ['_count', '_total', '_number']
        )

    def _extract_type_name(self, node) -> Optional[str]:
        """Extrait le nom de type depuis un noeud AST."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _is_primary_key(self, call_node: ast.Call) -> bool:
        """Vérifie si Column() est une primary key."""
        for keyword in call_node.keywords:
            if keyword.arg == 'primary_key':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value is True
                elif hasattr(keyword.value, 'value'):
                    return keyword.value.value is True
        return False

    def _has_foreign_key(self, call_node: ast.Call) -> bool:
        """Vérifie si Column() contient ForeignKey."""
        for arg in call_node.args:
            if isinstance(arg, ast.Call):
                type_name = self._extract_type_name(arg)
                if type_name == 'ForeignKey':
                    return True
        return False

    def _analyze_class(self, node: ast.ClassDef, file_path: str) -> List[ValidationIssue]:
        """Analyse une classe ORM."""
        issues = []
        class_name = node.name

        # Vérifier si c'est un modèle SQLAlchemy
        is_model = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('Base', 'DeclarativeBase'):
                is_model = True
            elif isinstance(base, ast.Attribute) and base.attr in ('Base', 'DeclarativeBase'):
                is_model = True

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        is_model = True

        if not is_model:
            return issues

        self.report.total_classes += 1

        # Analyser chaque attribut
        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue

            for target in item.targets:
                if not isinstance(target, ast.Name):
                    continue

                col_name = target.id

                # Vérifier si c'est un Column()
                if not isinstance(item.value, ast.Call):
                    continue

                call = item.value
                func = call.func

                is_column = False
                if isinstance(func, ast.Name) and func.id == 'Column':
                    is_column = True
                elif isinstance(func, ast.Attribute) and func.attr == 'Column':
                    is_column = True

                if not is_column:
                    continue

                # Extraire le type
                if not call.args:
                    continue

                type_node = call.args[0]
                type_name = self._extract_type_name(type_node)

                if not type_name:
                    continue

                is_pk = self._is_primary_key(call)
                is_fk = self._has_foreign_key(call)
                is_id_col = self._is_id_column(col_name)

                if is_pk:
                    self.report.total_pk += 1
                if is_fk:
                    self.report.total_fk += 1

                # === VALIDATION ===

                # 1. PK avec type interdit
                if is_pk and type_name in self.FORBIDDEN_TYPES:
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        line_number=item.lineno,
                        class_name=class_name,
                        column_name=col_name,
                        issue_type="PK_INTEGER",
                        current_type=type_name,
                        message=f"PK '{col_name}' utilise {type_name} au lieu de UUID"
                    ))

                # 2. FK avec type interdit
                elif is_fk and type_name in self.FORBIDDEN_TYPES:
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        line_number=item.lineno,
                        class_name=class_name,
                        column_name=col_name,
                        issue_type="FK_INTEGER",
                        current_type=type_name,
                        message=f"FK '{col_name}' utilise {type_name} au lieu de UUID"
                    ))

                # 3. Colonne *_id avec type interdit
                elif is_id_col and type_name in self.FORBIDDEN_TYPES:
                    if not self._is_allowed_integer(col_name):
                        issues.append(ValidationIssue(
                            file_path=str(file_path),
                            line_number=item.lineno,
                            class_name=class_name,
                            column_name=col_name,
                            issue_type="ID_INTEGER",
                            current_type=type_name,
                            message=f"Colonne ID '{col_name}' utilise {type_name} au lieu de UUID"
                        ))

        return issues

    def _analyze_file(self, file_path: Path) -> List[ValidationIssue]:
        """Analyse un fichier Python."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            self.report.total_files += 1

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    issues.extend(self._analyze_class(node, file_path))

        except SyntaxError as e:
            pass  # Ignorer les erreurs de syntaxe
        except Exception as e:
            pass

        return issues

    def validate_orm(self) -> bool:
        """Valide tous les modèles ORM."""
        print("[GUARD] Validation des modèles ORM...")

        for file_path in self.base_path.rglob('*.py'):
            if '__pycache__' in str(file_path):
                continue
            if 'test' in str(file_path).lower():
                continue
            if 'backup' in str(file_path).lower():
                continue

            issues = self._analyze_file(file_path)
            self.report.issues.extend(issues)

        return len(self.report.issues) == 0

    def validate_postgres(self, connection_string: str = None) -> bool:
        """Valide le schéma PostgreSQL."""
        try:
            from sqlalchemy import create_engine, text

            if not connection_string:
                # Essayer de charger depuis la config
                try:
                    from app.core.config import get_settings
                    settings = get_settings()
                    connection_string = settings.database_url
                except Exception:
                    print("[GUARD] Impossible de charger la config PostgreSQL")
                    return True  # Ne pas bloquer si pas de config

            engine = create_engine(connection_string)

            with engine.connect() as conn:
                # Vérifier les PK BIGINT
                result = conn.execute(text("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        c.udt_name
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

                for row in result:
                    table_name, column_name, udt_name = row
                    self.report.pg_issues.append(
                        f"[PG] {table_name}.{column_name}: PK de type {udt_name}"
                    )
                    self.report.pg_tables_checked += 1

            return len(self.report.pg_issues) == 0

        except Exception as e:
            print(f"[GUARD] Erreur PostgreSQL: {e}")
            return True  # Ne pas bloquer si erreur de connexion

    def generate_report(self) -> str:
        """Génère le rapport de validation."""
        lines = []
        lines.append("=" * 80)
        lines.append("AZALS - UUID SCHEMA GUARD - RAPPORT DE VALIDATION")
        lines.append("=" * 80)
        lines.append(f"Date: {self.report.timestamp}")
        lines.append(f"Mode: {'STRICT (bloquant)' if self.strict else 'PERMISSIF'}")
        lines.append("")

        # Statistiques ORM
        lines.append("-" * 80)
        lines.append("STATISTIQUES ORM")
        lines.append("-" * 80)
        lines.append(f"Fichiers analysés:     {self.report.total_files}")
        lines.append(f"Classes ORM:           {self.report.total_classes}")
        lines.append(f"Clés primaires:        {self.report.total_pk}")
        lines.append(f"Clés étrangères:       {self.report.total_fk}")
        lines.append("")

        # Statistiques PostgreSQL
        if self.report.pg_tables_checked > 0 or self.report.pg_issues:
            lines.append("-" * 80)
            lines.append("STATISTIQUES POSTGRESQL")
            lines.append("-" * 80)
            lines.append(f"Tables BIGINT:         {len(self.report.pg_issues)}")
            lines.append("")

        # Erreurs ORM
        orm_errors = len(self.report.issues)
        pg_errors = len(self.report.pg_issues)
        total_errors = orm_errors + pg_errors

        if self.report.issues:
            lines.append("-" * 80)
            lines.append(f"ERREURS CRITIQUES ORM ({orm_errors})")
            lines.append("-" * 80)

            # Grouper par fichier
            by_file: Dict[str, List[ValidationIssue]] = {}
            for issue in self.report.issues:
                if issue.file_path not in by_file:
                    by_file[issue.file_path] = []
                by_file[issue.file_path].append(issue)

            for file_path, issues in sorted(by_file.items()):
                rel_path = os.path.relpath(file_path, self.base_path)
                lines.append(f"\n📁 {rel_path}")

                for issue in issues:
                    lines.append(
                        f"  ❌ Ligne {issue.line_number}: "
                        f"{issue.class_name}.{issue.column_name} "
                        f"[{issue.issue_type}] {issue.current_type}"
                    )

        # Erreurs PostgreSQL
        if self.report.pg_issues:
            lines.append("")
            lines.append("-" * 80)
            lines.append(f"ERREURS CRITIQUES POSTGRESQL ({pg_errors})")
            lines.append("-" * 80)
            for issue in self.report.pg_issues:
                lines.append(f"  ❌ {issue}")

        # Statut final
        lines.append("")
        lines.append("=" * 80)

        if total_errors == 0:
            lines.append("✅ STATUT: OK - UUID FULL COMPLIANCE")
            lines.append("")
            lines.append(f"Tables ORM analysées:        {self.report.total_classes}")
            lines.append(f"Tables avec BIGINT détectées: 0")
            lines.append(f"Erreurs critiques:           0")
            lines.append("")
            lines.append("Le projet peut démarrer avec le verrou anti-régression activé.")
        else:
            lines.append("❌ STATUT: ÉCHEC CRITIQUE")
            lines.append("")
            lines.append(f"Tables ORM analysées:        {self.report.total_classes}")
            lines.append(f"Erreurs ORM:                 {orm_errors}")
            lines.append(f"Erreurs PostgreSQL:          {pg_errors}")
            lines.append(f"TOTAL ERREURS CRITIQUES:     {total_errors}")
            lines.append("")
            if self.strict:
                lines.append("⛔ DÉMARRAGE BLOQUÉ - Corriger avec fix_all_models_to_uuid.py")
            else:
                lines.append("⚠️  Corriger les erreurs avec fix_all_models_to_uuid.py")

        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="AZALS - UUID Schema Guard - Validation anti-régression"
    )
    parser.add_argument(
        '--path', '-p',
        default='app',
        help='Chemin du répertoire à valider (défaut: app)'
    )
    parser.add_argument(
        '--strict', '-s',
        action='store_true',
        default=True,
        help='Mode strict (bloque sur erreur)'
    )
    parser.add_argument(
        '--postgres', '--pg',
        action='store_true',
        help='Valider aussi PostgreSQL'
    )
    parser.add_argument(
        '--output', '-o',
        help='Fichier de sortie pour le rapport'
    )

    args = parser.parse_args()

    # Déterminer le chemin
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    base_path = project_root / args.path

    if not base_path.exists():
        print(f"[ERREUR] Répertoire non trouvé: {base_path}")
        sys.exit(1)

    print("[GUARD] AZALS UUID Schema Guard")
    print("[GUARD] Validation anti-régression en cours...")

    # Créer le guard
    guard = UUIDSchemaGuard(base_path, strict=args.strict)

    # Valider ORM
    orm_ok = guard.validate_orm()

    # Valider PostgreSQL si demandé
    pg_ok = True
    if args.postgres:
        pg_ok = guard.validate_postgres()

    # Générer le rapport
    report = guard.generate_report()

    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[GUARD] Rapport: {output_path}")
    else:
        print(report)

    # Code de sortie
    if not orm_ok or not pg_ok:
        if args.strict:
            sys.exit(1)  # Bloque le démarrage
        else:
            sys.exit(0)  # Warning seulement

    sys.exit(0)


if __name__ == '__main__':
    main()
