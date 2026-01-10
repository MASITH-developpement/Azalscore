#!/usr/bin/env python3
"""
AZALS - SQLAlchemy 2.x Migration Script
========================================
Migration AUTOMATIQUE vers la syntaxe SQLAlchemy 2.x stricte.

TRANSFORMATIONS:
1. Column(...) → mapped_column(...)
2. Ajout de type annotations Mapped[T]
3. Mise à jour des imports

AVANT:
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

APRÈS:
    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Usage:
    python scripts/fix_sqlalchemy2_annotations.py
    python scripts/fix_sqlalchemy2_annotations.py --dry-run
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime as dt
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional


@dataclass
class ColumnTransform:
    """Représente une transformation de colonne."""
    line_number: int
    original: str
    transformed: str
    column_name: str
    mapped_type: str


@dataclass
class FileTransform:
    """Transformations d'un fichier."""
    file_path: str
    columns_transformed: List[ColumnTransform] = field(default_factory=list)
    imports_added: List[str] = field(default_factory=list)
    imports_removed: List[str] = field(default_factory=list)


@dataclass
class MigrationReport:
    """Rapport de migration."""
    timestamp: str = ""
    files_analyzed: int = 0
    files_modified: int = 0
    columns_transformed: int = 0
    imports_updated: int = 0
    transforms: List[FileTransform] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SQLAlchemy2Migrator:
    """
    Migrateur SQLAlchemy 1.x → 2.x
    Transforme Column() en mapped_column() avec annotations Mapped[T].
    """

    # Mapping des types SQLAlchemy vers types Python pour Mapped[]
    TYPE_MAPPING = {
        # Types String
        'String': 'str',
        'Text': 'str',
        'VARCHAR': 'str',
        'CHAR': 'str',

        # Types Numériques
        'Integer': 'int',
        'BigInteger': 'int',
        'SmallInteger': 'int',
        'Numeric': 'Decimal',
        'Float': 'float',
        'DECIMAL': 'Decimal',

        # Types Date/Time
        'DateTime': 'datetime',
        'Date': 'date',
        'Time': 'time',
        'TIMESTAMP': 'datetime',

        # Types Boolean
        'Boolean': 'bool',

        # Types UUID
        'UUID': 'uuid.UUID',
        'UniversalUUID': 'uuid.UUID',
        'GUID': 'uuid.UUID',

        # Types JSON
        'JSON': 'dict',
        'JSONB': 'dict',

        # Types Enum (special handling)
        'Enum': 'ENUM_TYPE',
    }

    # Pattern pour détecter les colonnes Column(...)
    COLUMN_PATTERN = re.compile(
        r'^(\s*)(\w+)\s*=\s*Column\s*\(([^)]+(?:\([^)]*\)[^)]*)*)\)',
        re.MULTILINE
    )

    # Pattern pour les colonnes avec annotation existante
    ANNOTATED_COLUMN_PATTERN = re.compile(
        r'^(\s*)(\w+)\s*:\s*([^\s=]+)\s*=\s*Column\s*\(([^)]+(?:\([^)]*\)[^)]*)*)\)',
        re.MULTILINE
    )

    # Pattern pour détecter le type dans Column(Type(...), ...)
    TYPE_EXTRACT_PATTERN = re.compile(r'^(\w+)(?:\([^)]*\))?')

    # Pattern pour Enum
    ENUM_PATTERN = re.compile(r'Enum\s*\(\s*(\w+)\s*[,)]')

    # Imports à ajouter
    REQUIRED_IMPORTS = [
        'from sqlalchemy.orm import Mapped, mapped_column',
    ]

    # Imports à supprimer/modifier
    OLD_IMPORTS = [
        re.compile(r'from sqlalchemy import.*\bColumn\b'),
    ]

    def __init__(self, base_path: str, dry_run: bool = False, backup: bool = True):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.backup = backup
        self.report = MigrationReport(timestamp=dt.now().isoformat())
        self.backup_dir: Optional[Path] = None

    def _create_backup(self) -> Path:
        """Crée le répertoire de backup."""
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.base_path.parent / 'backups' / f'sqlalchemy2_migration_{timestamp}'
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

    def _extract_sqlalchemy_type(self, column_args: str) -> Tuple[str, str]:
        """
        Extrait le type SQLAlchemy et retourne le type Mapped correspondant.

        Returns:
            Tuple[str, str]: (type_sqlalchemy, type_python_pour_mapped)
        """
        column_args = column_args.strip()

        # Chercher le premier argument (le type)
        match = self.TYPE_EXTRACT_PATTERN.match(column_args)
        if not match:
            return ('Unknown', 'Any')

        sql_type = match.group(1)

        # Cas spécial: Enum
        if sql_type == 'Enum':
            enum_match = self.ENUM_PATTERN.search(column_args)
            if enum_match:
                return ('Enum', enum_match.group(1))
            return ('Enum', 'str')

        # Lookup dans le mapping
        python_type = self.TYPE_MAPPING.get(sql_type, 'Any')

        return (sql_type, python_type)

    def _is_nullable(self, column_args: str) -> bool:
        """Vérifie si la colonne est nullable."""
        # Par défaut nullable=True en SQLAlchemy
        if 'nullable=False' in column_args:
            return False
        if 'nullable=True' in column_args:
            return True
        if 'primary_key=True' in column_args:
            return False
        return True

    def _transform_column(self, match: re.Match, file_transforms: FileTransform) -> str:
        """Transforme une définition Column() en mapped_column()."""
        indent = match.group(1)
        col_name = match.group(2)
        col_args = match.group(3)

        # Extraire le type
        sql_type, python_type = self._extract_sqlalchemy_type(col_args)

        # Déterminer si nullable
        is_nullable = self._is_nullable(col_args)

        # Construire le type Mapped
        if is_nullable and python_type not in ('uuid.UUID',) and 'primary_key' not in col_args:
            mapped_type = f'Optional[{python_type}]'
        else:
            mapped_type = python_type

        # Nettoyer les arguments (supprimer nullable=False pour les non-nullable)
        clean_args = col_args
        if not is_nullable:
            clean_args = re.sub(r',?\s*nullable\s*=\s*False\s*,?', '', clean_args)
            clean_args = re.sub(r',\s*,', ',', clean_args)
            clean_args = clean_args.strip(', ')

        # Construire la nouvelle ligne
        new_line = f'{indent}{col_name}: Mapped[{mapped_type}] = mapped_column({clean_args})'

        # Enregistrer la transformation
        transform = ColumnTransform(
            line_number=0,  # Sera calculé plus tard
            original=match.group(0),
            transformed=new_line,
            column_name=col_name,
            mapped_type=mapped_type
        )
        file_transforms.columns_transformed.append(transform)

        return new_line

    def _transform_annotated_column(self, match: re.Match, file_transforms: FileTransform) -> str:
        """Transforme une colonne avec annotation existante."""
        indent = match.group(1)
        col_name = match.group(2)
        existing_type = match.group(3)
        col_args = match.group(4)

        # Si déjà Mapped[], ne pas transformer
        if 'Mapped[' in existing_type:
            return match.group(0)

        # Extraire le type SQLAlchemy pour validation
        sql_type, python_type = self._extract_sqlalchemy_type(col_args)

        # Utiliser le type existant s'il est valide, sinon le type détecté
        if existing_type in ('str', 'int', 'float', 'bool', 'datetime', 'date', 'UUID'):
            mapped_type = existing_type
        else:
            mapped_type = python_type

        # Déterminer si nullable
        is_nullable = self._is_nullable(col_args)
        if is_nullable and 'Optional' not in existing_type:
            mapped_type = f'Optional[{mapped_type}]'

        # Nettoyer les arguments
        clean_args = col_args
        if not is_nullable:
            clean_args = re.sub(r',?\s*nullable\s*=\s*False\s*,?', '', clean_args)
            clean_args = re.sub(r',\s*,', ',', clean_args)
            clean_args = clean_args.strip(', ')

        new_line = f'{indent}{col_name}: Mapped[{mapped_type}] = mapped_column({clean_args})'

        transform = ColumnTransform(
            line_number=0,
            original=match.group(0),
            transformed=new_line,
            column_name=col_name,
            mapped_type=mapped_type
        )
        file_transforms.columns_transformed.append(transform)

        return new_line

    def _update_imports(self, content: str, file_transforms: FileTransform) -> str:
        """Met à jour les imports pour SQLAlchemy 2.x."""
        lines = content.split('\n')
        new_lines = []

        # Tracking
        has_mapped_import = 'from sqlalchemy.orm import Mapped' in content or 'Mapped,' in content
        has_mapped_column_import = 'mapped_column' in content
        has_optional_import = 'from typing import' in content and 'Optional' in content
        column_import_line_idx = -1
        orm_import_line_idx = -1
        typing_import_line_idx = -1

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Trouver l'import de Column
            if 'from sqlalchemy import' in line and 'Column' in line:
                column_import_line_idx = i
                # Retirer Column de l'import
                new_line = re.sub(r',?\s*\bColumn\b\s*,?', '', line)
                new_line = re.sub(r'import\s*,', 'import ', new_line)
                new_line = re.sub(r',\s*$', '', new_line)
                new_line = re.sub(r',\s*,', ',', new_line)

                # Vérifier s'il reste quelque chose à importer
                if 'import' in new_line:
                    remaining = new_line.split('import')[1].strip()
                    if remaining and remaining != '(':
                        new_lines.append(new_line)
                        file_transforms.imports_removed.append('Column removed from sqlalchemy import')
                    else:
                        file_transforms.imports_removed.append('Removed empty sqlalchemy import')
                continue

            # Trouver l'import sqlalchemy.orm
            if 'from sqlalchemy.orm import' in line:
                orm_import_line_idx = i
                # Ajouter Mapped et mapped_column si absents
                if 'Mapped' not in line:
                    if line.rstrip().endswith(')'):
                        # Import multiligne
                        line = line.rstrip().rstrip(')')
                        line += ', Mapped, mapped_column)'
                    else:
                        line = line.rstrip() + ', Mapped, mapped_column'
                    file_transforms.imports_added.append('Mapped, mapped_column added to sqlalchemy.orm import')
                elif 'mapped_column' not in line:
                    if line.rstrip().endswith(')'):
                        line = line.rstrip().rstrip(')')
                        line += ', mapped_column)'
                    else:
                        line = line.rstrip() + ', mapped_column'
                    file_transforms.imports_added.append('mapped_column added to sqlalchemy.orm import')

            # Trouver l'import typing
            if 'from typing import' in line:
                typing_import_line_idx = i
                if 'Optional' not in line:
                    if line.rstrip().endswith(')'):
                        line = line.rstrip().rstrip(')')
                        line += ', Optional)'
                    else:
                        line = line.rstrip() + ', Optional'
                    file_transforms.imports_added.append('Optional added to typing import')

            new_lines.append(line)

        # Si pas d'import sqlalchemy.orm, l'ajouter
        if orm_import_line_idx == -1 and not has_mapped_import:
            # Trouver où insérer (après les imports existants)
            insert_idx = 0
            for i, line in enumerate(new_lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_idx = i + 1

            new_lines.insert(insert_idx, 'from sqlalchemy.orm import Mapped, mapped_column')
            file_transforms.imports_added.append('from sqlalchemy.orm import Mapped, mapped_column')

        # Si pas d'import typing Optional, l'ajouter
        if typing_import_line_idx == -1 and not has_optional_import:
            insert_idx = 0
            for i, line in enumerate(new_lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_idx = i + 1

            # Chercher si typing est déjà importé
            typing_exists = any('from typing import' in l for l in new_lines)
            if not typing_exists:
                new_lines.insert(insert_idx, 'from typing import Optional')
                file_transforms.imports_added.append('from typing import Optional')

        return '\n'.join(new_lines)

    def _is_model_file(self, content: str) -> bool:
        """Vérifie si le fichier contient des modèles SQLAlchemy."""
        return 'Column(' in content and ('Base)' in content or '__tablename__' in content)

    def transform_file(self, file_path: Path) -> Optional[FileTransform]:
        """Transforme un fichier Python."""
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

        file_transforms = FileTransform(file_path=str(file_path))
        content = original_content

        # 1. Transformer les colonnes avec annotation existante
        content = self.ANNOTATED_COLUMN_PATTERN.sub(
            lambda m: self._transform_annotated_column(m, file_transforms),
            content
        )

        # 2. Transformer les colonnes sans annotation
        content = self.COLUMN_PATTERN.sub(
            lambda m: self._transform_column(m, file_transforms),
            content
        )

        # 3. Mettre à jour les imports
        content = self._update_imports(content, file_transforms)

        # Vérifier si des modifications ont été faites
        if content == original_content:
            return None

        # Sauvegarder
        if not self.dry_run:
            if self.backup:
                self._backup_file(file_path)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        self.report.files_modified += 1
        self.report.columns_transformed += len(file_transforms.columns_transformed)
        self.report.imports_updated += len(file_transforms.imports_added)
        self.report.transforms.append(file_transforms)

        return file_transforms

    def migrate(self) -> None:
        """Exécute la migration complète."""
        if self.backup:
            self._create_backup()

        print(f"[MIGRATE] Analyse de {self.base_path}...")

        for file_path in self.base_path.rglob('*.py'):
            if '__pycache__' in str(file_path):
                continue
            if 'test' in str(file_path).lower():
                continue
            if 'backup' in str(file_path).lower():
                continue
            if 'migration' in str(file_path).lower():
                continue

            self.transform_file(file_path)

    def generate_report(self) -> str:
        """Génère le rapport de migration."""
        lines = []
        lines.append("=" * 80)
        lines.append("AZALS - SQLALCHEMY 2.x MIGRATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Date: {self.report.timestamp}")
        lines.append(f"Mode: {'DRY-RUN' if self.dry_run else 'PRODUCTION'}")
        if self.backup_dir:
            lines.append(f"Backup: {self.backup_dir}")
        lines.append("")

        # Statistiques
        lines.append("-" * 80)
        lines.append("STATISTICS")
        lines.append("-" * 80)
        lines.append(f"Files analyzed:          {self.report.files_analyzed}")
        lines.append(f"Files modified:          {self.report.files_modified}")
        lines.append(f"Columns transformed:     {self.report.columns_transformed}")
        lines.append(f"Imports updated:         {self.report.imports_updated}")
        lines.append("")

        # Détails par fichier
        if self.report.transforms:
            lines.append("-" * 80)
            lines.append("TRANSFORMATIONS")
            lines.append("-" * 80)

            for ft in self.report.transforms:
                rel_path = os.path.relpath(ft.file_path, self.base_path)
                lines.append(f"\n📁 {rel_path}")
                lines.append("-" * 60)

                if ft.imports_added:
                    lines.append("  Imports added:")
                    for imp in ft.imports_added:
                        lines.append(f"    + {imp}")

                if ft.imports_removed:
                    lines.append("  Imports removed:")
                    for imp in ft.imports_removed:
                        lines.append(f"    - {imp}")

                if ft.columns_transformed:
                    lines.append(f"  Columns ({len(ft.columns_transformed)}):")
                    for col in ft.columns_transformed[:10]:  # Limiter l'affichage
                        lines.append(f"    ✓ {col.column_name}: Mapped[{col.mapped_type}]")
                    if len(ft.columns_transformed) > 10:
                        lines.append(f"    ... and {len(ft.columns_transformed) - 10} more")

        # Erreurs
        if self.report.errors:
            lines.append("")
            lines.append("-" * 80)
            lines.append("ERRORS")
            lines.append("-" * 80)
            for error in self.report.errors:
                lines.append(f"  ⚠ {error}")

        # Statut final
        lines.append("")
        lines.append("=" * 80)
        if self.report.columns_transformed == 0:
            lines.append("✅ No transformations needed - already SQLAlchemy 2.x compliant")
        elif self.dry_run:
            lines.append(f"🔍 DRY-RUN: {self.report.columns_transformed} transformation(s) identified")
            lines.append("   Run without --dry-run to apply changes")
        else:
            lines.append(f"✅ {self.report.columns_transformed} column(s) migrated to SQLAlchemy 2.x")
            lines.append("   Test with: python -c \"from app.core.models import *\"")
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="AZALS - SQLAlchemy 2.x Migration Script"
    )
    parser.add_argument(
        '--path', '-p',
        default='app',
        help='Directory to migrate (default: app)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Simulation mode (no changes)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable backups'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file for report'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force without confirmation'
    )

    args = parser.parse_args()

    # Determine path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    base_path = project_root / args.path

    if not base_path.exists():
        print(f"[ERROR] Directory not found: {base_path}")
        sys.exit(1)

    print("=" * 60)
    print("AZALS - SQLAlchemy 2.x Migration")
    print("=" * 60)

    if args.dry_run:
        print("[MODE] DRY-RUN - Simulation only")
    else:
        print("[MODE] PRODUCTION - Files will be modified!")

    if not args.no_backup:
        print("[BACKUP] Original files will be saved")

    # Confirmation
    if not args.dry_run and not args.force:
        print("\n⚠️  This will transform ALL ORM models to SQLAlchemy 2.x syntax!")
        response = input("Continue? [y/N] ")
        if response.lower() != 'y':
            print("[CANCELLED]")
            sys.exit(0)

    # Execute
    migrator = SQLAlchemy2Migrator(
        base_path=base_path,
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    migrator.migrate()

    # Report
    report = migrator.generate_report()

    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n[REPORT] Saved: {output_path}")
    else:
        print(report)

    # Exit code
    if migrator.report.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
