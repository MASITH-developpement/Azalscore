#!/usr/bin/env python3
"""
AZALS - Fix ORM IDs - Script de Correction Automatique Industriel
==================================================================
Corrige automatiquement tous les problèmes UUID/BIGINT dans les modèles ORM.

Ce script lit le rapport d'audit (ou exécute l'audit) et applique les corrections
de manière chirurgicale sans modifier la logique métier.

CORRECTIONS APPLIQUÉES:
1. Column(Integer, primary_key=True) → Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
2. Column(BigInteger, primary_key=True) → Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
3. Column(Integer, ForeignKey(...)) → Column(UniversalUUID(), ForeignKey(...))
4. autoincrement=True → supprimé + default=uuid.uuid4 ajouté
5. Sequence(...) → supprimé + default=uuid.uuid4 ajouté

IMPORTS AJOUTÉS AUTOMATIQUEMENT:
- from app.core.types import UniversalUUID
- import uuid

Usage:
    python scripts/fix_orm_ids.py
    python scripts/fix_orm_ids.py --dry-run
    python scripts/fix_orm_ids.py --input audit_report.json
    python scripts/fix_orm_ids.py --backup
"""

import ast
import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime


@dataclass
class Correction:
    """Représente une correction à appliquer."""
    file_path: str
    line_number: int
    old_line: str
    new_line: str
    correction_type: str
    class_name: str
    column_name: str


