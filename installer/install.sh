#!/bin/bash
# ==============================================================================
# AZALSCORE - Installateur Universel Autonome
# ==============================================================================
# Installation 100% scriptee, sans intervention humaine.
# Multi-plateforme: Linux, macOS (Intel & ARM), Windows (via Docker)
# Zero dependance cloud, zero SDK proprietaire.
#
# USAGE:
#   ./install.sh                    # Installation interactive
#   ./install.sh --auto             # Installation automatique (mode headless)
#   ./install.sh --uninstall        # Desinstallation
#   ./install.sh --upgrade          # Mise a jour
#   ./install.sh --backup           # Sauvegarde manuelle
#   ./install.sh --restore <date>   # Restauration depuis sauvegarde
#
# PREREQUIS:
#   - Docker & Docker Compose (installes automatiquement si absents)
#   - 2GB RAM minimum
#   - 10GB espace disque
#
# ==============================================================================

set -e  # Arret en cas d'erreur

# ==============================================================================
# CONSTANTES
# ==============================================================================

readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly AZALS_DIR="${SCRIPT_DIR}"
readonly DATA_DIR="${AZALS_DIR}/data"
readonly BACKUP_DIR="${AZALS_DIR}/backups"
readonly LOG_FILE="${AZALS_DIR}/install.log"
readonly ENV_FILE="${AZALS_DIR}/.env"

# Couleurs (desactivees si non-interactif)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${msg}" | tee -a "${LOG_FILE}"
}

info() { log "INFO" "${GREEN}$*${NC}"; }
warn() { log "WARN" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; }
fatal() {
    error "$*"
    exit 1
}

# Genere une cle aleatoire securisee
generate_secret() {
    local length="${1:-64}"
    if command -v openssl &> /dev/null; then
        openssl rand -base64 "$length" | tr -dc 'a-zA-Z0-9' | head -c "$length"
    elif command -v python3 &> /dev/null; then
        python3 -c "import secrets; print(secrets.token_urlsafe($length))" | head -c "$length"
    else
        head -c "$length" /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c "$length"
    fi
}

# Genere une cle Fernet
generate_fernet_key() {
    if command -v python3 &> /dev/null; then
        python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || \
        python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
    else
        # Fallback: genere une cle compatible
        echo "$(head -c 32 /dev/urandom | base64 | tr '+/' '-_')"
    fi
}

# ==============================================================================
# DETECTION SYSTEME
# ==============================================================================

detect_os() {
    local os=""
    local arch=""

    case "$(uname -s)" in
        Linux*)     os="linux" ;;
        Darwin*)    os="macos" ;;
        MINGW*|MSYS*|CYGWIN*)
                    os="windows" ;;
        *)          os="unknown" ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64)   arch="amd64" ;;
        aarch64|arm64)  arch="arm64" ;;
        armv7l)         arch="arm" ;;
        *)              arch="unknown" ;;
    esac

    echo "${os}:${arch}"
}

check_requirements() {
    local os_arch=$(detect_os)
    local os="${os_arch%%:*}"
    local arch="${os_arch##*:}"

    info "Systeme detecte: OS=${os}, Architecture=${arch}"

    # Verification memoire
    local mem_total=0
    if [ "$os" = "linux" ]; then
        mem_total=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
    elif [ "$os" = "macos" ]; then
        mem_total=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024)}')
    fi

    if [ "$mem_total" -lt 2000 ] && [ "$mem_total" -gt 0 ]; then
        warn "Memoire insuffisante: ${mem_total}MB (recommande: 2048MB)"
    fi

    # Verification espace disque
    local disk_free=$(df -m "${AZALS_DIR}" | awk 'NR==2 {print $4}')
    if [ "$disk_free" -lt 10000 ]; then
        warn "Espace disque faible: ${disk_free}MB (recommande: 10000MB)"
    fi

    info "Ressources: RAM=${mem_total}MB, Disque libre=${disk_free}MB"
}

# ==============================================================================
# INSTALLATION DOCKER
# ==============================================================================

