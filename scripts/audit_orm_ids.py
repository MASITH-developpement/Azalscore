#!/usr/bin/env python3
"""
AZALS - Audit ORM IDs - Script Industriel
==========================================
Détecte automatiquement tous les problèmes UUID/BIGINT dans les modèles ORM.

Ce script analyse via AST tous les fichiers Python contenant des modèles SQLAlchemy
et génère un rapport détaillé des colonnes non conformes.

RÈGLES DE DÉTECTION:
1. Toute colonne `id` ou `*_id` avec Column(Integer/BigInteger) = ERREUR CRITIQUE
2. Toute PK avec Integer/BigInteger = ERREUR CRITIQUE
3. Toute FK avec Integer/BigInteger = ERREUR CRITIQUE
4. autoincrement=True sur colonnes id = ERREUR CRITIQUE
5. Sequence(...) pour colonnes id = ERREUR CRITIQUE

Usage:
    python scripts/audit_orm_ids.py
    python scripts/audit_orm_ids.py --output report.txt
    python scripts/audit_orm_ids.py --json
"""

import ast
import os
import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime


@dataclass
class ColumnIssue:
    """Représente un problème détecté sur une colonne."""
    file_path: str
    line_number: int
    class_name: str
    column_name: str
    current_type: str
    expected_type: str
    issue_type: str  # PK_INTEGER, FK_INTEGER, AUTOINCREMENT, SEQUENCE
    severity: str = "CRITICAL"
    raw_line: str = ""


@dataclass
class AuditReport:
    """Rapport d'audit complet."""
    timestamp: str
    total_files: int = 0
    total_classes: int = 0
    total_columns: int = 0
    total_pk_columns: int = 0
    total_fk_columns: int = 0
    total_issues: int = 0
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    issues_by_file: Dict[str, List[ColumnIssue]] = field(default_factory=dict)
    compliant_classes: List[str] = field(default_factory=list)
    non_compliant_classes: List[str] = field(default_factory=list)


