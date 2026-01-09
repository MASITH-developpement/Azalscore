#!/usr/bin/env python3
"""
AZALS ERP - UUID Schema Validation Script
==========================================

This script validates that all SQLAlchemy models use UUID for primary keys
and foreign keys, ensuring PostgreSQL compatibility.

Usage:
    python scripts/migrations/003_validate_uuid_schema.py

Exit codes:
    0: All validations passed
    1: Validation errors found
"""

import sys
import importlib
import inspect
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_column_type_name(column: Any) -> str:
    """Extract the type name from a SQLAlchemy column."""
    try:
        col_type = column.type
        type_name = type(col_type).__name__
        # Handle wrapper types
        if hasattr(col_type, 'impl'):
            type_name = type(col_type.impl).__name__
        return type_name
    except Exception:
        return "Unknown"


def validate_model(model_class: Any) -> list[dict]:
    """Validate a single SQLAlchemy model for UUID compliance."""
    errors = []
    table_name = getattr(model_class, '__tablename__', 'unknown')

    # Get all columns
    mapper = getattr(model_class, '__mapper__', None)
    if mapper is None:
        return errors

    for column in mapper.columns:
        col_name = column.name
        col_type = get_column_type_name(column)
        is_pk = column.primary_key
        is_fk = len(column.foreign_keys) > 0

        # Check primary keys
        if is_pk and col_name == 'id':
            if col_type not in ('UUID', 'UniversalUUID', 'GUID'):
                errors.append({
                    'table': table_name,
                    'column': col_name,
                    'issue': f'Primary key should be UUID, found: {col_type}',
                    'severity': 'ERROR'
                })

        # Check foreign keys
        if is_fk:
            for fk in column.foreign_keys:
                target_col = str(fk.column)
                if '.id' in target_col:
                    if col_type not in ('UUID', 'UniversalUUID', 'GUID', 'String'):
                        errors.append({
                            'table': table_name,
                            'column': col_name,
                            'issue': f'FK to {target_col} should be UUID, found: {col_type}',
                            'severity': 'ERROR'
                        })

        # Check reference columns (user_id, employee_id, etc. without explicit FK)
        ref_columns = [
            'user_id', 'employee_id', 'customer_id', 'vendor_id', 'product_id',
            'created_by', 'updated_by', 'approved_by', 'validated_by', 'assigned_to',
            'manager_id', 'requested_by', 'rejected_by', 'revoked_by', 'triggered_by',
            'detected_by', 'generated_by', 'processed_by', 'managed_by', 'uploaded_by',
            'evaluator_id', 'replacement_id', 'closed_by', 'data_subject_id',
            'transfer_to_user_id', 'last_review_by'
        ]

        if col_name in ref_columns and not is_fk:
            if col_type not in ('UUID', 'UniversalUUID', 'GUID', 'String', 'NullType'):
                errors.append({
                    'table': table_name,
                    'column': col_name,
                    'issue': f'Reference column should be UUID, found: {col_type}',
                    'severity': 'WARNING'
                })

    return errors


def import_all_models():
    """Import all model modules to register them with SQLAlchemy."""
    model_modules = [
        'app.core.models',
        'app.models.user',
        'app.models.tenant',
        'app.modules.accounting.models',
        'app.modules.autoconfig.models',
        'app.modules.banking.models',
        'app.modules.country_packs.models',
        'app.modules.country_packs.france.models',
        'app.modules.dashboard.models',
        'app.modules.documents.models',
        'app.modules.hr.models',
        'app.modules.invoicing.models',
        'app.modules.notifications.models',
        'app.modules.reporting.models',
        'app.modules.stripe_integration.models',
        'app.modules.tax_management.models',
        'app.modules.treasury.models',
    ]

    loaded_modules = []
    for module_name in model_modules:
        try:
            module = importlib.import_module(module_name)
            loaded_modules.append((module_name, module))
        except ImportError as e:
            print(f"⚠ Could not import {module_name}: {e}")

    return loaded_modules


