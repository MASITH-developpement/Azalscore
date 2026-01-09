#!/bin/bash
#
# Azalscore - Launcher Universel
# Compatible: macOS, Linux, Windows (WSL/Git Bash)
#
# Ce script:
# 1. Détecte automatiquement le système d'exploitation
# 2. Vérifie et installe les prérequis si nécessaire
# 3. Clone ou met à jour le dépôt depuis GitHub (branche main)
# 4. Lance l'application Azalscore
#

set -e

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

REPO_URL="https://github.com/MASITH-developpement/Azalscore.git"
BRANCH="main"
INSTALL_DIR="$HOME/Azalscore"
LOG_DIR="$HOME/.azalscore"
LOG_FILE="$LOG_DIR/launcher.log"

# ═══════════════════════════════════════════════════════════════
# COULEURS
# ═══════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Créer le dossier de logs
mkdir -p "$LOG_DIR"

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$message" | tee -a "$LOG_FILE"
}

log_info() { log "${BLUE}[INFO]${NC} $1"; }
log_success() { log "${GREEN}[✓]${NC} $1"; }
log_warning() { log "${YELLOW}[⚠]${NC} $1"; }
log_error() { log "${RED}[✗]${NC} $1"; }

check_command() {
    command -v "$1" &> /dev/null
}

# Logo
show_logo() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║     █████╗ ███████╗ █████╗ ██╗     ███████╗ ██████╗ ██████╗   ║"
    echo "║    ██╔══██╗╚══███╔╝██╔══██╗██║     ██╔════╝██╔════╝██╔═══██╗  ║"
    echo "║    ███████║  ███╔╝ ███████║██║     ███████╗██║     ██║   ██║  ║"
    echo "║    ██╔══██║ ███╔╝  ██╔══██║██║     ╚════██║██║     ██║   ██║  ║"
    echo "║    ██║  ██║███████╗██║  ██║███████╗███████║╚██████╗╚██████╔╝  ║"
    echo "║    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═════╝   ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ═══════════════════════════════════════════════════════════════
# DÉTECTION DU SYSTÈME
# ═══════════════════════════════════════════════════════════════

detect_system() {
    OS_TYPE=""
    OS_NAME=""
    OS_VERSION=""
    OS_ARCH=""

    # Architecture
    OS_ARCH=$(uname -m)
    case "$OS_ARCH" in
        x86_64|amd64) OS_ARCH="amd64" ;;
        arm64|aarch64) OS_ARCH="arm64" ;;
        armv7l) OS_ARCH="armv7" ;;
    esac

    # Système d'exploitation
    case "$(uname -s)" in
        Darwin)
            OS_TYPE="macos"
            OS_VERSION=$(sw_vers -productVersion)
            local major=$(echo "$OS_VERSION" | cut -d. -f1)
            case "$major" in
                15) OS_NAME="macOS Sequoia" ;;
                14) OS_NAME="macOS Sonoma" ;;
                13) OS_NAME="macOS Ventura" ;;
                12) OS_NAME="macOS Monterey" ;;
                11) OS_NAME="macOS Big Sur" ;;
                *) OS_NAME="macOS $OS_VERSION" ;;
            esac
            ;;
        Linux)
            OS_TYPE="linux"
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                OS_NAME="$NAME"
                OS_VERSION="$VERSION_ID"
            else
                OS_NAME="Linux"
            fi
            # WSL?
            if grep -qi microsoft /proc/version 2>/dev/null; then
                OS_NAME="$OS_NAME (WSL)"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_TYPE="windows"
            OS_NAME="Windows"
            ;;
    esac

    log_info "Système détecté: $OS_NAME ($OS_ARCH)"
}

# ═══════════════════════════════════════════════════════════════
# VÉRIFICATION DES PRÉREQUIS
# ═══════════════════════════════════════════════════════════════

