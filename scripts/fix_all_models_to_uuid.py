#!/usr/bin/env python3
"""
AZALS - Fix All Models to UUID - Script Industriel DÉFINITIF
=============================================================
Corrige AUTOMATIQUEMENT et IRRÉVERSIBLEMENT tous les modèles ORM
pour utiliser UUID au lieu de Integer/BigInteger.

OPÉRATIONS EFFECTUÉES:
1. Supprime toute définition manuelle de 'id' avec Integer/BigInteger
2. Remplace TOUS les Column(Integer/BigInteger) pour FK par UUID
3. Corrige TOUTES les colonnes *_id, parent_id, tenant_id, user_id, etc.
4. Ajoute les imports nécessaires
5. Met à jour l'héritage pour utiliser la Base unifiée

GARANTIES:
- NE MODIFIE JAMAIS les noms de tables
- NE MODIFIE JAMAIS les noms de colonnes
- NE MODIFIE JAMAIS la logique métier
- NE MODIFIE JAMAIS les relationships
- PRÉSERVE toute la structure existante

Usage:
    python scripts/fix_all_models_to_uuid.py
    python scripts/fix_all_models_to_uuid.py --dry-run
    python scripts/fix_all_models_to_uuid.py --backup
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional


@dataclass
class FileModification:
    """Représente les modifications d'un fichier."""
    file_path: str
    original_content: str
    new_content: str
    changes: List[str] = field(default_factory=list)
    imports_added: List[str] = field(default_factory=list)


@dataclass
class FixReport:
    """Rapport de correction."""
    timestamp: str = ""
    files_analyzed: int = 0
    files_modified: int = 0
    pk_columns_fixed: int = 0
    fk_columns_fixed: int = 0
    id_columns_fixed: int = 0
    imports_added: int = 0
    base_imports_fixed: int = 0
    errors: List[str] = field(default_factory=list)
    modifications: List[FileModification] = field(default_factory=list)


