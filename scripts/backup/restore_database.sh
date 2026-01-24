#!/bin/bash
#
# AZALSCORE - PostgreSQL Restore Script
# ======================================
# Restores database from backup with safety checks:
# - Backup file validation
# - Database connection test
# - Optional dry-run mode
# - Point-in-time recovery support
#
# Usage:
#   ./restore_database.sh backup_file.sql.gz
#   ./restore_database.sh backup_file.sql.gz.gpg  # Encrypted backup
#   ./restore_database.sh --list              # List available backups
#   ./restore_database.sh --dry-run file.gz   # Test without restoring
#
# Environment Variables:
#   DATABASE_URL          - PostgreSQL connection URL (required)
#   BACKUP_DIR            - Backup directory (default: /var/backups/azalscore)
#   BACKUP_DECRYPTION_KEY - Path to GPG private key for decryption
#   BACKUP_PASSPHRASE     - Symmetric passphrase for decryption
#

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/azalscore}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# FUNCTIONS
# ============================================================================

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

parse_database_url() {
    if [[ -z "${DATABASE_URL:-}" ]]; then
        log_error "DATABASE_URL environment variable is not set"
        exit 1
    fi

    local url="${DATABASE_URL#postgresql://}"
    url="${url#postgres://}"

    local userpass="${url%%@*}"
    DB_USER="${userpass%%:*}"
    DB_PASS="${userpass#*:}"

    local hostportdb="${url#*@}"
    local hostport="${hostportdb%%/*}"
    DB_NAME="${hostportdb#*/}"
    DB_NAME="${DB_NAME%%\?*}"

    DB_HOST="${hostport%%:*}"
    if [[ "$hostport" == *":"* ]]; then
        DB_PORT="${hostport#*:}"
    else
        DB_PORT="5432"
    fi
}