check_prerequisites() {
    log_info "Vérification des prérequis..."
    local missing=()

    # Git
    if check_command git; then
        log_success "Git: $(git --version | awk '{print $3}')"
    else
        missing+=("git")
        log_error "Git: non installé"
    fi

    # Docker
    if check_command docker; then
        log_success "Docker: $(docker --version | awk '{print $3}' | tr -d ',')"

        # Docker en cours d'exécution?
        if docker info &> /dev/null; then
            log_success "Docker: en cours d'exécution"
        else
            log_warning "Docker: installé mais non démarré"
            start_docker
        fi
    else
        missing+=("docker")
        log_error "Docker: non installé"
    fi

    # Docker Compose
    if docker compose version &> /dev/null || check_command docker-compose; then
        log_success "Docker Compose: disponible"
    else
        missing+=("docker-compose")
        log_error "Docker Compose: non disponible"
    fi

    # Si prérequis manquants
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Prérequis manquants: ${missing[*]}"
        log_warning "Lancement de l'installation automatique..."

        # Lancer le script d'installation
        local SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        if [ -f "$SCRIPT_DIR/install.sh" ]; then
            bash "$SCRIPT_DIR/install.sh"
        elif [ -f "$INSTALL_DIR/launcher/install.sh" ]; then
            bash "$INSTALL_DIR/launcher/install.sh"
        else
            log_error "Script d'installation non trouvé"
            log_warning "Téléchargez-le: curl -fsSL https://raw.githubusercontent.com/MASITH-developpement/Azalscore/main/launcher/install.sh | bash"
            return 1
        fi

        # Revérifier
        check_prerequisites
    fi

    return 0
}

# ═══════════════════════════════════════════════════════════════
# DÉMARRAGE DE DOCKER
# ═══════════════════════════════════════════════════════════════

start_docker() {
    log_info "Tentative de démarrage de Docker..."

    case "$OS_TYPE" in
        macos)
            open -a Docker 2>/dev/null || true
            ;;
        linux)
            sudo systemctl start docker 2>/dev/null || \
            sudo service docker start 2>/dev/null || true
            ;;
    esac

    log_info "Attente du démarrage de Docker (60s max)..."
    local counter=0
    while ! docker info &> /dev/null && [ $counter -lt 60 ]; do
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    echo ""

    if docker info &> /dev/null; then
        log_success "Docker démarré"
    else
        log_error "Impossible de démarrer Docker. Veuillez le démarrer manuellement."
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# MISE À JOUR DU DÉPÔT
# ═══════════════════════════════════════════════════════════════

update_repository() {
    log_info "Mise à jour depuis GitHub (branche $BRANCH)..."

    if [ -d "$INSTALL_DIR/.git" ]; then
        log_info "Dépôt existant, mise à jour..."
        cd "$INSTALL_DIR"

        # Sauvegarder les modifications locales
        if ! git diff --quiet 2>/dev/null; then
            log_warning "Modifications locales détectées, sauvegarde..."
            git stash push -m "Sauvegarde auto $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
        fi

        # Mettre à jour
        git fetch origin "$BRANCH"
        git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" origin/"$BRANCH"
        git reset --hard origin/"$BRANCH"

        log_success "Dépôt mis à jour"
    else
        log_info "Premier lancement, clonage du dépôt..."

        [ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
        git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"

        log_success "Dépôt cloné"
    fi

    cd "$INSTALL_DIR"
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION DE L'ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════════

setup_environment() {
    log_info "Configuration de l'environnement..."
    cd "$INSTALL_DIR"

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_info "Création du fichier .env..."
            cp .env.example .env

            # Générer des clés sécurisées
            local SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p)
            local BOOTSTRAP_SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p)
            local DB_PASSWORD=$(openssl rand -hex 16 2>/dev/null || head -c 16 /dev/urandom | xxd -p)

            # Remplacer les valeurs (compatible macOS et Linux)
            if [[ "$OS_TYPE" == "macos" ]]; then
                sed -i '' "s/CHANGEME_PASSWORD/$DB_PASSWORD/g" .env 2>/dev/null || true
                sed -i '' "s/CHANGEME_SECRET_KEY/$SECRET_KEY/g" .env 2>/dev/null || true
                sed -i '' "s/CHANGEME_BOOTSTRAP_SECRET/$BOOTSTRAP_SECRET/g" .env 2>/dev/null || true
            else
                sed -i "s/CHANGEME_PASSWORD/$DB_PASSWORD/g" .env 2>/dev/null || true
                sed -i "s/CHANGEME_SECRET_KEY/$SECRET_KEY/g" .env 2>/dev/null || true
                sed -i "s/CHANGEME_BOOTSTRAP_SECRET/$BOOTSTRAP_SECRET/g" .env 2>/dev/null || true
            fi

            log_success "Fichier .env créé avec des clés sécurisées"
        else
            log_warning "Fichier .env.example non trouvé"
        fi
    else
        log_success "Fichier .env existant conservé"
    fi
}