check_docker() {
    if ! command -v docker &> /dev/null; then
        return 1
    fi

    if ! docker info &> /dev/null; then
        return 1
    fi

    return 0
}

install_docker() {
    local os_arch=$(detect_os)
    local os="${os_arch%%:*}"

    info "Installation de Docker..."

    case "$os" in
        linux)
            install_docker_linux
            ;;
        macos)
            fatal "Sur macOS, installez Docker Desktop manuellement: https://www.docker.com/products/docker-desktop"
            ;;
        windows)
            fatal "Sur Windows, installez Docker Desktop manuellement: https://www.docker.com/products/docker-desktop"
            ;;
        *)
            fatal "Systeme non supporte pour l'installation automatique de Docker"
            ;;
    esac
}

install_docker_linux() {
    # Detection de la distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        local distro="$ID"
    else
        fatal "Distribution Linux non reconnue"
    fi

    info "Distribution detectee: $distro"

    case "$distro" in
        ubuntu|debian)
            install_docker_debian
            ;;
        centos|rhel|fedora|rocky|almalinux)
            install_docker_rhel
            ;;
        alpine)
            install_docker_alpine
            ;;
        *)
            warn "Distribution $distro: installation Docker generique"
            install_docker_generic
            ;;
    esac
}

install_docker_debian() {
    info "Installation Docker pour Debian/Ubuntu..."

    # Mise a jour
    sudo apt-get update -qq

    # Installation des prerequis
    sudo apt-get install -y -qq \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Ajout de la cle GPG Docker
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg | \
        sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Ajout du repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Installation Docker
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Ajout de l'utilisateur au groupe docker
    sudo usermod -aG docker "$USER" 2>/dev/null || true

    # Demarrage du service
    sudo systemctl enable docker
    sudo systemctl start docker

    info "Docker installe avec succes"
}

install_docker_rhel() {
    info "Installation Docker pour RHEL/CentOS/Fedora..."

    # Installation des prerequis
    sudo dnf install -y dnf-plugins-core

    # Ajout du repository Docker
    sudo dnf config-manager --add-repo https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/docker-ce.repo

    # Installation Docker
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Demarrage du service
    sudo systemctl enable docker
    sudo systemctl start docker

    # Ajout de l'utilisateur au groupe docker
    sudo usermod -aG docker "$USER" 2>/dev/null || true

    info "Docker installe avec succes"
}

install_docker_alpine() {
    info "Installation Docker pour Alpine..."

    sudo apk add --no-cache docker docker-cli-compose
    sudo rc-update add docker boot
    sudo service docker start

    info "Docker installe avec succes"
}

install_docker_generic() {
    info "Installation Docker via script officiel..."

    curl -fsSL https://get.docker.com | sh

    # Ajout de l'utilisateur au groupe docker
    sudo usermod -aG docker "$USER" 2>/dev/null || true

    info "Docker installe avec succes"
}

# ==============================================================================
# CONFIGURATION
# ==============================================================================

