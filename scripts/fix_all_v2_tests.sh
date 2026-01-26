#!/bin/bash
# Fix all v2 test files to work with global conftest

echo "🔧 Fixing all v2 test files..."

# 1. Backup all module-level conftest.py files that might conflict
echo "📦 Backing up module conftest files..."
find app/modules/*/tests -name "conftest.py" -exec bash -c 'mv "$1" "$1.backup"' _ {} \;

# 2. Remove mock_*_service parameters from all test functions
echo "🧹 Cleaning test function signatures..."
for test_file in $(find app/modules -name "test_router_v2.py"); do
    echo "  Processing: $test_file"

    # Remove common mock service parameters
    sed -i 's/(test_client, mock_[a-z_]*_service)/(test_client)/g' "$test_file"
    sed -i 's/(test_client, sample_/( test_client, sample_/g' "$test_file"
done

echo "✅ All test files fixed!"
echo ""
echo "Next: Run pytest to verify"