# ═══════════════════════════════════════════════════════════════
# DÉMARRAGE DE L'APPLICATION
# ═══════════════════════════════════════════════════════════════

start_application() {
    log_info "Démarrage d'Azalscore..."
    cd "$INSTALL_DIR"

    # Arrêter les conteneurs existants
    log_info "Arrêt des conteneurs existants..."
    docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

    # Démarrer
    log_info "Construction et démarrage..."
    if docker compose up --build -d 2>/dev/null; then
        log_success "Conteneurs démarrés (docker compose)"
    elif docker-compose up --build -d 2>/dev/null; then
        log_success "Conteneurs démarrés (docker-compose)"
    else
        log_error "Erreur lors du démarrage"
        return 1
    fi

    # Attendre que l'API soit prête
    log_info "Attente de l'API (60s max)..."
    local counter=0
    while [ $counter -lt 60 ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API prête!"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    echo ""

    if [ $counter -ge 60 ]; then
        log_warning "L'API n'est pas encore prête. Vérifiez: docker compose logs -f"
    fi
}

stop_application() {
    log_info "Arrêt d'Azalscore..."
    cd "$INSTALL_DIR" 2>/dev/null || true
    docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
    log_success "Application arrêtée"
}

# ═══════════════════════════════════════════════════════════════
# AFFICHAGE DES INFORMATIONS
# ═══════════════════════════════════════════════════════════════

show_info() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}          Azalscore est en cours d'exécution!                  ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}URLs d'accès:${NC}"
    echo -e "  ${BLUE}API Backend:${NC}     http://localhost:8000"
    echo -e "  ${BLUE}Documentation:${NC}   http://localhost:8000/docs"
    echo -e "  ${BLUE}Health Check:${NC}    http://localhost:8000/health"
    echo ""
    echo -e "${CYAN}Commandes utiles:${NC}"
    echo -e "  ${BLUE}Logs:${NC}      cd $INSTALL_DIR && docker compose logs -f"
    echo -e "  ${BLUE}Arrêter:${NC}   $0 stop"
    echo -e "  ${BLUE}Restart:${NC}   $0 restart"
    echo -e "  ${BLUE}Status:${NC}    $0 status"
    echo ""
}

show_help() {
    echo ""
    echo "Usage: $0 [COMMANDE]"
    echo ""
    echo "Commandes:"
    echo "  start       Démarrer Azalscore (par défaut)"
    echo "  stop        Arrêter Azalscore"
    echo "  restart     Redémarrer Azalscore"
    echo "  update      Mettre à jour depuis GitHub"
    echo "  logs        Afficher les logs"
    echo "  status      État des conteneurs"
    echo "  install     Installer les prérequis"
    echo "  diagnose    Diagnostic du système"
    echo "  help        Afficher cette aide"
    echo ""
}