@dataclass
class FixReport:
    """Rapport de correction."""
    timestamp: str
    total_files_modified: int = 0
    total_corrections: int = 0
    corrections_by_type: Dict[str, int] = field(default_factory=dict)
    corrections_by_file: Dict[str, List[Correction]] = field(default_factory=dict)
    import_fixes: Dict[str, List[str]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ORMFixer:
    """
    Correcteur ORM industriel pour les problèmes UUID/BIGINT.
    Applique des corrections chirurgicales préservant la structure du code.
    """

    # Types à remplacer
    TYPES_TO_REPLACE = {
        'Integer': 'UniversalUUID()',
        'BigInteger': 'UniversalUUID()',
        'SmallInteger': 'UniversalUUID()',
        'BIGINT': 'UniversalUUID()',
        'INT': 'UniversalUUID()',
        'INTEGER': 'UniversalUUID()',
    }

    # Regex pour détecter les colonnes problématiques
    PK_PATTERN = re.compile(
        r'(\s*)(\w+)\s*=\s*Column\(\s*(Integer|BigInteger|SmallInteger)\s*,'
        r'([^)]*primary_key\s*=\s*True[^)]*)\)',
        re.MULTILINE
    )

    FK_PATTERN = re.compile(
        r'(\s*)(\w+)\s*=\s*Column\(\s*(Integer|BigInteger)\s*,'
        r'([^)]*ForeignKey\([^)]+\)[^)]*)\)',
        re.MULTILINE
    )

    ID_COLUMN_PATTERN = re.compile(
        r'(\s*)(\w*_?id)\s*=\s*Column\(\s*(Integer|BigInteger)\s*,([^)]*)\)',
        re.MULTILINE | re.IGNORECASE
    )

    AUTOINCREMENT_PATTERN = re.compile(
        r',?\s*autoincrement\s*=\s*True\s*,?'
    )

    SEQUENCE_PATTERN = re.compile(
        r',?\s*(default|server_default)\s*=\s*Sequence\([^)]+\)\s*,?'
    )

    # Imports requis
    REQUIRED_IMPORTS = {
        'uuid': 'import uuid',
        'UniversalUUID': 'from app.core.types import UniversalUUID',
    }

    def __init__(self, base_path: str, dry_run: bool = False, backup: bool = True):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.backup = backup
        self.corrections: List[Correction] = []
        self.report = FixReport(timestamp=datetime.now().isoformat())
        self.processed_files: Set[str] = set()

    def _backup_file(self, file_path: Path) -> Optional[Path]:
        """Crée une sauvegarde du fichier."""
        if not self.backup:
            return None

        backup_dir = self.base_path.parent / 'backups' / 'orm_fix'
        backup_dir.mkdir(parents=True, exist_ok=True)

        rel_path = file_path.relative_to(self.base_path)
        backup_path = backup_dir / f"{rel_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _check_imports(self, content: str) -> Tuple[bool, bool]:
        """Vérifie les imports nécessaires."""
        has_uuid = 'import uuid' in content or 'from uuid import' in content
        has_universal_uuid = 'UniversalUUID' in content and (
            'from app.core.types import' in content or
            'import UniversalUUID' in content
        )
        return has_uuid, has_universal_uuid

    def _add_missing_imports(self, content: str, file_path: str) -> str:
        """Ajoute les imports manquants."""
        has_uuid, has_universal_uuid = self._check_imports(content)
        imports_to_add = []

        if not has_uuid:
            imports_to_add.append('import uuid')
            if file_path not in self.report.import_fixes:
                self.report.import_fixes[file_path] = []
            self.report.import_fixes[file_path].append('import uuid')

        if not has_universal_uuid:
            imports_to_add.append('from app.core.types import UniversalUUID')
            if file_path not in self.report.import_fixes:
                self.report.import_fixes[file_path] = []
            self.report.import_fixes[file_path].append('from app.core.types import UniversalUUID')

        if imports_to_add:
            # Trouver le meilleur endroit pour insérer les imports
            lines = content.split('\n')
            insert_index = 0

            # Chercher après les docstrings et les imports existants
            in_docstring = False
            for i, line in enumerate(lines):
                stripped = line.strip()

                # Gérer les docstrings multi-lignes
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_docstring:
                        in_docstring = False
                    elif stripped.count('"""') == 1 or stripped.count("'''") == 1:
                        in_docstring = True

                if in_docstring:
                    continue

                # Après les imports existants
                if stripped.startswith('import ') or stripped.startswith('from '):
                    insert_index = i + 1
                elif stripped and not stripped.startswith('#') and insert_index > 0:
                    break

            # Insérer les nouveaux imports
            for imp in imports_to_add:
                lines.insert(insert_index, imp)
                insert_index += 1

            content = '\n'.join(lines)

        return content

    def _fix_pk_column(self, match: re.Match, file_path: str, class_name: str = "") -> str:
        """Corrige une clé primaire Integer."""
        indent = match.group(1)
        col_name = match.group(2)
        old_type = match.group(3)
        rest = match.group(4)

        # Supprimer autoincrement
        rest = self.AUTOINCREMENT_PATTERN.sub('', rest)
        # Supprimer Sequence
        rest = self.SEQUENCE_PATTERN.sub('', rest)

        # Ajouter default=uuid.uuid4 si absent
        if 'default=' not in rest and 'default =' not in rest:
            rest = rest.rstrip(', ') + ', default=uuid.uuid4'

        # Nettoyer les virgules doubles
        rest = re.sub(r',\s*,', ',', rest)
        rest = rest.strip(', ')

        new_line = f"{indent}{col_name} = Column(UniversalUUID(), {rest})"

        correction = Correction(
            file_path=file_path,
            line_number=0,  # Will be calculated later
            old_line=match.group(0),
            new_line=new_line,
            correction_type="PK_TO_UUID",
            class_name=class_name,
            column_name=col_name
        )
        self.corrections.append(correction)

        return new_line

    def _fix_fk_column(self, match: re.Match, file_path: str, class_name: str = "") -> str:
        """Corrige une clé étrangère Integer."""
        indent = match.group(1)
        col_name = match.group(2)
        old_type = match.group(3)
        rest = match.group(4)

        new_line = f"{indent}{col_name} = Column(UniversalUUID(), {rest.strip()})"

        correction = Correction(
            file_path=file_path,
            line_number=0,
            old_line=match.group(0),
            new_line=new_line,
            correction_type="FK_TO_UUID",
            class_name=class_name,
            column_name=col_name
        )
        self.corrections.append(correction)

        return new_line

    def _fix_id_column(self, match: re.Match, file_path: str, class_name: str = "") -> str:
        """Corrige une colonne *_id Integer."""
        indent = match.group(1)
        col_name = match.group(2)
        old_type = match.group(3)
        rest = match.group(4)

        # Ne pas corriger les colonnes autorisées en Integer
        if self._is_allowed_integer_column(col_name):
            return match.group(0)

        new_line = f"{indent}{col_name} = Column(UniversalUUID(), {rest.strip()})"

        correction = Correction(
            file_path=file_path,
            line_number=0,
            old_line=match.group(0),
            new_line=new_line,
            correction_type="ID_TO_UUID",
            class_name=class_name,
            column_name=col_name
        )
        self.corrections.append(correction)

        return new_line

    def _is_allowed_integer_column(self, column_name: str) -> bool:
        """Vérifie si une colonne peut légitimement être Integer."""
        # Liste des patterns autorisés (non-identifiants)
        allowed_patterns = {
            'sequence', 'level', 'priority', 'order', 'sort_order', 'count',
            'quantity', 'year', 'month', 'day', 'hour', 'minute', 'second',
            'file_size', 'size', 'version', 'retry_count', 'max_retries',
            'day_of_week', 'day_of_month', 'month_of_year', 'execution_number',
        }

        col_lower = column_name.lower()

        # Les colonnes 'id' ou '*_id' ne sont JAMAIS autorisées en Integer
        if col_lower == 'id' or col_lower.endswith('_id'):
            return False

        return col_lower in allowed_patterns

    def _extract_class_context(self, content: str, match_start: int) -> str:
        """Extrait le nom de la classe contenant le match."""
        before_match = content[:match_start]
        class_pattern = re.compile(r'class\s+(\w+)\s*[:\(]', re.MULTILINE)

        matches = list(class_pattern.finditer(before_match))
        if matches:
            return matches[-1].group(1)
        return ""

    def fix_file(self, file_path: Path) -> bool:
        """Corrige un fichier Python."""
        if str(file_path) in self.processed_files:
            return False

        self.processed_files.add(str(file_path))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            self.report.errors.append(f"Erreur lecture {file_path}: {e}")
            return False

        content = original_content
        file_modified = False

        # 1. Corriger les PK Integer
        def pk_replacer(m):
            nonlocal file_modified
            class_name = self._extract_class_context(content, m.start())
            file_modified = True
            return self._fix_pk_column(m, str(file_path), class_name)

        content = self.PK_PATTERN.sub(pk_replacer, content)

        # 2. Corriger les FK Integer
        def fk_replacer(m):
            nonlocal file_modified
            class_name = self._extract_class_context(content, m.start())
            file_modified = True
            return self._fix_fk_column(m, str(file_path), class_name)

        content = self.FK_PATTERN.sub(fk_replacer, content)

        # 3. Corriger les colonnes *_id Integer (sans FK explicite)
        def id_replacer(m):
            nonlocal file_modified
            col_name = m.group(2)
            if self._is_allowed_integer_column(col_name):
                return m.group(0)
            class_name = self._extract_class_context(content, m.start())
            file_modified = True
            return self._fix_id_column(m, str(file_path), class_name)

        content = self.ID_COLUMN_PATTERN.sub(id_replacer, content)

        # 4. Ajouter les imports manquants si des modifications ont été faites
        if file_modified:
            content = self._add_missing_imports(content, str(file_path))

        # Appliquer les modifications
        if file_modified and content != original_content:
            if not self.dry_run:
                # Backup
                if self.backup:
                    self._backup_file(file_path)

                # Écrire le fichier corrigé
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            self.report.total_files_modified += 1

            # Enregistrer les corrections par fichier
            if str(file_path) not in self.report.corrections_by_file:
                self.report.corrections_by_file[str(file_path)] = []

            for corr in self.corrections:
                if corr.file_path == str(file_path):
                    self.report.corrections_by_file[str(file_path)].append(corr)
                    self.report.corrections_by_type[corr.correction_type] = \
                        self.report.corrections_by_type.get(corr.correction_type, 0) + 1

            return True

        return False

    def scan_and_fix(self, patterns: List[str] = None) -> None:
        """Scanne et corrige tous les fichiers."""
        if patterns is None:
            patterns = ['**/models.py', '**/model.py', '**/models/*.py']

        files_to_process = set()

        for pattern in patterns:
            for file_path in self.base_path.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith('__'):
                    files_to_process.add(file_path)

        # Aussi scanner tous les .py pour les modèles inline
        for file_path in self.base_path.rglob('*.py'):
            if file_path.is_file() and 'test' not in str(file_path).lower():
                files_to_process.add(file_path)

        print(f"[FIX] Analyse de {len(files_to_process)} fichiers...")

        for file_path in sorted(files_to_process):
            self.fix_file(file_path)

        self.report.total_corrections = len(self.corrections)

    def generate_report(self) -> str:
        """Génère le rapport de correction."""
        lines = []
        lines.append("=" * 80)
        lines.append("AZALS - FIX ORM IDS - RAPPORT DE CORRECTION")
        lines.append("=" * 80)
        lines.append(f"Date: {self.report.timestamp}")
        lines.append(f"Mode: {'DRY-RUN (simulation)' if self.dry_run else 'PRODUCTION'}")
        lines.append(f"Backup: {'Activé' if self.backup else 'Désactivé'}")
        lines.append("")

        # Statistiques
        lines.append("-" * 80)
        lines.append("RÉSUMÉ DES CORRECTIONS")
        lines.append("-" * 80)
        lines.append(f"Fichiers modifiés:      {self.report.total_files_modified}")
        lines.append(f"Corrections appliquées: {self.report.total_corrections}")
        lines.append("")

        # Par type
        if self.report.corrections_by_type:
            lines.append("Par type de correction:")
            for corr_type, count in sorted(self.report.corrections_by_type.items()):
                lines.append(f"  {corr_type}: {count}")
            lines.append("")

        # Imports ajoutés
        if self.report.import_fixes:
            lines.append("-" * 80)
            lines.append("IMPORTS AJOUTÉS")
            lines.append("-" * 80)
            for file_path, imports in self.report.import_fixes.items():
                rel_path = os.path.relpath(file_path, self.base_path)
                lines.append(f"📁 {rel_path}")
                for imp in imports:
                    lines.append(f"    + {imp}")
            lines.append("")

        # Détails des corrections
        if self.report.corrections_by_file:
            lines.append("-" * 80)
            lines.append("DÉTAILS DES CORRECTIONS")
            lines.append("-" * 80)

            for file_path, file_corrections in sorted(self.report.corrections_by_file.items()):
                rel_path = os.path.relpath(file_path, self.base_path)
                lines.append(f"\n📁 {rel_path}")
                lines.append("-" * 60)

                for corr in file_corrections:
                    lines.append(f"  {corr.class_name}.{corr.column_name} [{corr.correction_type}]")
                    lines.append(f"    - {corr.old_line.strip()[:70]}...")
                    lines.append(f"    + {corr.new_line.strip()[:70]}...")
                    lines.append("")

        # Erreurs
        if self.report.errors:
            lines.append("-" * 80)
            lines.append("ERREURS")
            lines.append("-" * 80)
            for error in self.report.errors:
                lines.append(f"  ⚠ {error}")
            lines.append("")

        # Statut final
        lines.append("=" * 80)
        if self.report.total_corrections == 0:
            lines.append("✅ AUCUNE CORRECTION NÉCESSAIRE")
            lines.append("   Les modèles sont déjà conformes aux règles UUID.")
        elif self.dry_run:
            lines.append(f"🔍 DRY-RUN: {self.report.total_corrections} correction(s) à appliquer")
            lines.append("   Relancer sans --dry-run pour appliquer les modifications.")
        else:
            lines.append(f"✅ {self.report.total_corrections} CORRECTION(S) APPLIQUÉE(S)")
            lines.append("   Relancer scripts/audit_orm_ids.py pour vérification.")
        lines.append("=" * 80)

        return "\n".join(lines)


def run_audit_first(base_path: Path) -> Dict:
    """Exécute l'audit et retourne le rapport JSON."""
    import subprocess

    audit_script = base_path.parent / 'scripts' / 'audit_orm_ids.py'
    if not audit_script.exists():
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), '--json', '--path', str(base_path)],
            capture_output=True,
            text=True,
            cwd=str(base_path.parent)
        )
        if result.stdout:
            return json.loads(result.stdout)
    except Exception:
        pass

    return None


