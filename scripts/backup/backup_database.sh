#!/bin/bash
#
# AZALSCORE - PostgreSQL Backup Script
# =====================================
# Automated database backup with:
# - Full database dumps
# - Compression (gzip)
# - Retention management
# - S3/Cloud upload support (optional)
# - Slack/Email notifications (optional)
#
# Usage:
#   ./backup_database.sh                    # Full backup
#   ./backup_database.sh --schema-only      # Schema only
#   ./backup_database.sh --data-only        # Data only
#   ./backup_database.sh --tenant TENANT_ID # Single tenant
#
# Environment Variables:
#   DATABASE_URL     - PostgreSQL connection URL (required)
#   BACKUP_DIR       - Backup directory (default: /var/backups/azalscore)
#   RETENTION_DAYS   - Days to keep backups (default: 30)
#   S3_BUCKET        - S3 bucket for remote storage (optional)
#   SLACK_WEBHOOK    - Slack webhook for notifications (optional)
#   BACKUP_ENCRYPTION_KEY - Path to GPG public key for encryption (optional)
#   BACKUP_PASSPHRASE     - Symmetric passphrase for encryption (alternative)
#

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BACKUP_DIR="${BACKUP_DIR:-/var/backups/azalscore}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCTIONS
# ============================================================================

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$1"; }
log_warn() { log "WARN" "${YELLOW}$1${NC}"; }
log_error() { log "ERROR" "${RED}$1${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$1${NC}"; }

parse_database_url() {
    # Parse DATABASE_URL into components
    # Format: postgresql://user:password@host:port/database

    if [[ -z "${DATABASE_URL:-}" ]]; then
        log_error "DATABASE_URL environment variable is not set"
        exit 1
    fi

    # Extract components using bash parameter expansion
    local url="${DATABASE_URL#postgresql://}"
    url="${url#postgres://}"

    # Extract user:password
    local userpass="${url%%@*}"
    DB_USER="${userpass%%:*}"
    DB_PASS="${userpass#*:}"

    # Extract host:port/database
    local hostportdb="${url#*@}"
    local hostport="${hostportdb%%/*}"
    DB_NAME="${hostportdb#*/}"
    DB_NAME="${DB_NAME%%\?*}"  # Remove query params

    DB_HOST="${hostport%%:*}"
    if [[ "$hostport" == *":"* ]]; then
        DB_PORT="${hostport#*:}"
    else
        DB_PORT="5432"
    fi
}

check_dependencies() {
    local missing=()

    for cmd in pg_dump gzip; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    # Check for encryption tools if encryption is enabled
    if [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]] || [[ -n "${BACKUP_PASSPHRASE:-}" ]]; then
        if ! command -v gpg &> /dev/null; then
            missing+=("gpg")
        fi
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install with: apt-get install postgresql-client gzip gnupg"
        exit 1
    fi
}

encrypt_backup() {
    local backup_file="$1"
    local encrypted_file="${backup_file}.gpg"

    # Skip if no encryption configured
    if [[ -z "${BACKUP_ENCRYPTION_KEY:-}" ]] && [[ -z "${BACKUP_PASSPHRASE:-}" ]]; then
        log_warn "SÉCURITÉ P0-10: Backup NON CHIFFRÉ! Configurez BACKUP_ENCRYPTION_KEY ou BACKUP_PASSPHRASE"
        echo "$backup_file"
        return
    fi

    log_info "Chiffrement du backup (P0-10 sécurité)..."

    if [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]]; then
        # Asymmetric encryption with GPG public key
        if gpg --batch --yes --trust-model always \
            --recipient-file "$BACKUP_ENCRYPTION_KEY" \
            --output "$encrypted_file" \
            --encrypt "$backup_file"; then
            rm -f "$backup_file"
            log_success "Backup chiffré avec clé publique: $encrypted_file"
            echo "$encrypted_file"
        else
            log_error "Échec du chiffrement GPG"
            echo "$backup_file"
        fi
    elif [[ -n "${BACKUP_PASSPHRASE:-}" ]]; then
        # Symmetric encryption with passphrase
        if echo "$BACKUP_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
            --symmetric --cipher-algo AES256 \
            --output "$encrypted_file" \
            "$backup_file"; then
            rm -f "$backup_file"
            log_success "Backup chiffré avec passphrase: $encrypted_file"
            echo "$encrypted_file"
        else
            log_error "Échec du chiffrement symétrique"
            echo "$backup_file"
        fi
    fi
}

create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