show_status() {
    cd "$INSTALL_DIR" 2>/dev/null || { log_error "Azalscore non installé"; return 1; }
    docker compose ps 2>/dev/null || docker-compose ps
}

show_logs() {
    cd "$INSTALL_DIR" 2>/dev/null || { log_error "Azalscore non installé"; return 1; }
    docker compose logs -f 2>/dev/null || docker-compose logs -f
}

diagnose() {
    show_logo
    detect_system

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                 DIAGNOSTIC SYSTÈME                            ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    echo -e "${MAGENTA}Système:${NC}"
    echo -e "  OS:           ${GREEN}$OS_NAME${NC}"
    echo -e "  Version:      ${GREEN}$OS_VERSION${NC}"
    echo -e "  Architecture: ${GREEN}$OS_ARCH${NC}"

    echo ""
    echo -e "${MAGENTA}Logiciels:${NC}"

    if check_command git; then
        echo -e "  Git:          ${GREEN}✓ $(git --version | awk '{print $3}')${NC}"
    else
        echo -e "  Git:          ${RED}✗ Non installé${NC}"
    fi

    if check_command docker; then
        echo -e "  Docker:       ${GREEN}✓ $(docker --version | awk '{print $3}' | tr -d ',')${NC}"
        if docker info &> /dev/null; then
            echo -e "  Docker:       ${GREEN}✓ En cours d'exécution${NC}"
        else
            echo -e "  Docker:       ${YELLOW}⚠ Installé mais arrêté${NC}"
        fi
    else
        echo -e "  Docker:       ${RED}✗ Non installé${NC}"
    fi

    if docker compose version &> /dev/null; then
        echo -e "  Compose:      ${GREEN}✓ $(docker compose version --short 2>/dev/null || echo 'v2')${NC}"
    elif check_command docker-compose; then
        echo -e "  Compose:      ${GREEN}✓ $(docker-compose --version | awk '{print $3}')${NC}"
    else
        echo -e "  Compose:      ${RED}✗ Non disponible${NC}"
    fi

    if check_command node; then
        echo -e "  Node.js:      ${GREEN}✓ $(node -v)${NC}"
    else
        echo -e "  Node.js:      ${YELLOW}⚠ Non installé (optionnel)${NC}"
    fi

    echo ""
    echo -e "${MAGENTA}Azalscore:${NC}"
    if [ -d "$INSTALL_DIR/.git" ]; then
        cd "$INSTALL_DIR"
        local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        local last_commit=$(git log -1 --format="%h %s" 2>/dev/null)
        echo -e "  Installé:     ${GREEN}✓ $INSTALL_DIR${NC}"
        echo -e "  Branche:      ${GREEN}$current_branch${NC}"
        echo -e "  Commit:       ${GREEN}$last_commit${NC}"
    else
        echo -e "  Installé:     ${YELLOW}⚠ Non installé${NC}"
    fi

    echo ""
}

# ═══════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════

main() {
    local action="${1:-start}"

    case "$action" in
        start)
            show_logo
            detect_system
            check_prerequisites || exit 1
            update_repository
            setup_environment
            start_application
            show_info
            ;;
        stop)
            stop_application
            ;;
        restart)
            stop_application
            sleep 2
            detect_system
            check_prerequisites || exit 1
            start_application
            show_info
            ;;
        update)
            detect_system
            check_prerequisites || exit 1
            update_repository
            log_success "Mise à jour terminée. Utilisez 'restart' pour appliquer."
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        install)
            local SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
            if [ -f "$SCRIPT_DIR/install.sh" ]; then
                bash "$SCRIPT_DIR/install.sh"
            else
                log_error "Script d'installation non trouvé"
            fi
            ;;
        diagnose|diag)
            diagnose
            ;;
        help|--help|-h)
            show_logo
            show_help
            ;;
        *)
            log_error "Commande inconnue: $action"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