def main():
    parser = argparse.ArgumentParser(
        description="AZALS - Fix ORM IDs - Correction automatique des problèmes UUID/BIGINT"
    )
    parser.add_argument(
        '--path', '-p',
        default='app',
        help='Chemin du répertoire à corriger (défaut: app)'
    )
    parser.add_argument(
        '--input', '-i',
        help='Fichier JSON d\'audit en entrée (optionnel)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Fichier de sortie pour le rapport'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Mode simulation (aucune modification)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Désactiver les sauvegardes'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Forcer la correction sans confirmation'
    )

    args = parser.parse_args()

    # Déterminer le chemin de base
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    base_path = project_root / args.path

    if not base_path.exists():
        print(f"[ERREUR] Répertoire non trouvé: {base_path}")
        sys.exit(1)

    # Afficher le mode
    if args.dry_run:
        print("[FIX] Mode DRY-RUN activé (simulation uniquement)")
    else:
        print("[FIX] Mode PRODUCTION - Les fichiers seront modifiés")

    if not args.no_backup:
        print("[FIX] Les fichiers originaux seront sauvegardés")

    # Confirmation
    if not args.dry_run and not args.force:
        response = input("\nContinuer avec les corrections? [y/N] ")
        if response.lower() != 'y':
            print("[FIX] Annulé par l'utilisateur")
            sys.exit(0)

    # Exécuter les corrections
    fixer = ORMFixer(
        base_path=base_path,
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    fixer.scan_and_fix()

    # Générer le rapport
    report = fixer.generate_report()

    # Afficher ou sauvegarder
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[FIX] Rapport sauvegardé: {output_path}")
    else:
        print(report)

    # Code de sortie
    if fixer.report.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