generate_env_file() {
    info "Generation de la configuration..."

    # Genere les secrets
    local secret_key=$(generate_secret 64)
    local bootstrap_secret=$(generate_secret 64)
    local encryption_key=$(generate_fernet_key)
    local db_password=$(generate_secret 32)
    local admin_password=$(generate_secret 16)

    # Cree le fichier .env
    cat > "${ENV_FILE}" << EOF
# ==============================================================================
# AZALSCORE - Configuration Generee Automatiquement
# ==============================================================================
# Date de generation: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# Version: ${SCRIPT_VERSION}
# ATTENTION: Ce fichier contient des secrets. Ne pas partager.
# ==============================================================================

# Environnement
ENVIRONMENT=production
DEBUG=false

# Base de donnees
DATABASE_URL=postgresql://azals:${db_password}@postgres:5432/azalscore
POSTGRES_USER=azals
POSTGRES_PASSWORD=${db_password}
POSTGRES_DB=azalscore

# Securite
SECRET_KEY=${secret_key}
BOOTSTRAP_SECRET=${bootstrap_secret}
ENCRYPTION_KEY=${encryption_key}
MASTER_ENCRYPTION_KEY=${encryption_key}

# CORS (adapter selon votre domaine)
CORS_ORIGINS=http://localhost,http://localhost:5173,http://localhost:3000

# Redis
REDIS_URL=redis://redis:6379/0

# Admin initial (changez ces valeurs!)
ADMIN_EMAIL=admin@azalscore.local
ADMIN_PASSWORD=${admin_password}
BOOTSTRAP_TENANT_SLUG=main
BOOTSTRAP_TENANT_NAME=Organisation Principale

# Backup (configurer pour activer les sauvegardes externes)
BACKUP_PROVIDER=local
BACKUP_PATH=${BACKUP_DIR}
BACKUP_RETENTION_DAYS=7

# Alertes (optionnel)
# ALERT_WEBHOOK_URL=https://hooks.slack.com/...
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=alerts@example.com
# SMTP_PASSWORD=...
# ALERT_EMAIL_TO=admin@example.com

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
EOF

    chmod 600 "${ENV_FILE}"

    info "Configuration generee: ${ENV_FILE}"
    warn "IMPORTANT: Notez le mot de passe admin temporaire: ${admin_password}"
    warn "Ce mot de passe devra etre change a la premiere connexion."
}

# ==============================================================================
# INSTALLATION
# ==============================================================================