class ORMAuditor:
    """
    Auditeur ORM industriel pour la détection des problèmes UUID/BIGINT.
    Utilise l'AST Python pour une analyse fiable et précise.
    """

    # Patterns de types interdits pour les identifiants
    FORBIDDEN_TYPES = {
        'Integer', 'BigInteger', 'SmallInteger',
        'BIGINT', 'INT', 'INTEGER', 'SMALLINT'
    }

    # Types acceptés pour les identifiants
    ACCEPTED_TYPES = {
        'UniversalUUID', 'UUID', 'GUID', 'String'  # String(36) for UUID
    }

    # Colonnes qui DOIVENT être UUID
    ID_COLUMN_PATTERNS = re.compile(r'^(id|.*_id)$', re.IGNORECASE)

    # Colonnes autorisées à être Integer (non-identifiants)
    ALLOWED_INTEGER_COLUMNS = {
        'sequence', 'level', 'priority', 'order', 'sort_order', 'count',
        'quantity', 'year', 'month', 'day', 'hour', 'minute', 'second',
        'file_size', 'size', 'version', 'retry_count', 'max_retries',
        'interventions_used', 'max_interventions', 'notice_period_days',
        'lead_time_days', 'response_time_hours', 'resolution_time_hours',
        'estimated_duration', 'actual_minutes', 'estimated_minutes',
        'frequency_value', 'cycle_count', 'current_cycles', 'expected_life',
        'useful_life', 'shelf_life', 'year_manufactured', 'is_active',
        'is_fully_validated', 'sync_version', 'last_sync_version',
        'wo_total', 'wo_preventive', 'wo_corrective', 'wo_completed',
        'wo_overdue', 'failure_count', 'work_order_backlog', 'total_sent',
        'total_delivered', 'total_failed', 'total_opened', 'total_clicked',
        'day_of_week', 'day_of_month', 'month_of_year', 'execution_number',
        'total_recipients', 'active_recipients', 'sent_count', 'delivered_count',
        'failed_count', 'bounced_count', 'opened_count', 'clicked_count',
        'click_count', 'unsubscribed_count', 'total_broadcasts', 'total_executions',
        'total_messages', 'digest_count', 'newsletter_count', 'report_count',
        'alert_count', 'email_count', 'in_app_count', 'webhook_count', 'sms_count',
    }

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.issues: List[ColumnIssue] = []
        self.report = AuditReport(timestamp=datetime.now().isoformat())
        self.processed_files: Set[str] = set()

    def _is_id_column(self, column_name: str) -> bool:
        """Vérifie si une colonne est un identifiant."""
        return bool(self.ID_COLUMN_PATTERNS.match(column_name))

    def _is_allowed_integer_column(self, column_name: str) -> bool:
        """Vérifie si une colonne peut légitimement être Integer."""
        col_lower = column_name.lower()
        # Les colonnes id ne sont JAMAIS autorisées en Integer
        if self._is_id_column(column_name):
            return False
        # Vérifier les colonnes autorisées
        return col_lower in self.ALLOWED_INTEGER_COLUMNS or any(
            pattern in col_lower for pattern in ['_count', '_total', '_number']
        )

    def _extract_column_type(self, call_node: ast.Call) -> Optional[str]:
        """Extrait le type d'une colonne depuis un noeud Column(...)."""
        if not call_node.args:
            return None

        first_arg = call_node.args[0]

        # Cas: Column(UniversalUUID(), ...)
        if isinstance(first_arg, ast.Call):
            if isinstance(first_arg.func, ast.Name):
                return first_arg.func.id
            elif isinstance(first_arg.func, ast.Attribute):
                return first_arg.func.attr

        # Cas: Column(Integer, ...)
        elif isinstance(first_arg, ast.Name):
            return first_arg.id

        # Cas: Column(sqlalchemy.Integer, ...)
        elif isinstance(first_arg, ast.Attribute):
            return first_arg.attr

        return None

    def _has_primary_key(self, call_node: ast.Call) -> bool:
        """Vérifie si Column() contient primary_key=True."""
        for keyword in call_node.keywords:
            if keyword.arg == 'primary_key':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value is True
                elif isinstance(keyword.value, ast.NameConstant):  # Python 3.7
                    return keyword.value.value is True
        return False

    def _has_autoincrement(self, call_node: ast.Call) -> bool:
        """Vérifie si Column() contient autoincrement=True."""
        for keyword in call_node.keywords:
            if keyword.arg == 'autoincrement':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value is True
                elif isinstance(keyword.value, ast.NameConstant):
                    return keyword.value.value is True
        return False

    def _has_foreign_key(self, call_node: ast.Call) -> bool:
        """Vérifie si Column() contient un ForeignKey(...)."""
        for arg in call_node.args:
            if isinstance(arg, ast.Call):
                if isinstance(arg.func, ast.Name) and arg.func.id == 'ForeignKey':
                    return True
                elif isinstance(arg.func, ast.Attribute) and arg.func.attr == 'ForeignKey':
                    return True
        return False

    def _has_sequence(self, call_node: ast.Call) -> bool:
        """Vérifie si Column() utilise une Sequence(...)."""
        for keyword in call_node.keywords:
            if keyword.arg in ('default', 'server_default'):
                if isinstance(keyword.value, ast.Call):
                    if isinstance(keyword.value.func, ast.Name):
                        if keyword.value.func.id == 'Sequence':
                            return True
        return False

    def _get_source_line(self, file_path: str, line_number: int) -> str:
        """Récupère la ligne source."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if 0 <= line_number - 1 < len(lines):
                    return lines[line_number - 1].strip()
        except Exception:
            pass
        return ""

    def _analyze_class(self, node: ast.ClassDef, file_path: str, source_lines: List[str]):
        """Analyse une classe SQLAlchemy pour les problèmes d'ID."""
        class_name = node.name
        is_sqlalchemy_model = False

        # Vérifier si c'est un modèle SQLAlchemy (hérite de Base ou a __tablename__)
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('Base', 'DeclarativeBase'):
                is_sqlalchemy_model = True
            elif isinstance(base, ast.Attribute):
                if base.attr in ('Base', 'DeclarativeBase'):
                    is_sqlalchemy_model = True

        # Chercher __tablename__
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        is_sqlalchemy_model = True

        if not is_sqlalchemy_model:
            return

        self.report.total_classes += 1
        class_has_issues = False

        # Analyser chaque attribut de la classe
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if not isinstance(target, ast.Name):
                        continue

                    column_name = target.id

                    # Vérifier si c'est un Column(...)
                    if not isinstance(item.value, ast.Call):
                        continue

                    call = item.value
                    func = call.func

                    # Vérifier que c'est Column()
                    is_column = False
                    if isinstance(func, ast.Name) and func.id == 'Column':
                        is_column = True
                    elif isinstance(func, ast.Attribute) and func.attr == 'Column':
                        is_column = True

                    if not is_column:
                        continue

                    self.report.total_columns += 1

                    # Extraire le type
                    col_type = self._extract_column_type(call)
                    is_pk = self._has_primary_key(call)
                    is_fk = self._has_foreign_key(call)
                    has_autoincrement = self._has_autoincrement(call)
                    has_sequence = self._has_sequence(call)

                    if is_pk:
                        self.report.total_pk_columns += 1
                    if is_fk:
                        self.report.total_fk_columns += 1

                    # === DÉTECTION DES PROBLÈMES ===

                    raw_line = self._get_source_line(file_path, item.lineno)

                    # 1. PK avec Integer/BigInteger
                    if is_pk and col_type in self.FORBIDDEN_TYPES:
                        issue = ColumnIssue(
                            file_path=str(file_path),
                            line_number=item.lineno,
                            class_name=class_name,
                            column_name=column_name,
                            current_type=col_type,
                            expected_type="UniversalUUID()",
                            issue_type="PK_INTEGER",
                            raw_line=raw_line
                        )
                        self.issues.append(issue)
                        class_has_issues = True

                    # 2. FK avec Integer/BigInteger
                    elif is_fk and col_type in self.FORBIDDEN_TYPES:
                        issue = ColumnIssue(
                            file_path=str(file_path),
                            line_number=item.lineno,
                            class_name=class_name,
                            column_name=column_name,
                            current_type=col_type,
                            expected_type="UniversalUUID()",
                            issue_type="FK_INTEGER",
                            raw_line=raw_line
                        )
                        self.issues.append(issue)
                        class_has_issues = True

                    # 3. Colonne *_id avec Integer (même sans FK déclarée)
                    elif self._is_id_column(column_name) and col_type in self.FORBIDDEN_TYPES:
                        if not self._is_allowed_integer_column(column_name):
                            issue = ColumnIssue(
                                file_path=str(file_path),
                                line_number=item.lineno,
                                class_name=class_name,
                                column_name=column_name,
                                current_type=col_type,
                                expected_type="UniversalUUID()",
                                issue_type="ID_COLUMN_INTEGER",
                                raw_line=raw_line
                            )
                            self.issues.append(issue)
                            class_has_issues = True

                    # 4. autoincrement=True sur colonne id
                    if has_autoincrement and self._is_id_column(column_name):
                        issue = ColumnIssue(
                            file_path=str(file_path),
                            line_number=item.lineno,
                            class_name=class_name,
                            column_name=column_name,
                            current_type=f"{col_type} + autoincrement",
                            expected_type="UniversalUUID() + default=uuid.uuid4",
                            issue_type="AUTOINCREMENT",
                            raw_line=raw_line
                        )
                        self.issues.append(issue)
                        class_has_issues = True

                    # 5. Sequence sur colonne id
                    if has_sequence and self._is_id_column(column_name):
                        issue = ColumnIssue(
                            file_path=str(file_path),
                            line_number=item.lineno,
                            class_name=class_name,
                            column_name=column_name,
                            current_type=f"{col_type} + Sequence",
                            expected_type="UniversalUUID() + default=uuid.uuid4",
                            issue_type="SEQUENCE",
                            raw_line=raw_line
                        )
                        self.issues.append(issue)
                        class_has_issues = True

        # Enregistrer le statut de la classe
        if class_has_issues:
            self.report.non_compliant_classes.append(f"{file_path}:{class_name}")
        else:
            self.report.compliant_classes.append(f"{file_path}:{class_name}")

    def analyze_file(self, file_path: Path) -> None:
        """Analyse un fichier Python pour les modèles ORM."""
        if str(file_path) in self.processed_files:
            return

        self.processed_files.add(str(file_path))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                source_lines = source.splitlines()

            tree = ast.parse(source, filename=str(file_path))

            self.report.total_files += 1

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._analyze_class(node, file_path, source_lines)

        except SyntaxError as e:
            print(f"[WARN] Erreur syntaxe dans {file_path}: {e}")
        except Exception as e:
            print(f"[WARN] Erreur lecture {file_path}: {e}")

    def scan_directory(self, patterns: List[str] = None) -> None:
        """Scanne récursivement le répertoire pour les fichiers modèles."""
        if patterns is None:
            patterns = ['**/models.py', '**/model.py', '**/models/*.py']

        for pattern in patterns:
            for file_path in self.base_path.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith('__'):
                    self.analyze_file(file_path)

        # Aussi scanner tous les .py pour les modèles inline
        for file_path in self.base_path.rglob('*.py'):
            if file_path.is_file() and 'test' not in str(file_path).lower():
                self.analyze_file(file_path)

    def generate_report(self) -> str:
        """Génère le rapport d'audit textuel."""
        self.report.total_issues = len(self.issues)

        # Compter les issues par type
        for issue in self.issues:
            self.report.issues_by_type[issue.issue_type] = \
                self.report.issues_by_type.get(issue.issue_type, 0) + 1

        # Grouper par fichier
        for issue in self.issues:
            if issue.file_path not in self.report.issues_by_file:
                self.report.issues_by_file[issue.file_path] = []
            self.report.issues_by_file[issue.file_path].append(issue)

        lines = []
        lines.append("=" * 80)
        lines.append("AZALS - AUDIT ORM IDS - RAPPORT INDUSTRIEL")
        lines.append("=" * 80)
        lines.append(f"Date: {self.report.timestamp}")
        lines.append(f"Répertoire analysé: {self.base_path}")
        lines.append("")

        # Statistiques
        lines.append("-" * 80)
        lines.append("STATISTIQUES GLOBALES")
        lines.append("-" * 80)
        lines.append(f"Fichiers analysés:        {self.report.total_files}")
        lines.append(f"Classes ORM détectées:    {self.report.total_classes}")
        lines.append(f"Colonnes analysées:       {self.report.total_columns}")
        lines.append(f"  - Clés primaires:       {self.report.total_pk_columns}")
        lines.append(f"  - Clés étrangères:      {self.report.total_fk_columns}")
        lines.append("")
        lines.append(f"Classes conformes:        {len(self.report.compliant_classes)}")
        lines.append(f"Classes NON conformes:    {len(self.report.non_compliant_classes)}")
        lines.append(f"ERREURS CRITIQUES:        {self.report.total_issues}")
        lines.append("")

        # Résumé par type d'erreur
        if self.report.issues_by_type:
            lines.append("-" * 80)
            lines.append("ERREURS PAR TYPE")
            lines.append("-" * 80)
            for issue_type, count in sorted(self.report.issues_by_type.items()):
                lines.append(f"  {issue_type}: {count}")
            lines.append("")

        # Détails des erreurs
        if self.issues:
            lines.append("-" * 80)
            lines.append("DÉTAILS DES ERREURS CRITIQUES")
            lines.append("-" * 80)

            for file_path, file_issues in sorted(self.report.issues_by_file.items()):
                rel_path = os.path.relpath(file_path, self.base_path)
                lines.append(f"\n📁 {rel_path}")
                lines.append("-" * 60)

                for issue in file_issues:
                    lines.append(f"  Ligne {issue.line_number}: {issue.class_name}.{issue.column_name}")
                    lines.append(f"    Type actuel:   {issue.current_type}")
                    lines.append(f"    Type attendu:  {issue.expected_type}")
                    lines.append(f"    Problème:      {issue.issue_type}")
                    if issue.raw_line:
                        lines.append(f"    Code:          {issue.raw_line[:80]}...")
                    lines.append("")

        # Statut final
        lines.append("=" * 80)
        if self.report.total_issues == 0:
            lines.append("✅ STATUT: SUCCÈS - Tous les modèles sont conformes UUID")
            lines.append("")
            lines.append("Le projet peut démarrer avec le verrou anti-régression activé.")
        else:
            lines.append("❌ STATUT: ÉCHEC CRITIQUE")
            lines.append("")
            lines.append(f"{self.report.total_issues} erreur(s) détectée(s).")
            lines.append("Le projet NE PEUT PAS démarrer avec le verrou anti-régression.")
            lines.append("")
            lines.append("ACTION REQUISE: Exécuter scripts/fix_orm_ids.py")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """Génère le rapport au format JSON."""
        self.report.total_issues = len(self.issues)

        for issue in self.issues:
            self.report.issues_by_type[issue.issue_type] = \
                self.report.issues_by_type.get(issue.issue_type, 0) + 1

        # Convertir les issues en dict
        issues_list = [asdict(issue) for issue in self.issues]

        report_dict = {
            "timestamp": self.report.timestamp,
            "base_path": str(self.base_path),
            "statistics": {
                "total_files": self.report.total_files,
                "total_classes": self.report.total_classes,
                "total_columns": self.report.total_columns,
                "total_pk_columns": self.report.total_pk_columns,
                "total_fk_columns": self.report.total_fk_columns,
                "compliant_classes": len(self.report.compliant_classes),
                "non_compliant_classes": len(self.report.non_compliant_classes),
                "total_issues": self.report.total_issues,
            },
            "issues_by_type": self.report.issues_by_type,
            "issues": issues_list,
            "compliant_classes": self.report.compliant_classes,
            "non_compliant_classes": self.report.non_compliant_classes,
            "status": "SUCCESS" if self.report.total_issues == 0 else "FAILURE"
        }

        return json.dumps(report_dict, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="AZALS - Audit ORM IDs - Détection des problèmes UUID/BIGINT"
    )
    parser.add_argument(
        '--path', '-p',
        default='app',
        help='Chemin du répertoire à analyser (défaut: app)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Fichier de sortie pour le rapport'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Générer le rapport au format JSON'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbose'
    )

    args = parser.parse_args()

    # Déterminer le chemin de base
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    base_path = project_root / args.path

    if not base_path.exists():
        print(f"[ERREUR] Répertoire non trouvé: {base_path}")
        sys.exit(1)

    print(f"[AUDIT] Analyse des modèles ORM dans {base_path}...")

    # Exécuter l'audit
    auditor = ORMAuditor(base_path)
    auditor.scan_directory()

    # Générer le rapport
    if args.json:
        report = auditor.generate_json_report()
    else:
        report = auditor.generate_report()

    # Afficher ou sauvegarder
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[AUDIT] Rapport sauvegardé: {output_path}")
    else:
        print(report)

    # Code de sortie
    if auditor.report.total_issues > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
