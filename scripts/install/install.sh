#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Installation Universelle (Linux / macOS)
#===============================================================================
# Point d'entrée principal pour l'installation automatisée de AZALSCORE
#
# Usage:
#   ./install.sh              # Installation interactive
#   ./install.sh --dev        # Mode développement
#   ./install.sh --prod       # Mode production
#   ./install.sh --help       # Aide
#
# Auteur: AZALS DevOps Team
# Version: 1.0.0
#===============================================================================

set -euo pipefail
IFS=$'\n\t'

#===============================================================================
# VARIABLES GLOBALES
#===============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly COMMON_DIR="${SCRIPT_DIR}/common"
readonly LOG_FILE="${PROJECT_ROOT}/install.log"
readonly VERSION="1.0.0"
readonly MIN_PYTHON_VERSION="3.11"
readonly REQUIRED_DISK_SPACE_MB=2048

# Couleurs pour le terminal
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color
readonly BOLD='\033[1m'

# Variables d'état
INSTALL_MODE=""          # dev, prod, cloud
OS_TYPE=""               # linux, darwin (macOS)
DISTRO=""                # debian, ubuntu, fedora, arch, macos
ARCH=""                  # x86_64, arm64
POSTGRES_LOCAL=true
INTERACTIVE=true
DRY_RUN=false

#===============================================================================
# FONCTIONS UTILITAIRES
#===============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        INFO)  echo -e "${BLUE}[INFO]${NC} ${message}" ;;
        OK)    echo -e "${GREEN}[OK]${NC} ${message}" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} ${message}" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} ${message}" ;;
        DEBUG) [[ "${DEBUG:-false}" == "true" ]] && echo -e "${CYAN}[DEBUG]${NC} ${message}" ;;
    esac

    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
}

print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
    ___   _____   _   _     _____  _____ _____ _____ _____
   / _ \ |__  /  / \ | |   /  ___|/  __ \  _  | ___ \  ___|
  / /_\ \  / /  / _ \| |   \ `--. | /  \/ | | | |_/ / |__
  |  _  | / /  / ___ \ |    `--. \| |   | | | |    /|  __|
  |_| |_|/_/  /_/   \_\_|___/\__/ | \__/\ \_/ / |\ \| |___
                       \_____\____/ \____/\___/\_| \_\____/

EOF
    echo -e "${NC}"
    echo -e "${BOLD}AZALSCORE - Système d'Installation v${VERSION}${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev           Mode développement (par défaut)"
    echo "  --prod          Mode production (avec sécurité renforcée)"
    echo "  --cloud         Mode cloud (configuration uniquement)"
    echo "  --non-interactive    Pas de prompts interactifs"
    echo "  --dry-run       Afficher les commandes sans les exécuter"
    echo "  --help, -h      Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0                   # Installation interactive"
    echo "  $0 --dev             # Installation développement"
    echo "  $0 --prod            # Installation production"
    echo ""
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log WARN "Exécution en tant que root détectée"
        if [[ "${INSTALL_MODE}" == "prod" ]]; then
            log INFO "Mode production: root requis pour certaines opérations"
        else
            log WARN "Il est recommandé de ne pas exécuter en tant que root pour le développement"
            if [[ "${INTERACTIVE}" == "true" ]]; then
                read -rp "Continuer quand même? [y/N] " response
                [[ ! "${response,,}" =~ ^(y|yes)$ ]] && exit 1
            fi
        fi
    elif [[ "${INSTALL_MODE}" == "prod" ]]; then
        log INFO "Certaines opérations nécessitent sudo"
        if ! sudo -v 2>/dev/null; then
            log ERROR "Accès sudo requis pour l'installation en production"
            exit 1
        fi
    fi
}