list_backups() {
    echo ""
    echo "Available Backups in $BACKUP_DIR:"
    echo "=================================="

    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warn "Backup directory does not exist"
        return
    fi

    local files=$(find "$BACKUP_DIR" -name "azalscore_*.sql.gz" -type f | sort -r)

    if [[ -z "$files" ]]; then
        log_warn "No backups found"
        return
    fi

    echo ""
    printf "%-50s %10s %s\n" "FILENAME" "SIZE" "DATE"
    printf "%-50s %10s %s\n" "--------" "----" "----"

    for f in $files; do
        local name=$(basename "$f")
        local size=$(du -h "$f" | cut -f1)
        local date=$(stat -c %y "$f" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$f" 2>/dev/null)
        printf "%-50s %10s %s\n" "$name" "$size" "$date"
    done

    echo ""
}

decrypt_backup() {
    local backup_file="$1"
    local decrypted_file

    # Check if file is encrypted
    if [[ "$backup_file" != *.gpg ]]; then
        echo "$backup_file"
        return
    fi

    log_info "Déchiffrement du backup chiffré..."

    # Remove .gpg extension for decrypted file
    decrypted_file="${backup_file%.gpg}"

    if [[ -n "${BACKUP_DECRYPTION_KEY:-}" ]]; then
        # Asymmetric decryption with private key
        if gpg --batch --yes \
            --decrypt \
            --output "$decrypted_file" \
            "$backup_file"; then
            log_success "Backup déchiffré: $decrypted_file"
            echo "$decrypted_file"
        else
            log_error "Échec du déchiffrement GPG (vérifiez votre clé privée)"
            exit 1
        fi
    elif [[ -n "${BACKUP_PASSPHRASE:-}" ]]; then
        # Symmetric decryption with passphrase
        if echo "$BACKUP_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
            --decrypt \
            --output "$decrypted_file" \
            "$backup_file"; then
            log_success "Backup déchiffré: $decrypted_file"
            echo "$decrypted_file"
        else
            log_error "Échec du déchiffrement (vérifiez votre passphrase)"
            exit 1
        fi
    else
        log_error "Backup chiffré détecté mais ni BACKUP_DECRYPTION_KEY ni BACKUP_PASSPHRASE n'est défini"
        exit 1
    fi
}

validate_backup_file() {
    local backup_file="$1"

    if [[ ! -f "$backup_file" ]]; then
        # Check in backup directory
        if [[ -f "${BACKUP_DIR}/${backup_file}" ]]; then
            backup_file="${BACKUP_DIR}/${backup_file}"
        else
            log_error "Backup file not found: $backup_file"
            exit 1
        fi
    fi

    # Decrypt if encrypted
    if [[ "$backup_file" == *.gpg ]]; then
        backup_file=$(decrypt_backup "$backup_file")
    fi

    # Check if it's a valid gzip file
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file" 2>/dev/null; then
            log_error "Invalid gzip file: $backup_file"
            exit 1
        fi
    fi

    echo "$backup_file"
}

test_connection() {
    log_info "Testing database connection..."

    export PGPASSWORD="$DB_PASS"

    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log_success "Database connection OK"
        return 0
    else
        log_error "Cannot connect to database"
        return 1
    fi
}

create_pre_restore_backup() {
    log_info "Creating pre-restore backup..."

    local pre_backup="${BACKUP_DIR}/pre_restore_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"

    export PGPASSWORD="$DB_PASS"

    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$pre_backup"; then
        log_success "Pre-restore backup created: $pre_backup"
        echo "$pre_backup"
    else
        log_error "Failed to create pre-restore backup"
        exit 1
    fi
}

restore_backup() {
    local backup_file="$1"
    local dry_run="${2:-false}"

    log_info "Restoring from: $backup_file"

    export PGPASSWORD="$DB_PASS"

    local restore_cmd
    if [[ "$backup_file" == *.gz ]]; then
        restore_cmd="gunzip -c \"$backup_file\" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    else
        restore_cmd="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < \"$backup_file\""
    fi

    if $dry_run; then
        log_info "[DRY RUN] Would execute:"
        echo "  $restore_cmd"
        return 0
    fi

    # Execute restore
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --set ON_ERROR_STOP=on
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --set ON_ERROR_STOP=on < "$backup_file"
    fi

    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log_success "Restore completed successfully"
    else
        log_error "Restore failed with exit code: $exit_code"
        exit $exit_code
    fi
}

show_usage() {
    cat <<EOF
AZALSCORE PostgreSQL Restore Script

Usage: $0 [OPTIONS] BACKUP_FILE

Options:
    --list          List available backup files
    --dry-run       Show what would be done without restoring
    --no-backup     Skip creating pre-restore backup
    --force         Skip confirmation prompt
    --help          Show this help

Arguments:
    BACKUP_FILE     Path to backup file (.sql or .sql.gz)

Environment Variables:
    DATABASE_URL    PostgreSQL connection URL (required)
    BACKUP_DIR      Backup directory (default: /var/backups/azalscore)

Examples:
    $0 --list                           # List backups
    $0 azalscore_full_20260109.sql.gz   # Restore from file
    $0 --dry-run backup.sql.gz          # Test restore
    $0 --force backup.sql.gz            # Restore without confirmation
EOF
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local backup_file=""
    local dry_run=false
    local skip_backup=false
    local force=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --list)
                list_backups
                exit 0
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --no-backup)
                skip_backup=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                backup_file="$1"
                shift
                ;;
        esac
    done

    if [[ -z "$backup_file" ]]; then
        log_error "No backup file specified"
        show_usage
        exit 1
    fi

    echo ""
    echo "========================================"
    echo "AZALSCORE DATABASE RESTORE"
    echo "========================================"
    echo ""

    # Validate and parse
    parse_database_url
    backup_file=$(validate_backup_file "$backup_file")

    log_info "Database: $DB_NAME@$DB_HOST:$DB_PORT"
    log_info "Backup file: $backup_file"
    log_info "File size: $(du -h "$backup_file" | cut -f1)"

    if $dry_run; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi

    # Test connection
    if ! test_connection; then
        exit 1
    fi

    # Confirmation
    if ! $force && ! $dry_run; then
        echo ""
        log_warn "WARNING: This will overwrite data in database '$DB_NAME'"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Restore cancelled"
            exit 0
        fi
    fi

    # Create pre-restore backup
    if ! $skip_backup && ! $dry_run; then
        mkdir -p "$BACKUP_DIR"
        create_pre_restore_backup
    fi

    # Restore
    restore_backup "$backup_file" "$dry_run"

    echo ""
    echo "========================================"
    if $dry_run; then
        log_info "DRY RUN completed"
    else
        log_success "Restore completed!"
    fi
    echo "========================================"
    echo ""
}

main "$@"