run_backup() {
    local backup_type="${1:-full}"
    local tenant="${2:-}"
    local backup_file
    local pg_dump_opts=()

    # Build filename
    if [[ -n "$tenant" ]]; then
        backup_file="${BACKUP_DIR}/azalscore_tenant_${tenant}_${TIMESTAMP}.sql"
    else
        backup_file="${BACKUP_DIR}/azalscore_${backup_type}_${TIMESTAMP}.sql"
    fi

    # Build pg_dump options
    pg_dump_opts+=("-h" "$DB_HOST")
    pg_dump_opts+=("-p" "$DB_PORT")
    pg_dump_opts+=("-U" "$DB_USER")
    pg_dump_opts+=("-d" "$DB_NAME")
    pg_dump_opts+=("--no-password")
    pg_dump_opts+=("-v")

    case "$backup_type" in
        schema)
            pg_dump_opts+=("--schema-only")
            ;;
        data)
            pg_dump_opts+=("--data-only")
            ;;
        full)
            # Default: full backup
            ;;
    esac

    # Add tenant filter if specified
    if [[ -n "$tenant" ]]; then
        # Create a temp SQL file with tenant-specific WHERE clause
        # This is a simplified approach - in production, you might want
        # to backup tenant-specific schemas if using schema-based isolation
        pg_dump_opts+=("--table=*")
        log_warn "Tenant-specific backup uses full dump. Consider schema-based isolation for true tenant backups."
    fi

    log_info "Starting $backup_type backup..."
    log_info "Output file: $backup_file"

    # Set password via environment
    export PGPASSWORD="$DB_PASS"

    # Run pg_dump
    if pg_dump "${pg_dump_opts[@]}" > "$backup_file" 2>> "$LOG_FILE"; then
        # Compress
        log_info "Compressing backup..."
        gzip -f "$backup_file"
        backup_file="${backup_file}.gz"

        # SÉCURITÉ P0-10: Encrypt backup
        backup_file=$(encrypt_backup "$backup_file")

        # Get file size
        local size=$(du -h "$backup_file" | cut -f1)
        log_success "Backup completed: $backup_file ($size)"

        echo "$backup_file"
    else
        log_error "Backup failed!"
        exit 1
    fi

    unset PGPASSWORD
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."

    local count=$(find "$BACKUP_DIR" -name "azalscore_*.sql.gz" -type f -mtime +$RETENTION_DAYS | wc -l)

    if [[ $count -gt 0 ]]; then
        find "$BACKUP_DIR" -name "azalscore_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
        log_info "Deleted $count old backup(s)"
    else
        log_info "No old backups to clean up"
    fi
}

upload_to_s3() {
    local backup_file="$1"

    if [[ -z "${S3_BUCKET:-}" ]]; then
        log_info "S3_BUCKET not set, skipping remote upload"
        return
    fi

    if ! command -v aws &> /dev/null; then
        log_warn "AWS CLI not installed, skipping S3 upload"
        return
    fi

    local s3_path="s3://${S3_BUCKET}/backups/$(basename "$backup_file")"

    log_info "Uploading to S3: $s3_path"

    if aws s3 cp "$backup_file" "$s3_path" --storage-class STANDARD_IA; then
        log_success "Upload completed"
    else
        log_error "S3 upload failed"
    fi
}

send_notification() {
    local status="$1"
    local message="$2"
    local backup_file="${3:-}"

    if [[ -z "${SLACK_WEBHOOK:-}" ]]; then
        return
    fi

    local color
    case "$status" in
        success) color="good" ;;
        warning) color="warning" ;;
        error) color="danger" ;;
    esac

    local payload=$(cat <<EOF
{
    "attachments": [{
        "color": "$color",
        "title": "AZALSCORE Database Backup",
        "text": "$message",
        "fields": [
            {"title": "Environment", "value": "${ENVIRONMENT:-production}", "short": true},
            {"title": "Database", "value": "$DB_NAME", "short": true},
            {"title": "Timestamp", "value": "$TIMESTAMP", "short": true},
            {"title": "File", "value": "$(basename "${backup_file:-N/A}")", "short": true}
        ],
        "footer": "AZALSCORE Backup System",
        "ts": $(date +%s)
    }]
}
EOF
)

    curl -s -X POST -H 'Content-type: application/json' \
        --data "$payload" "$SLACK_WEBHOOK" > /dev/null
}

show_usage() {
    cat <<EOF
AZALSCORE PostgreSQL Backup Script

Usage: $0 [OPTIONS]

Options:
    --full          Full database backup (default)
    --schema-only   Backup schema only (no data)
    --data-only     Backup data only (no schema)
    --tenant ID     Backup specific tenant data
    --no-cleanup    Skip cleanup of old backups
    --no-upload     Skip S3 upload
    --help          Show this help

Environment Variables:
    DATABASE_URL    PostgreSQL connection URL (required)
    BACKUP_DIR      Backup directory (default: /var/backups/azalscore)
    RETENTION_DAYS  Days to keep backups (default: 30)
    S3_BUCKET       S3 bucket for remote storage
    SLACK_WEBHOOK   Slack webhook for notifications

Examples:
    $0                          # Full backup
    $0 --schema-only            # Schema only
    $0 --tenant tenant_123      # Single tenant
EOF
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local backup_type="full"
    local tenant=""
    local do_cleanup=true
    local do_upload=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --full)
                backup_type="full"
                shift
                ;;
            --schema-only)
                backup_type="schema"
                shift
                ;;
            --data-only)
                backup_type="data"
                shift
                ;;
            --tenant)
                tenant="$2"
                shift 2
                ;;
            --no-cleanup)
                do_cleanup=false
                shift
                ;;
            --no-upload)
                do_upload=false
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    echo ""
    echo "========================================"
    echo "AZALSCORE DATABASE BACKUP"
    echo "========================================"
    echo ""

    # Initialize
    create_backup_dir
    check_dependencies
    parse_database_url

    log_info "Database: $DB_NAME@$DB_HOST:$DB_PORT"
    log_info "Backup type: $backup_type"
    [[ -n "$tenant" ]] && log_info "Tenant: $tenant"

    # Run backup
    local backup_file
    backup_file=$(run_backup "$backup_type" "$tenant")

    # Cleanup old backups
    if $do_cleanup; then
        cleanup_old_backups
    fi

    # Upload to S3
    if $do_upload; then
        upload_to_s3 "$backup_file"
    fi

    # Send notification
    send_notification "success" "Database backup completed successfully" "$backup_file"

    echo ""
    echo "========================================"
    log_success "Backup completed!"
    echo "========================================"
    echo ""
}

main "$@"