detect_os() {
    log INFO "Détection du système d'exploitation..."

    case "$(uname -s)" in
        Linux*)
            OS_TYPE="linux"
            if [[ -f /etc/os-release ]]; then
                # shellcheck source=/dev/null
                source /etc/os-release
                case "${ID:-}" in
                    debian|ubuntu|linuxmint|pop)
                        DISTRO="${ID}"
                        ;;
                    fedora|centos|rhel|rocky|almalinux)
                        DISTRO="${ID}"
                        ;;
                    arch|manjaro)
                        DISTRO="arch"
                        ;;
                    alpine)
                        DISTRO="alpine"
                        ;;
                    *)
                        DISTRO="unknown"
                        log WARN "Distribution non reconnue: ${ID:-unknown}"
                        ;;
                esac
            else
                DISTRO="unknown"
            fi
            ;;
        Darwin*)
            OS_TYPE="darwin"
            DISTRO="macos"
            ;;
        *)
            log ERROR "Système d'exploitation non supporté: $(uname -s)"
            exit 1
            ;;
    esac

    ARCH=$(uname -m)
    case "${ARCH}" in
        x86_64|amd64)   ARCH="x86_64" ;;
        arm64|aarch64)  ARCH="arm64" ;;
        *)
            log WARN "Architecture non standard: ${ARCH}"
            ;;
    esac

    log OK "OS: ${OS_TYPE} | Distro: ${DISTRO} | Arch: ${ARCH}"
}

check_internet() {
    log INFO "Vérification de la connexion Internet..."

    local test_urls=(
        "https://pypi.org"
        "https://github.com"
        "https://deb.debian.org"
    )

    for url in "${test_urls[@]}"; do
        if curl -s --connect-timeout 5 "${url}" > /dev/null 2>&1; then
            log OK "Connexion Internet active"
            return 0
        fi
    done

    log ERROR "Pas de connexion Internet détectée"
    exit 1
}