install_azalscore() {
    info "Installation d'AZALSCORE..."

    # Cree les repertoires necessaires
    mkdir -p "${DATA_DIR}"
    mkdir -p "${BACKUP_DIR}"
    mkdir -p "${AZALS_DIR}/logs"

    # Verifie Docker
    if ! check_docker; then
        install_docker
    fi

    # Genere la configuration si absente
    if [ ! -f "${ENV_FILE}" ]; then
        generate_env_file
    fi

    # Construction des images
    info "Construction des images Docker..."
    cd "${AZALS_DIR}"

    # Utilise docker-compose.prod.yml s'il existe
    if [ -f "docker-compose.prod.yml" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi

    docker compose -f "${COMPOSE_FILE}" build --no-cache 2>&1 | tee -a "${LOG_FILE}"

    # Demarrage des services
    info "Demarrage des services..."
    docker compose -f "${COMPOSE_FILE}" up -d 2>&1 | tee -a "${LOG_FILE}"

    # Attente que les services soient prets
    info "Attente du demarrage des services..."
    sleep 10

    # Verification de sante
    local retries=30
    local wait=5

    while [ $retries -gt 0 ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            info "API en ligne!"
            break
        fi
        retries=$((retries - 1))
        info "Attente de l'API... (${retries} tentatives restantes)"
        sleep $wait
    done

    if [ $retries -eq 0 ]; then
        error "L'API n'a pas demarre dans le delai imparti"
        docker compose -f "${COMPOSE_FILE}" logs --tail=50
        return 1
    fi

    # Execution des migrations
    info "Execution des migrations de base de donnees..."
    docker compose -f "${COMPOSE_FILE}" exec -T api python -c "
from app.db.base import Base
from app.core.database import engine
Base.metadata.create_all(bind=engine)
print('Migrations appliquees')
" 2>&1 | tee -a "${LOG_FILE}" || warn "Migrations: verification manuelle recommandee"

    info "Installation terminee!"
}

# ==============================================================================
# TESTS
# ==============================================================================

run_tests() {
    info "Execution des tests de validation..."

    local tests_passed=0
    local tests_failed=0

    # Test 1: API accessible
    info "Test 1/5: Verification API..."
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        info "  [OK] API accessible"
        tests_passed=$((tests_passed + 1))
    else
        error "  [FAIL] API non accessible"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 2: Base de donnees
    info "Test 2/5: Verification base de donnees..."
    if docker compose exec -T postgres pg_isready -U azals > /dev/null 2>&1; then
        info "  [OK] PostgreSQL operationnel"
        tests_passed=$((tests_passed + 1))
    else
        error "  [FAIL] PostgreSQL non disponible"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 3: Redis
    info "Test 3/5: Verification Redis..."
    if docker compose exec -T redis redis-cli ping 2>&1 | grep -q PONG; then
        info "  [OK] Redis operationnel"
        tests_passed=$((tests_passed + 1))
    else
        warn "  [WARN] Redis non disponible (optionnel)"
    fi

    # Test 4: Frontend
    info "Test 4/5: Verification Frontend..."
    if curl -sf http://localhost > /dev/null 2>&1 || curl -sf http://localhost:5173 > /dev/null 2>&1; then
        info "  [OK] Frontend accessible"
        tests_passed=$((tests_passed + 1))
    else
        warn "  [WARN] Frontend non accessible (verifier configuration)"
    fi

    # Test 5: Securite
    info "Test 5/5: Verification securite..."
    local env_perms=$(stat -c %a "${ENV_FILE}" 2>/dev/null || stat -f %Lp "${ENV_FILE}" 2>/dev/null)
    if [ "$env_perms" = "600" ]; then
        info "  [OK] Permissions .env correctes"
        tests_passed=$((tests_passed + 1))
    else
        warn "  [WARN] Permissions .env: $env_perms (recommande: 600)"
    fi

    # Resume
    echo ""
    info "======================================"
    info "RESUME DES TESTS"
    info "======================================"
    info "Tests reussis:  ${tests_passed}"
    if [ $tests_failed -gt 0 ]; then
        error "Tests echoues:  ${tests_failed}"
    else
        info "Tests echoues:  ${tests_failed}"
    fi
    info "======================================"

    if [ $tests_failed -gt 0 ]; then
        return 1
    fi
    return 0
}

# ==============================================================================
# BACKUP
# ==============================================================================

create_backup() {
    local backup_date=$(date '+%Y-%m-%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/azalscore_${backup_date}.tar.gz"

    info "Creation de la sauvegarde..."

    # Sauvegarde de la base de donnees
    info "Export de la base de donnees..."
    docker compose exec -T postgres pg_dump -U azals azalscore | gzip > "${BACKUP_DIR}/db_${backup_date}.sql.gz"

    # Sauvegarde des volumes
    info "Sauvegarde des donnees..."
    tar -czf "${backup_file}" \
        -C "${AZALS_DIR}" \
        --exclude='*.log' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='node_modules' \
        data/ \
        "${ENV_FILE}" \
        "${BACKUP_DIR}/db_${backup_date}.sql.gz"

    # Nettoyage
    rm -f "${BACKUP_DIR}/db_${backup_date}.sql.gz"

    # Verification
    if [ -f "${backup_file}" ]; then
        local size=$(du -h "${backup_file}" | cut -f1)
        info "Sauvegarde creee: ${backup_file} (${size})"
    else
        error "Echec de la creation de la sauvegarde"
        return 1
    fi

    # Rotation des anciennes sauvegardes
    local retention_days="${BACKUP_RETENTION_DAYS:-7}"
    find "${BACKUP_DIR}" -name "azalscore_*.tar.gz" -mtime +${retention_days} -delete
    info "Sauvegardes de plus de ${retention_days} jours supprimees"

    return 0
}

restore_backup() {
    local backup_date="$1"

    if [ -z "$backup_date" ]; then
        error "Usage: $0 --restore <date>"
        info "Sauvegardes disponibles:"
        ls -la "${BACKUP_DIR}"/*.tar.gz 2>/dev/null || echo "  Aucune sauvegarde trouvee"
        return 1
    fi

    local backup_file="${BACKUP_DIR}/azalscore_${backup_date}.tar.gz"

    if [ ! -f "${backup_file}" ]; then
        # Recherche approximative
        backup_file=$(ls -1 "${BACKUP_DIR}"/azalscore_${backup_date}*.tar.gz 2>/dev/null | head -1)
    fi

    if [ ! -f "${backup_file}" ]; then
        error "Sauvegarde non trouvee: ${backup_date}"
        return 1
    fi

    info "Restauration depuis: ${backup_file}"
    warn "ATTENTION: Cette operation va remplacer les donnees actuelles!"

    # Arret des services
    info "Arret des services..."
    docker compose down

    # Extraction de la sauvegarde
    info "Extraction de la sauvegarde..."
    tar -xzf "${backup_file}" -C "${AZALS_DIR}"

    # Restauration de la base de donnees
    local db_backup=$(ls -1 "${BACKUP_DIR}"/db_*.sql.gz 2>/dev/null | head -1)
    if [ -f "$db_backup" ]; then
        info "Restauration de la base de donnees..."
        docker compose up -d postgres
        sleep 5
        gunzip -c "$db_backup" | docker compose exec -T postgres psql -U azals azalscore
        rm -f "$db_backup"
    fi

    # Redemarrage
    info "Redemarrage des services..."
    docker compose up -d

    info "Restauration terminee!"
}

# ==============================================================================
# COMMANDES
# ==============================================================================

show_help() {
    cat << EOF
AZALSCORE - Installateur Universel v${SCRIPT_VERSION}

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --auto          Installation automatique (mode headless)
    --uninstall     Desinstallation complete
    --upgrade       Mise a jour vers la derniere version
    --backup        Creer une sauvegarde
    --restore DATE  Restaurer depuis une sauvegarde
    --test          Executer les tests de validation
    --status        Afficher le statut des services
    --logs          Afficher les logs
    --help          Afficher cette aide

EXEMPLES:
    $0                      # Installation interactive
    $0 --auto               # Installation automatique
    $0 --backup             # Sauvegarde manuelle
    $0 --restore 2024-01-15 # Restauration

DOCUMENTATION:
    https://github.com/MASITH-developpement/Azalscore

EOF
}

show_status() {
    info "Statut des services AZALSCORE:"
    echo ""
    docker compose ps
    echo ""

    info "Utilisation des ressources:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

show_logs() {
    local service="$1"
    if [ -n "$service" ]; then
        docker compose logs -f "$service"
    else
        docker compose logs -f --tail=100
    fi
}

uninstall() {
    warn "ATTENTION: Cette operation va supprimer AZALSCORE et toutes ses donnees!"
    warn "Appuyez sur Ctrl+C pour annuler, ou attendez 10 secondes pour continuer..."
    sleep 10

    info "Desinstallation en cours..."

    # Arret des services
    docker compose down -v --remove-orphans 2>/dev/null || true

    # Suppression des images
    docker compose down --rmi all 2>/dev/null || true

    info "Desinstallation terminee"
    warn "Les fichiers de configuration et sauvegardes ont ete conserves dans ${AZALS_DIR}"
}

upgrade() {
    info "Mise a jour d'AZALSCORE..."

    # Sauvegarde avant mise a jour
    create_backup

    # Pull des nouvelles images
    docker compose pull

    # Reconstruction
    docker compose build --no-cache

    # Redemarrage avec les nouvelles images
    docker compose up -d

    info "Mise a jour terminee!"
    run_tests
}

# ==============================================================================
# MAIN
# ==============================================================================

main() {
    # Initialisation du log
    mkdir -p "$(dirname "${LOG_FILE}")"
    echo "=== Installation AZALSCORE $(date) ===" >> "${LOG_FILE}"

    info "======================================"
    info "AZALSCORE Installateur v${SCRIPT_VERSION}"
    info "======================================"

    # Parse des arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --auto)
            check_requirements
            install_azalscore
            run_tests
            ;;
        --uninstall)
            uninstall
            ;;
        --upgrade)
            upgrade
            ;;
        --backup)
            create_backup
            ;;
        --restore)
            restore_backup "$2"
            ;;
        --test)
            run_tests
            ;;
        --status)
            show_status
            ;;
        --logs)
            show_logs "$2"
            ;;
        "")
            # Installation interactive
            check_requirements
            install_azalscore
            run_tests
            ;;
        *)
            error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Execution
main "$@"