class UUIDModelFixer:
    """
    Correcteur industriel pour la migration UUID.
    Transforme TOUS les modèles ORM de Integer/BigInteger vers UUID.
    """

    # =====================================================================
    # PATTERNS DE DÉTECTION
    # =====================================================================

    # Pattern pour détecter les définitions de PK Integer
    PK_INTEGER_PATTERN = re.compile(
        r'^(\s*)id\s*=\s*Column\s*\(\s*'
        r'(Integer|BigInteger|SmallInteger|INT|BIGINT)'
        r'([^)]*)'
        r'primary_key\s*=\s*True'
        r'([^)]*)\)',
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern alternatif PK
    PK_INTEGER_PATTERN_ALT = re.compile(
        r'^(\s*)id\s*=\s*Column\s*\(\s*'
        r'(Integer|BigInteger|SmallInteger|INT|BIGINT)\s*,'
        r'([^)]*)\)',
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern pour les FK colonnes (any *_id column with Integer)
    FK_INTEGER_PATTERN = re.compile(
        r'^(\s*)(\w+_id)\s*=\s*Column\s*\(\s*'
        r'(Integer|BigInteger)'
        r'(\s*,\s*ForeignKey\s*\([^)]+\))?'
        r'([^)]*)\)',
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern pour parent_id, tenant_id, user_id, etc.
    SPECIAL_ID_PATTERN = re.compile(
        r'^(\s*)(parent_id|tenant_id|user_id|owner_id|created_by_id|'
        r'updated_by_id|assigned_to_id|manager_id|supervisor_id|'
        r'company_id|organization_id|department_id|team_id|'
        r'customer_id|supplier_id|vendor_id|partner_id|'
        r'project_id|task_id|order_id|invoice_id|'
        r'category_id|type_id|status_id|priority_id|'
        r'source_id|target_id|origin_id|destination_id|'
        r'asset_id|product_id|item_id|resource_id|'
        r'document_id|file_id|attachment_id|'
        r'session_id|token_id|key_id|'
        r'workflow_id|step_id|stage_id|'
        r'[a-z_]+_id)\s*=\s*Column\s*\(\s*'
        r'(Integer|BigInteger)'
        r'([^)]*)\)',
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern pour détecter l'import de Base actuel
    BASE_IMPORT_PATTERNS = [
        re.compile(r'^from\s+app\.core\.database\s+import.*\bBase\b', re.MULTILINE),
        re.compile(r'^from\s+sqlalchemy\.orm\s+import.*\bdeclarative_base\b', re.MULTILINE),
        re.compile(r'^from\s+sqlalchemy\.ext\.declarative\s+import.*\bdeclarative_base\b', re.MULTILINE),
    ]

    # Pattern pour détecter les imports existants
    UUID_IMPORT_PATTERN = re.compile(
        r'^from\s+sqlalchemy\.dialects\.postgresql\s+import.*\bUUID\b',
        re.MULTILINE
    )
    UUID_MODULE_IMPORT_PATTERN = re.compile(r'^import\s+uuid\b', re.MULTILINE)

    # Pattern pour Sequence et autoincrement
    SEQUENCE_PATTERN = re.compile(r',?\s*Sequence\s*\([^)]+\)\s*,?', re.IGNORECASE)
    AUTOINCREMENT_PATTERN = re.compile(r',?\s*autoincrement\s*=\s*True\s*,?', re.IGNORECASE)
    SERVER_DEFAULT_SEQ_PATTERN = re.compile(
        r',?\s*server_default\s*=\s*["\']?nextval[^,)]+["\']?\s*,?',
        re.IGNORECASE
    )

    # Types interdits
    FORBIDDEN_TYPES = {'Integer', 'BigInteger', 'SmallInteger', 'INT', 'BIGINT', 'SERIAL', 'BIGSERIAL'}

    # Colonnes autorisées en Integer (non-identifiants)
    ALLOWED_INTEGER_COLUMNS = {
        'sequence', 'seq', 'level', 'priority', 'order', 'sort_order', 'position',
        'count', 'quantity', 'qty', 'amount', 'total',
        'year', 'month', 'day', 'hour', 'minute', 'second', 'week',
        'day_of_week', 'day_of_month', 'month_of_year',
        'file_size', 'size', 'length', 'width', 'height', 'weight',
        'version', 'revision', 'build', 'patch',
        'retry_count', 'attempt_count', 'max_retries', 'max_attempts',
        'duration', 'duration_seconds', 'duration_minutes', 'duration_hours',
        'estimated_minutes', 'actual_minutes', 'estimated_hours', 'actual_hours',
        'age', 'years', 'months', 'days', 'hours', 'minutes', 'seconds',
        'rating', 'score', 'points', 'stars',
        'page', 'page_number', 'line_number', 'row_number',
        'index', 'offset', 'limit',
        'is_active', 'is_enabled', 'is_deleted', 'is_validated', 'is_fully_validated',
        'status_code', 'error_code', 'response_code',
        'port', 'timeout', 'interval', 'frequency',
        'min_value', 'max_value', 'default_value',
        'decimal_places', 'precision', 'scale',
        'children_count', 'items_count', 'records_count',
        'sync_version', 'last_sync_version',
    }

    def __init__(self, base_path: str, dry_run: bool = False, backup: bool = True):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.backup = backup
        self.report = FixReport(timestamp=datetime.now().isoformat())
        self.backup_dir: Optional[Path] = None

    def _is_allowed_integer_column(self, column_name: str) -> bool:
        """Vérifie si une colonne peut légitimement être Integer."""
        col_lower = column_name.lower()

        # Les colonnes *_id ne sont JAMAIS autorisées en Integer
        if col_lower == 'id' or col_lower.endswith('_id'):
            return False

        # Vérifier les patterns autorisés
        return col_lower in self.ALLOWED_INTEGER_COLUMNS or any(
            pattern in col_lower for pattern in [
                '_count', '_total', '_number', '_qty', '_amount',
                '_size', '_length', '_duration', '_interval'
            ]
        )

    def _create_backup(self) -> Path:
        """Crée le répertoire de backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.base_path.parent / 'backups' / f'uuid_fix_{timestamp}'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        return self.backup_dir

    def _backup_file(self, file_path: Path) -> Optional[Path]:
        """Sauvegarde un fichier."""
        if not self.backup or not self.backup_dir:
            return None

        rel_path = file_path.relative_to(self.base_path)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def _fix_pk_column(self, content: str, modifications: List[str]) -> str:
        """Supprime les définitions de PK Integer et laisse UUIDMixin gérer."""

        def pk_replacer(match):
            indent = match.group(1)
            modifications.append(f"SUPPRIMÉ: définition manuelle de 'id' (Integer PK)")
            # Retourner un commentaire indiquant que id est géré par UUIDMixin
            return f"{indent}# id géré automatiquement par UUIDMixin (UUID)"

        content = self.PK_INTEGER_PATTERN.sub(pk_replacer, content)
        content = self.PK_INTEGER_PATTERN_ALT.sub(pk_replacer, content)

        return content

    def _fix_fk_columns(self, content: str, modifications: List[str]) -> str:
        """Corrige toutes les FK Integer en UUID."""

        def fk_replacer(match):
            indent = match.group(1)
            col_name = match.group(2)
            old_type = match.group(3)
            fk_part = match.group(4) or ''
            rest = match.group(5) or ''

            # Supprimer autoincrement et Sequence
            rest = self.AUTOINCREMENT_PATTERN.sub('', rest)
            rest = self.SEQUENCE_PATTERN.sub('', rest)
            rest = self.SERVER_DEFAULT_SEQ_PATTERN.sub('', rest)

            # Nettoyer les virgules doubles
            rest = re.sub(r',\s*,', ',', rest)
            rest = rest.strip(', ')

            # Construire la nouvelle définition
            if fk_part:
                new_line = f"{indent}{col_name} = Column(UUID(as_uuid=True){fk_part}"
                if rest:
                    new_line += f", {rest}"
                new_line += ")"
            else:
                # FK implicite (pas de ForeignKey explicite mais c'est une _id column)
                new_line = f"{indent}{col_name} = Column(UUID(as_uuid=True)"
                if rest:
                    new_line += f", {rest}"
                new_line += ")"

            modifications.append(f"FK: {col_name} : {old_type} → UUID")
            return new_line

        content = self.FK_INTEGER_PATTERN.sub(fk_replacer, content)
        return content

    def _fix_special_id_columns(self, content: str, modifications: List[str]) -> str:
        """Corrige les colonnes spéciales (*_id) en UUID."""

        def special_replacer(match):
            indent = match.group(1)
            col_name = match.group(2)
            old_type = match.group(3)
            rest = match.group(4) or ''

            # Ne pas corriger les colonnes autorisées en Integer
            if self._is_allowed_integer_column(col_name):
                return match.group(0)

            # Supprimer autoincrement et Sequence
            rest = self.AUTOINCREMENT_PATTERN.sub('', rest)
            rest = self.SEQUENCE_PATTERN.sub('', rest)
            rest = self.SERVER_DEFAULT_SEQ_PATTERN.sub('', rest)

            # Nettoyer
            rest = re.sub(r',\s*,', ',', rest)
            rest = rest.strip(', ')

            # Construire la nouvelle définition
            new_line = f"{indent}{col_name} = Column(UUID(as_uuid=True)"
            if rest:
                new_line += f", {rest}"
            new_line += ")"

            modifications.append(f"ID_COL: {col_name} : {old_type} → UUID")
            return new_line

        content = self.SPECIAL_ID_PATTERN.sub(special_replacer, content)
        return content

    def _fix_remaining_integer_ids(self, content: str, modifications: List[str]) -> str:
        """
        Passe finale pour capturer toute colonne *_id restante avec Integer.
        """
        # Pattern général pour toute colonne *_id avec Integer
        general_pattern = re.compile(
            r'^(\s*)(\w+_id)\s*=\s*Column\s*\(\s*(Integer|BigInteger)\b([^)]*)\)',
            re.MULTILINE | re.IGNORECASE
        )

        def general_replacer(match):
            indent = match.group(1)
            col_name = match.group(2)
            old_type = match.group(3)
            rest = match.group(4) or ''

            # Ne pas corriger les colonnes autorisées en Integer
            if self._is_allowed_integer_column(col_name):
                return match.group(0)

            # Supprimer autoincrement et Sequence
            rest = self.AUTOINCREMENT_PATTERN.sub('', rest)
            rest = self.SEQUENCE_PATTERN.sub('', rest)
            rest = re.sub(r',\s*,', ',', rest)
            rest = rest.strip(', ')

            new_line = f"{indent}{col_name} = Column(UUID(as_uuid=True)"
            if rest:
                new_line += f", {rest}"
            new_line += ")"

            modifications.append(f"REMAINING: {col_name} : {old_type} → UUID")
            return new_line

        content = general_pattern.sub(general_replacer, content)
        return content

    def _fix_imports(self, content: str, modifications: List[str]) -> Tuple[str, List[str]]:
        """Ajoute les imports nécessaires et corrige l'import de Base."""
        imports_added = []
        lines = content.split('\n')
        new_lines = []
        import_section_end = 0
        has_uuid_import = bool(self.UUID_IMPORT_PATTERN.search(content))
        has_uuid_module = bool(self.UUID_MODULE_IMPORT_PATTERN.search(content))
        has_base_from_db = 'from app.db import Base' in content or 'from app.db.base import Base' in content

        # Trouver la fin de la section imports
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Gérer les docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        in_docstring = False
                else:
                    in_docstring = False
                continue

            if in_docstring:
                continue

            if stripped.startswith('import ') or stripped.startswith('from '):
                import_section_end = i + 1
            elif stripped and not stripped.startswith('#') and import_section_end > 0:
                break

        # Corriger l'import de Base
        processed_lines = []
        base_import_fixed = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Remplacer les anciens imports de Base
            if any(p.search(line) for p in self.BASE_IMPORT_PATTERNS):
                if not has_base_from_db and not base_import_fixed:
                    # Remplacer par le nouvel import
                    if 'from app.core.database import' in line:
                        # Garder les autres imports de ce module
                        other_imports = re.sub(r'\bBase\b,?\s*', '', line)
                        other_imports = re.sub(r',\s*$', '', other_imports)
                        if 'import' in other_imports and other_imports.split('import')[1].strip():
                            processed_lines.append(other_imports)
                    processed_lines.append('from app.db import Base')
                    imports_added.append('from app.db import Base')
                    modifications.append("BASE: Import Base depuis app.db")
                    base_import_fixed = True
                    self.report.base_imports_fixed += 1
                continue

            processed_lines.append(line)

        # Ajouter les imports UUID si nécessaire
        if not has_uuid_import:
            # Insérer après les imports existants
            insert_pos = import_section_end
            processed_lines.insert(insert_pos, 'from sqlalchemy.dialects.postgresql import UUID')
            imports_added.append('from sqlalchemy.dialects.postgresql import UUID')
            modifications.append("IMPORT: UUID depuis postgresql")
            self.report.imports_added += 1

        if not has_uuid_module:
            insert_pos = import_section_end
            processed_lines.insert(insert_pos, 'import uuid')
            imports_added.append('import uuid')
            modifications.append("IMPORT: module uuid")
            self.report.imports_added += 1

        return '\n'.join(processed_lines), imports_added

    def _is_model_file(self, content: str) -> bool:
        """Vérifie si le fichier contient des modèles SQLAlchemy."""
        indicators = [
            'class ',
            '__tablename__',
            'Column(',
            'relationship(',
            'Base)',
            'DeclarativeBase',
        ]
        return any(indicator in content for indicator in indicators)

    def _has_integer_issues(self, content: str) -> bool:
        """Vérifie si le fichier a des problèmes Integer à corriger."""
        # Vérifier les PK Integer
        if self.PK_INTEGER_PATTERN.search(content):
            return True
        if self.PK_INTEGER_PATTERN_ALT.search(content):
            return True

        # Vérifier les FK Integer
        if self.FK_INTEGER_PATTERN.search(content):
            return True

        # Vérifier les colonnes spéciales
        if self.SPECIAL_ID_PATTERN.search(content):
            return True

        # Vérifier l'import de Base
        for pattern in self.BASE_IMPORT_PATTERNS:
            if pattern.search(content):
                if 'from app.db import Base' not in content:
                    return True

        return False

    def fix_file(self, file_path: Path) -> Optional[FileModification]:
        """Corrige un fichier Python."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            self.report.errors.append(f"Erreur lecture {file_path}: {e}")
            return None

        # Vérifier si c'est un fichier modèle
        if not self._is_model_file(original_content):
            return None

        self.report.files_analyzed += 1

        # Vérifier s'il y a des problèmes à corriger
        if not self._has_integer_issues(original_content):
            return None

        modifications = []
        content = original_content

        # 1. Corriger les PK Integer
        content = self._fix_pk_column(content, modifications)

        # 2. Corriger les FK Integer
        content = self._fix_fk_columns(content, modifications)

        # 3. Corriger les colonnes spéciales *_id
        content = self._fix_special_id_columns(content, modifications)

        # 4. Passe finale pour les colonnes restantes
        content = self._fix_remaining_integer_ids(content, modifications)

        # 5. Corriger les imports
        content, imports_added = self._fix_imports(content, modifications)

        # Vérifier si des modifications ont été faites
        if content == original_content:
            return None

        # Créer l'objet modification
        mod = FileModification(
            file_path=str(file_path),
            original_content=original_content,
            new_content=content,
            changes=modifications,
            imports_added=imports_added
        )

        # Compter les modifications
        for change in modifications:
            if change.startswith("SUPPRIMÉ"):
                self.report.pk_columns_fixed += 1
            elif change.startswith("FK:"):
                self.report.fk_columns_fixed += 1
            elif change.startswith("ID_COL:") or change.startswith("REMAINING:"):
                self.report.id_columns_fixed += 1

        # Appliquer les modifications
        if not self.dry_run:
            if self.backup:
                self._backup_file(file_path)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        self.report.files_modified += 1
        self.report.modifications.append(mod)

        return mod

    def scan_and_fix(self, patterns: List[str] = None) -> None:
        """Scanne et corrige tous les fichiers."""
        if patterns is None:
            patterns = ['**/*.py']

        if self.backup:
            self._create_backup()

        files_to_process = set()

        for pattern in patterns:
            for file_path in self.base_path.rglob(pattern):
                if file_path.is_file():
                    # Exclure les fichiers de test et les backups
                    path_str = str(file_path)
                    if 'test' in path_str.lower() or 'backup' in path_str.lower():
                        continue
                    if '__pycache__' in path_str:
                        continue
                    files_to_process.add(file_path)

        print(f"[FIX] Analyse de {len(files_to_process)} fichiers Python...")

        for file_path in sorted(files_to_process):
            self.fix_file(file_path)

    def generate_report(self) -> str:
        """Génère le rapport de correction."""
        lines = []
        lines.append("=" * 80)
        lines.append("AZALS - FIX ALL MODELS TO UUID - RAPPORT INDUSTRIEL")
        lines.append("=" * 80)
        lines.append(f"Date: {self.report.timestamp}")
        lines.append(f"Mode: {'DRY-RUN (simulation)' if self.dry_run else 'PRODUCTION'}")
        if self.backup_dir:
            lines.append(f"Backup: {self.backup_dir}")
        lines.append("")

        # Statistiques
        lines.append("-" * 80)
        lines.append("STATISTIQUES")
        lines.append("-" * 80)
        lines.append(f"Fichiers analysés:       {self.report.files_analyzed}")
        lines.append(f"Fichiers modifiés:       {self.report.files_modified}")
        lines.append(f"PK Integer supprimées:   {self.report.pk_columns_fixed}")
        lines.append(f"FK Integer → UUID:       {self.report.fk_columns_fixed}")
        lines.append(f"*_id Integer → UUID:     {self.report.id_columns_fixed}")
        lines.append(f"Imports ajoutés:         {self.report.imports_added}")
        lines.append(f"Base imports corrigés:   {self.report.base_imports_fixed}")
        lines.append("")

        total_fixes = (
            self.report.pk_columns_fixed +
            self.report.fk_columns_fixed +
            self.report.id_columns_fixed
        )
        lines.append(f"TOTAL CORRECTIONS:       {total_fixes}")
        lines.append("")

        # Détails par fichier
        if self.report.modifications:
            lines.append("-" * 80)
            lines.append("DÉTAILS DES MODIFICATIONS")
            lines.append("-" * 80)

            for mod in self.report.modifications:
                rel_path = os.path.relpath(mod.file_path, self.base_path)
                lines.append(f"\n📁 {rel_path}")
                lines.append("-" * 60)

                for change in mod.changes:
                    lines.append(f"  ✓ {change}")

                if mod.imports_added:
                    lines.append("  Imports ajoutés:")
                    for imp in mod.imports_added:
                        lines.append(f"    + {imp}")

        # Erreurs
        if self.report.errors:
            lines.append("")
            lines.append("-" * 80)
            lines.append("ERREURS")
            lines.append("-" * 80)
            for error in self.report.errors:
                lines.append(f"  ⚠ {error}")

        # Statut final
        lines.append("")
        lines.append("=" * 80)
        if total_fixes == 0:
            lines.append("✅ AUCUNE CORRECTION NÉCESSAIRE")
            lines.append("   Tous les modèles sont déjà conformes UUID.")
        elif self.dry_run:
            lines.append(f"🔍 DRY-RUN: {total_fixes} correction(s) identifiée(s)")
            lines.append("   Relancer sans --dry-run pour appliquer.")
        else:
            lines.append(f"✅ {total_fixes} CORRECTION(S) APPLIQUÉE(S)")
            lines.append("   Exécuter uuid_schema_guard.py pour validation.")
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="AZALS - Fix All Models to UUID - Correction industrielle"
    )
    parser.add_argument(
        '--path', '-p',
        default='app',
        help='Chemin du répertoire à corriger (défaut: app)'
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
        '--output', '-o',
        help='Fichier de sortie pour le rapport'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Forcer sans confirmation'
    )

    args = parser.parse_args()

    # Déterminer le chemin
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    base_path = project_root / args.path

    if not base_path.exists():
        print(f"[ERREUR] Répertoire non trouvé: {base_path}")
        sys.exit(1)

    # Afficher le mode
    print("=" * 60)
    print("AZALS - FIX ALL MODELS TO UUID")
    print("=" * 60)

    if args.dry_run:
        print("[MODE] DRY-RUN - Simulation uniquement")
    else:
        print("[MODE] PRODUCTION - Les fichiers seront modifiés!")

    if not args.no_backup:
        print("[BACKUP] Les originaux seront sauvegardés")

    # Confirmation
    if not args.dry_run and not args.force:
        print("\n⚠️  ATTENTION: Cette opération va modifier TOUS les modèles ORM!")
        response = input("Continuer? [y/N] ")
        if response.lower() != 'y':
            print("[ANNULÉ]")
            sys.exit(0)

    # Exécuter
    fixer = UUIDModelFixer(
        base_path=base_path,
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    fixer.scan_and_fix()

    # Rapport
    report = fixer.generate_report()

    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n[RAPPORT] Sauvegardé: {output_path}")
    else:
        print(report)

    # Code de sortie
    if fixer.report.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