def get_all_models(loaded_modules: list) -> list:
    """Extract all SQLAlchemy model classes from loaded modules."""
    from app.core.database import Base

    models = []
    for module_name, module in loaded_modules:
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, Base) and
                obj is not Base and
                hasattr(obj, '__tablename__')):
                models.append((module_name, obj))

    return models


def validate_table_creation_order():
    """Verify that table dependencies are correctly ordered."""
    from app.core.database import Base

    # SQLAlchemy handles dependency ordering automatically via MetaData.sorted_tables
    try:
        sorted_tables = Base.metadata.sorted_tables
        print("\n📋 Table creation order (sorted by dependencies):")
        print("-" * 50)
        for i, table in enumerate(sorted_tables, 1):
            fks = [f"{fk.parent.name} -> {fk.column.table.name}.{fk.column.name}"
                   for fk in table.foreign_key_constraints]
            fk_str = f" (FKs: {', '.join(fks)})" if fks else ""
            print(f"  {i:3d}. {table.name}{fk_str}")
        return True
    except Exception as e:
        print(f"\n❌ Error determining table order: {e}")
        return False


def check_database_connection():
    """Test database connection and verify UUID type support."""
    try:
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n🐘 PostgreSQL: {version[:50]}...")

            # Check UUID extension
            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp')"
            ))
            has_uuid_ext = result.scalar()
            print(f"📦 uuid-ossp extension: {'✓ Installed' if has_uuid_ext else '✗ Not installed'}")

            # Test gen_random_uuid() (available in PG 13+)
            try:
                conn.execute(text("SELECT gen_random_uuid()"))
                print("🎲 gen_random_uuid(): ✓ Available")
            except Exception:
                print("🎲 gen_random_uuid(): ✗ Not available (use uuid-ossp)")

            return True
    except Exception as e:
        print(f"\n⚠ Could not connect to database: {e}")
        return False


def main():
    """Main validation function."""
    print("=" * 60)
    print("AZALS ERP - UUID Schema Validation")
    print("=" * 60)

    # Import all models
    print("\n📂 Loading model modules...")
    loaded_modules = import_all_models()
    print(f"   Loaded {len(loaded_modules)} modules")

    # Get all model classes
    print("\n🔍 Extracting model classes...")
    models = get_all_models(loaded_modules)
    print(f"   Found {len(models)} models")

    # Validate each model
    print("\n🔬 Validating models...")
    all_errors = []
    tables_checked = set()

    for module_name, model_class in models:
        table_name = model_class.__tablename__
        if table_name in tables_checked:
            continue
        tables_checked.add(table_name)

        errors = validate_model(model_class)
        all_errors.extend(errors)

    # Report results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    if all_errors:
        error_count = sum(1 for e in all_errors if e['severity'] == 'ERROR')
        warning_count = sum(1 for e in all_errors if e['severity'] == 'WARNING')

        print(f"\n❌ Found {error_count} errors, {warning_count} warnings:\n")

        for error in sorted(all_errors, key=lambda x: (x['severity'], x['table'])):
            icon = "❌" if error['severity'] == 'ERROR' else "⚠"
            print(f"  {icon} [{error['table']}.{error['column']}]")
            print(f"     {error['issue']}")
    else:
        print("\n✅ All models use UUID correctly!")

    # Check table order
    print("\n" + "-" * 60)
    validate_table_creation_order()

    # Check database connection (optional)
    print("\n" + "-" * 60)
    print("DATABASE CONNECTION CHECK")
    check_database_connection()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Tables checked: {len(tables_checked)}")
    print(f"  Errors: {sum(1 for e in all_errors if e['severity'] == 'ERROR')}")
    print(f"  Warnings: {sum(1 for e in all_errors if e['severity'] == 'WARNING')}")

    # Exit with appropriate code
    if any(e['severity'] == 'ERROR' for e in all_errors):
        print("\n❌ Validation FAILED - Please fix errors before deployment")
        return 1
    else:
        print("\n✅ Validation PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