check_disk_space() {
    log INFO "Vérification de l'espace disque..."

    local available_mb
    if [[ "${OS_TYPE}" == "darwin" ]]; then
        available_mb=$(df -m "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    else
        available_mb=$(df -m "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    fi

    if [[ "${available_mb}" -lt "${REQUIRED_DISK_SPACE_MB}" ]]; then
        log ERROR "Espace disque insuffisant: ${available_mb}MB disponible, ${REQUIRED_DISK_SPACE_MB}MB requis"
        exit 1
    fi

    log OK "Espace disque: ${available_mb}MB disponible"
}

check_port() {
    local port="$1"
    local name="$2"

    if [[ "${OS_TYPE}" == "darwin" ]]; then
        if lsof -Pi ":${port}" -sTCP:LISTEN -t > /dev/null 2>&1; then
            log WARN "Port ${port} (${name}) déjà utilisé"
            return 1
        fi
    else
        if ss -tuln 2>/dev/null | grep -q ":${port} " || \
           netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            log WARN "Port ${port} (${name}) déjà utilisé"
            return 1
        fi
    fi
    return 0
}

check_ports() {
    log INFO "Vérification des ports..."

    local ports_ok=true

    if ! check_port 8000 "API AZALSCORE"; then
        ports_ok=false
    fi

    if ! check_port 5432 "PostgreSQL"; then
        log INFO "PostgreSQL peut être déjà installé (port 5432 utilisé)"
        if [[ "${INTERACTIVE}" == "true" ]]; then
            read -rp "Utiliser l'instance PostgreSQL existante? [Y/n] " response
            if [[ "${response,,}" =~ ^(n|no)$ ]]; then
                log ERROR "Port 5432 requis pour PostgreSQL"
                exit 1
            fi
            POSTGRES_LOCAL=false
        fi
    fi

    if ! check_port 3000 "Frontend" && [[ "${INSTALL_MODE}" == "dev" ]]; then
        log WARN "Port 3000 utilisé - le frontend devra utiliser un autre port"
    fi

    [[ "${ports_ok}" == "true" ]] && log OK "Ports principaux disponibles"
}

#===============================================================================
# INSTALLATION DES DÉPENDANCES SYSTÈME
#===============================================================================

install_system_deps_debian() {
    log INFO "Installation des dépendances système (Debian/Ubuntu)..."

    local packages=(
        "build-essential"
        "curl"
        "wget"
        "git"
        "software-properties-common"
        "libpq-dev"
        "libffi-dev"
        "libssl-dev"
        "python3-dev"
        "python3-pip"
        "python3-venv"
    )

    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        packages+=("ufw" "fail2ban" "nginx" "certbot" "python3-certbot-nginx")
    fi

    sudo apt-get update -qq
    sudo apt-get install -y -qq "${packages[@]}"

    log OK "Dépendances système installées"
}

install_system_deps_fedora() {
    log INFO "Installation des dépendances système (Fedora/RHEL)..."

    local packages=(
        "gcc"
        "gcc-c++"
        "make"
        "curl"
        "wget"
        "git"
        "libpq-devel"
        "libffi-devel"
        "openssl-devel"
        "python3-devel"
        "python3-pip"
    )

    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        packages+=("firewalld" "fail2ban" "nginx" "certbot" "python3-certbot-nginx")
    fi

    sudo dnf install -y -q "${packages[@]}"

    log OK "Dépendances système installées"
}

install_system_deps_arch() {
    log INFO "Installation des dépendances système (Arch Linux)..."

    local packages=(
        "base-devel"
        "curl"
        "wget"
        "git"
        "postgresql-libs"
        "libffi"
        "openssl"
        "python"
        "python-pip"
    )

    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        packages+=("ufw" "fail2ban" "nginx" "certbot" "certbot-nginx")
    fi

    sudo pacman -Sy --noconfirm "${packages[@]}"

    log OK "Dépendances système installées"
}

install_system_deps_macos() {
    log INFO "Installation des dépendances système (macOS)..."

    # Vérifier/installer Homebrew
    if ! command -v brew &> /dev/null; then
        log INFO "Installation de Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    local packages=(
        "python@3.12"
        "postgresql@15"
        "libpq"
        "openssl@3"
    )

    brew install "${packages[@]}" 2>/dev/null || true

    # Ajouter Python au PATH
    if [[ -d "/opt/homebrew/opt/python@3.12/bin" ]]; then
        export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"
    elif [[ -d "/usr/local/opt/python@3.12/bin" ]]; then
        export PATH="/usr/local/opt/python@3.12/bin:$PATH"
    fi

    log OK "Dépendances système installées"
}

install_system_deps() {
    case "${DISTRO}" in
        debian|ubuntu|linuxmint|pop)
            install_system_deps_debian
            ;;
        fedora|centos|rhel|rocky|almalinux)
            install_system_deps_fedora
            ;;
        arch|manjaro)
            install_system_deps_arch
            ;;
        macos)
            install_system_deps_macos
            ;;
        *)
            log WARN "Distribution non supportée pour l'installation automatique des dépendances"
            log INFO "Veuillez installer manuellement: python3.12+, pip, venv, libpq-dev"
            ;;
    esac
}

#===============================================================================
# CHARGEMENT DES MODULES
#===============================================================================

load_modules() {
    log INFO "Chargement des modules d'installation..."

    local modules=(
        "checks.sh"
        "env_generator.sh"
        "secrets.sh"
        "postgres.sh"
        "python.sh"
        "azalscore.sh"
        "systemd.sh"
        "firewall.sh"
        "summary.sh"
    )

    for module in "${modules[@]}"; do
        local module_path="${COMMON_DIR}/${module}"
        if [[ -f "${module_path}" ]]; then
            # shellcheck source=/dev/null
            source "${module_path}"
            log DEBUG "Module chargé: ${module}"
        else
            log ERROR "Module manquant: ${module_path}"
            exit 1
        fi
    done

    log OK "Tous les modules chargés"
}

#===============================================================================
# SÉLECTION DU MODE D'INSTALLATION
#===============================================================================

