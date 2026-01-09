#!/usr/bin/env python3
"""
AZALSCORE - Alembic Migration Automation
=========================================
Automates database migrations with safety checks:
- Pre-migration validation
- Migration execution with rollback support
- Post-migration verification
- Two-phase migration support (bootstrap + constraints)

Usage:
    python scripts/automation/run_alembic.py upgrade head
    python scripts/automation/run_alembic.py downgrade -1
    python scripts/automation/run_alembic.py status
    python scripts/automation/run_alembic.py validate
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class AlembicAutomation:
    """Automates Alembic migrations with safety checks."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.project_root = PROJECT_ROOT
        self.alembic_dir = PROJECT_ROOT / 'alembic'
        self.versions_dir = self.alembic_dir / 'versions'

    def run_command(self, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        if self.verbose:
            print(f"  > {' '.join(cmd)}")

        if self.dry_run and cmd[0] == 'alembic' and cmd[1] in ('upgrade', 'downgrade'):
            print(f"  [DRY RUN] Would execute: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, '', '')

        result = subprocess.run(
            cmd,
            cwd=str(self.project_root),
            capture_output=True,
            text=True
        )

        if check and result.returncode != 0:
            print(f"  Error: {result.stderr}")
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")

        return result

    def get_current_revision(self) -> str | None:
        """Get current database revision."""
        try:
            result = self.run_command(['alembic', 'current'], check=False)
            if result.returncode == 0:
                # Parse output to get revision
                for line in result.stdout.split('\n'):
                    if '(head)' in line or 'Rev:' in line:
                        parts = line.split()
                        if parts:
                            return parts[0]
            return None
        except Exception:
            return None

    def get_pending_migrations(self) -> list[str]:
        """Get list of pending migrations."""
        result = self.run_command(['alembic', 'history', '--indicate-current'], check=False)
        pending = []

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            current_found = False
            for line in lines:
                if '(current)' in line:
                    current_found = True
                    continue
                if not current_found and '->' in line:
                    # Extract revision ID
                    parts = line.split('->')
                    if len(parts) >= 2:
                        rev = parts[1].strip().split()[0]
                        pending.append(rev)

        return pending

    def validate_migrations(self) -> tuple[bool, list[str]]:
        """Validate migration files for common issues."""
        issues = []

        if not self.versions_dir.exists():
            issues.append("Versions directory does not exist")
            return False, issues

        migration_files = list(self.versions_dir.glob('*.py'))

        for mig_file in migration_files:
            if mig_file.name == '__pycache__':
                continue

            content = mig_file.read_text()

            # Check for required functions
            if 'def upgrade()' not in content and 'def upgrade(' not in content:
                issues.append(f"{mig_file.name}: Missing upgrade() function")

            if 'def downgrade()' not in content and 'def downgrade(' not in content:
                issues.append(f"{mig_file.name}: Missing downgrade() function")

            # Check for revision identifiers
            if 'revision =' not in content:
                issues.append(f"{mig_file.name}: Missing revision identifier")

            # Check for dangerous operations
            if 'op.drop_table' in content:
                issues.append(f"{mig_file.name}: Contains DROP TABLE (dangerous)")

            if 'op.execute' in content and 'TRUNCATE' in content.upper():
                issues.append(f"{mig_file.name}: Contains TRUNCATE (dangerous)")

        return len(issues) == 0, issues

    def status(self):
        """Show migration status."""
        print("\n" + "=" * 60)
        print("ALEMBIC MIGRATION STATUS")
        print("=" * 60)

        # Current revision
        current = self.get_current_revision()
        print(f"\nCurrent revision: {current or 'None (empty database)'}")

        # Migration files
        if self.versions_dir.exists():
            migrations = sorted(self.versions_dir.glob('*.py'))
            migrations = [m for m in migrations if m.name != '__pycache__']
            print(f"Migration files:  {len(migrations)}")

            if self.verbose:
                print("\nMigration files:")
                for m in migrations[-10:]:  # Show last 10
                    print(f"  - {m.name}")
        else:
            print("Migration files:  0 (versions directory not found)")

        # Pending migrations
        result = self.run_command(['alembic', 'history', '-v'], check=False)
        if result.returncode == 0:
            print("\nMigration history:")
            for line in result.stdout.strip().split('\n')[-10:]:
                print(f"  {line}")

        print("=" * 60)

    def upgrade(self, revision: str = 'head'):
        """Run upgrade migration."""
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}UPGRADING TO: {revision}")
        print("-" * 40)

        # Validate first
        is_valid, issues = self.validate_migrations()
        if not is_valid:
            print("Migration validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            if not self.dry_run:
                raise RuntimeError("Migration validation failed")

        # Run upgrade
        timestamp = datetime.now().isoformat()
        print(f"Starting upgrade at {timestamp}")

        self.run_command(['alembic', 'upgrade', revision])

        print(f"Upgrade completed successfully")

        # Show new current revision
        new_rev = self.get_current_revision()
        print(f"Current revision: {new_rev}")

    def downgrade(self, revision: str = '-1'):
        """Run downgrade migration."""
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}DOWNGRADING TO: {revision}")
        print("-" * 40)

        current = self.get_current_revision()
        print(f"Current revision: {current}")

        if not self.dry_run:
            confirm = input("Are you sure you want to downgrade? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Downgrade cancelled")
                return

        self.run_command(['alembic', 'downgrade', revision])

        print("Downgrade completed successfully")

        new_rev = self.get_current_revision()
        print(f"New revision: {new_rev}")

    def validate(self):
        """Run migration validation only."""
        print("\n" + "=" * 60)
        print("MIGRATION VALIDATION")
        print("=" * 60)

        is_valid, issues = self.validate_migrations()

        if is_valid:
            print("\nAll migrations are valid")
        else:
            print("\nValidation issues found:")
            for issue in issues:
                print(f"  - {issue}")

        # Also validate Alembic can parse them
        result = self.run_command(['alembic', 'check'], check=False)
        if result.returncode != 0:
            print("\nAlembic check failed:")
            print(result.stderr)
        else:
            print("\nAlembic check: OK")

        print("=" * 60)
        return is_valid

    def generate(self, message: str):
        """Generate a new migration."""
        print(f"\nGenerating migration: {message}")

        # Sanitize message for filename
        safe_message = message.lower().replace(' ', '_')[:40]

        self.run_command([
            'alembic', 'revision',
            '--autogenerate',
            '-m', message
        ])

        print("Migration generated successfully")
        print(f"Check {self.versions_dir} for the new file")


def main():
    parser = argparse.ArgumentParser(description='Alembic migration automation')
    parser.add_argument('command', choices=['upgrade', 'downgrade', 'status', 'validate', 'generate'],
                        help='Command to run')
    parser.add_argument('revision', nargs='?', default='head',
                        help='Revision to upgrade/downgrade to (default: head)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be done without executing')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output')
    parser.add_argument('--message', '-m', help='Message for new migration (with generate)')

    args = parser.parse_args()

    # Check environment
    if 'DATABASE_URL' not in os.environ:
        print("Warning: DATABASE_URL not set")
        print("Set it with: export DATABASE_URL='postgresql://user:pass@host/db'")
        if args.command in ('upgrade', 'downgrade'):
            sys.exit(1)

    automation = AlembicAutomation(dry_run=args.dry_run, verbose=args.verbose)

    try:
        if args.command == 'status':
            automation.status()
        elif args.command == 'upgrade':
            automation.upgrade(args.revision)
        elif args.command == 'downgrade':
            automation.downgrade(args.revision)
        elif args.command == 'validate':
            success = automation.validate()
            sys.exit(0 if success else 1)
        elif args.command == 'generate':
            if not args.message:
                print("Error: --message required for generate command")
                sys.exit(1)
            automation.generate(args.message)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
