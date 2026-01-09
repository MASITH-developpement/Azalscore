#!/usr/bin/env python3
"""
AZALSCORE - Module Validation Script
=====================================
Validates all modules for SaaS production readiness:
- Model imports (syntax check)
- UUID consistency (no BIGINT/UUID mixing)
- ForeignKey management (all FK in Alembic, not in models)
- Tenant isolation (tenant_id on all tables)
- Relationship integrity

Usage:
    python scripts/automation/validate_modules.py [--module MODULE] [--verbose]
"""

import argparse
import importlib
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ValidationResult:
    """Result of a validation check."""
    module: str
    check: str
    status: str  # PASS, FAIL, WARN, INFO
    message: str
    details: list = field(default_factory=list)


@dataclass
class ModuleReport:
    """Report for a single module."""
    name: str
    results: list = field(default_factory=list)
    errors: int = 0
    warnings: int = 0
    passed: int = 0
    infos: int = 0


class ModuleValidator:
    """Validates AZALSCORE modules for production readiness."""

    MODULES = [
        'iam',
        'commercial',
        'finance',
        'hr',
        'procurement',
        'inventory',
        'production',
        'maintenance',
        'quality',
        'qc',
        'projects',
        'bi',
        'ecommerce',
        'pos',
        'legal',
        'audit',
        'stripe_integration',
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.reports: list[ModuleReport] = []

    def validate_all(self, module_filter: str | None = None) -> bool:
        """Validate all modules or a specific one."""
        modules = [module_filter] if module_filter else self.MODULES
        all_passed = True

        for module_name in modules:
            if module_name not in self.MODULES and module_filter:
                print(f"Module '{module_name}' not found in registered modules")
                continue

            report = self._validate_module(module_name)
            self.reports.append(report)

            if report.errors > 0:
                all_passed = False

        return all_passed

    def _validate_module(self, module_name: str) -> ModuleReport:
        """Validate a single module."""
        report = ModuleReport(name=module_name)

        # Check 1: Model imports
        result = self._check_model_imports(module_name)
        report.results.append(result)
        self._update_counts(report, result)

        if result.status == 'FAIL':
            # Cannot continue if models don't import
            return report

        # Check 2: UUID consistency
        result = self._check_uuid_consistency(module_name)
        report.results.append(result)
        self._update_counts(report, result)

        # Check 3: ForeignKey in models (should be none)
        result = self._check_foreignkey_in_models(module_name)
        report.results.append(result)
        self._update_counts(report, result)

        # Check 4: Tenant isolation
        result = self._check_tenant_isolation(module_name)
        report.results.append(result)
        self._update_counts(report, result)

        # Check 5: Relationships defined
        result = self._check_relationships(module_name)
        report.results.append(result)
        self._update_counts(report, result)

        return report

    def _check_model_imports(self, module_name: str) -> ValidationResult:
        """Check if module models can be imported."""
        try:
            # Set minimal env vars for import
            os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
            if 'SECRET_KEY' not in os.environ:
                import secrets
                os.environ['SECRET_KEY'] = secrets.token_urlsafe(64)

            module = importlib.import_module(f'app.modules.{module_name}.models')
            return ValidationResult(
                module=module_name,
                check='model_imports',
                status='PASS',
                message=f'Models imported successfully'
            )
        except Exception as e:
            return ValidationResult(
                module=module_name,
                check='model_imports',
                status='FAIL',
                message=f'Import failed: {str(e)[:100]}'
            )

    def _check_uuid_consistency(self, module_name: str) -> ValidationResult:
        """Check for BIGINT/Integer usage (should be UUID only)."""
        models_path = PROJECT_ROOT / 'app' / 'modules' / module_name / 'models.py'

        if not models_path.exists():
            return ValidationResult(
                module=module_name,
                check='uuid_consistency',
                status='INFO',
                message='No models.py file found'
            )

        content = models_path.read_text()

        # Patterns that indicate non-UUID primary keys
        bad_patterns = [
            (r'Column\s*\(\s*Integer\s*,\s*primary_key\s*=\s*True', 'Integer primary key'),
            (r'Column\s*\(\s*BigInteger\s*,\s*primary_key\s*=\s*True', 'BigInteger primary key'),
            (r'id\s*=\s*Column\s*\(\s*Integer\b', 'Integer id column'),
            (r'id\s*=\s*Column\s*\(\s*BigInteger\b', 'BigInteger id column'),
        ]

        issues = []
        for pattern, desc in bad_patterns:
            matches = re.findall(pattern, content)
            if matches:
                issues.append(f'{desc}: {len(matches)} occurrence(s)')

        if issues:
            return ValidationResult(
                module=module_name,
                check='uuid_consistency',
                status='FAIL',
                message='Non-UUID columns detected',
                details=issues
            )

        return ValidationResult(
            module=module_name,
            check='uuid_consistency',
            status='PASS',
            message='All primary keys use UUID'
        )

    def _check_foreignkey_in_models(self, module_name: str) -> ValidationResult:
        """Check that ForeignKey is not used in model definitions."""
        models_path = PROJECT_ROOT / 'app' / 'modules' / module_name / 'models.py'

        if not models_path.exists():
            return ValidationResult(
                module=module_name,
                check='foreignkey_in_models',
                status='INFO',
                message='No models.py file found'
            )

        content = models_path.read_text()

        # Pattern for ForeignKey usage (excluding comments and imports)
        fk_pattern = r'ForeignKey\s*\(["\'][\w_]+\.[\w_]+["\']\)'
        matches = re.findall(fk_pattern, content)

        if matches:
            return ValidationResult(
                module=module_name,
                check='foreignkey_in_models',
                status='WARN',
                message=f'{len(matches)} ForeignKey(s) in models (should be in Alembic)',
                details=matches[:5]  # Show first 5
            )

        return ValidationResult(
            module=module_name,
            check='foreignkey_in_models',
            status='PASS',
            message='No ForeignKey in models (managed via Alembic)'
        )

    def _check_tenant_isolation(self, module_name: str) -> ValidationResult:
        """Check that all tables have tenant_id column."""
        models_path = PROJECT_ROOT / 'app' / 'modules' / module_name / 'models.py'

        if not models_path.exists():
            return ValidationResult(
                module=module_name,
                check='tenant_isolation',
                status='INFO',
                message='No models.py file found'
            )

        content = models_path.read_text()

        # Find all table definitions
        table_pattern = r'__tablename__\s*=\s*["\'](\w+)["\']'
        tables = re.findall(table_pattern, content)

        # Check each class for tenant_id
        class_pattern = r'class\s+(\w+)\s*\([^)]*Base[^)]*\):'
        classes = re.findall(class_pattern, content)

        missing_tenant = []
        for cls in classes:
            # Find the class definition and check for tenant_id
            class_match = re.search(
                rf'class\s+{cls}\s*\([^)]*Base[^)]*\):.*?(?=class\s+\w+|$)',
                content,
                re.DOTALL
            )
            if class_match:
                class_content = class_match.group()
                if 'tenant_id' not in class_content:
                    missing_tenant.append(cls)

        if missing_tenant:
            return ValidationResult(
                module=module_name,
                check='tenant_isolation',
                status='FAIL',
                message=f'{len(missing_tenant)} model(s) missing tenant_id',
                details=missing_tenant
            )

        return ValidationResult(
            module=module_name,
            check='tenant_isolation',
            status='PASS',
            message=f'All {len(classes)} models have tenant_id'
        )

    def _check_relationships(self, module_name: str) -> ValidationResult:
        """Check that ORM relationships are properly defined."""
        models_path = PROJECT_ROOT / 'app' / 'modules' / module_name / 'models.py'

        if not models_path.exists():
            return ValidationResult(
                module=module_name,
                check='relationships',
                status='INFO',
                message='No models.py file found'
            )

        content = models_path.read_text()

        # Count relationships
        rel_pattern = r'relationship\s*\('
        relationships = len(re.findall(rel_pattern, content))

        # Check for foreign_keys parameter (best practice when FK not in model)
        fk_param_pattern = r'foreign_keys\s*='
        fk_params = len(re.findall(fk_param_pattern, content))

        if relationships > 0 and fk_params == 0:
            return ValidationResult(
                module=module_name,
                check='relationships',
                status='WARN',
                message=f'{relationships} relationships without explicit foreign_keys parameter'
            )

        return ValidationResult(
            module=module_name,
            check='relationships',
            status='PASS',
            message=f'{relationships} relationships defined ({fk_params} with explicit foreign_keys)'
        )

    def _update_counts(self, report: ModuleReport, result: ValidationResult):
        """Update report counts based on result status."""
        if result.status == 'FAIL':
            report.errors += 1
        elif result.status == 'WARN':
            report.warnings += 1
        elif result.status == 'PASS':
            report.passed += 1
        else:
            report.infos += 1

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("AZALSCORE MODULE VALIDATION REPORT")
        print("=" * 70)

        total_errors = 0
        total_warnings = 0
        total_passed = 0

        for report in self.reports:
            status_icon = "PASS" if report.errors == 0 else "FAIL"
            print(f"\n[{status_icon}] Module: {report.name}")
            print("-" * 50)

            for result in report.results:
                icon = {
                    'PASS': '[OK]',
                    'FAIL': '[!!]',
                    'WARN': '[??]',
                    'INFO': '[--]'
                }.get(result.status, '[--]')

                print(f"  {icon} {result.check}: {result.message}")
                if self.verbose and result.details:
                    for detail in result.details:
                        print(f"      - {detail}")

            total_errors += report.errors
            total_warnings += report.warnings
            total_passed += report.passed

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"  Modules validated: {len(self.reports)}")
        print(f"  Checks passed:     {total_passed}")
        print(f"  Warnings:          {total_warnings}")
        print(f"  Errors:            {total_errors}")
        print("=" * 70)

        if total_errors > 0:
            print("\nVERDICT: VALIDATION FAILED")
            return False
        elif total_warnings > 0:
            print("\nVERDICT: PASSED WITH WARNINGS")
            return True
        else:
            print("\nVERDICT: ALL CHECKS PASSED")
            return True


def main():
    parser = argparse.ArgumentParser(description='Validate AZALSCORE modules')
    parser.add_argument('--module', '-m', help='Validate specific module only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    validator = ModuleValidator(verbose=args.verbose)
    success = validator.validate_all(module_filter=args.module)
    validator.print_report()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