select_install_mode() {
    if [[ -n "${INSTALL_MODE}" ]]; then
        return
    fi

    echo ""
    echo -e "${BOLD}Sélectionnez le mode d'installation:${NC}"
    echo ""
    echo "  1) ${GREEN}Développement${NC} - Pour développer localement"
    echo "     • Debug activé"
    echo "     • Logs verbeux"
    echo "     • Hot-reload activé"
    echo ""
    echo "  2) ${YELLOW}Production${NC} - Pour un serveur de production"
    echo "     • Sécurité renforcée"
    echo "     • Service systemd"
    echo "     • Pare-feu configuré"
    echo ""
    echo "  3) ${CYAN}Cloud${NC} - Préparation pour déploiement cloud"
    echo "     • Configuration .env uniquement"
    echo "     • Instructions pour Railway/Render/Fly.io"
    echo ""

    while true; do
        read -rp "Votre choix [1-3]: " choice
        case "${choice}" in
            1) INSTALL_MODE="dev"; break ;;
            2) INSTALL_MODE="prod"; break ;;
            3) INSTALL_MODE="cloud"; break ;;
            *) echo "Choix invalide. Veuillez entrer 1, 2 ou 3." ;;
        esac
    done

    log INFO "Mode sélectionné: ${INSTALL_MODE}"
}

#===============================================================================
# EXÉCUTION DE L'INSTALLATION
#===============================================================================

run_installation() {
    log INFO "Démarrage de l'installation en mode ${INSTALL_MODE}..."

    # Phase 1: Vérifications système
    log INFO "━━━ Phase 1: Vérifications système ━━━"
    run_system_checks

    # Phase 2: Dépendances système
    log INFO "━━━ Phase 2: Dépendances système ━━━"
    install_system_deps

    # Phase 3: Python et environnement virtuel
    log INFO "━━━ Phase 3: Python et environnement virtuel ━━━"
    setup_python

    # Phase 4: PostgreSQL
    if [[ "${INSTALL_MODE}" != "cloud" ]]; then
        log INFO "━━━ Phase 4: PostgreSQL ━━━"
        setup_postgres
    fi

    # Phase 5: Génération des secrets
    log INFO "━━━ Phase 5: Génération des secrets ━━━"
    generate_secrets

    # Phase 6: Configuration .env
    log INFO "━━━ Phase 6: Configuration environnement ━━━"
    generate_env_file

    # Phase 7: Installation AZALSCORE
    log INFO "━━━ Phase 7: Installation AZALSCORE ━━━"
    install_azalscore

    # Phase 8: Configuration production (si applicable)
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        log INFO "━━━ Phase 8: Configuration production ━━━"

        if [[ "${OS_TYPE}" == "linux" ]]; then
            setup_systemd
            setup_firewall
        fi
    fi

    # Phase 9: Résumé final
    log INFO "━━━ Phase 9: Résumé final ━━━"
    print_summary
}

#===============================================================================
# POINT D'ENTRÉE PRINCIPAL
#===============================================================================

main() {
    # Créer le fichier de log
    mkdir -p "$(dirname "${LOG_FILE}")"
    : > "${LOG_FILE}"

    # Afficher la bannière
    print_banner

    # Parser les arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dev)
                INSTALL_MODE="dev"
                shift
                ;;
            --prod)
                INSTALL_MODE="prod"
                shift
                ;;
            --cloud)
                INSTALL_MODE="cloud"
                shift
                ;;
            --non-interactive)
                INTERACTIVE=false
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                print_help
                exit 0
                ;;
            *)
                log ERROR "Option inconnue: $1"
                print_help
                exit 1
                ;;
        esac
    done

    # Détection du système
    detect_os

    # Vérifications préliminaires
    check_internet
    check_disk_space
    check_ports

    # Charger les modules
    load_modules

    # Sélection du mode (si non spécifié)
    if [[ "${INTERACTIVE}" == "true" ]] && [[ -z "${INSTALL_MODE}" ]]; then
        select_install_mode
    fi

    # Défaut: mode dev
    INSTALL_MODE="${INSTALL_MODE:-dev}"

    # Vérification des droits
    check_root

    # Exécuter l'installation
    run_installation

    log OK "Installation terminée avec succès!"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}   AZALSCORE a été installé avec succès!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Exécution
main "$@"
