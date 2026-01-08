#!/bin/bash
#
# Azalscore - Script d'installation universel
# Compatible: macOS, Linux (Debian/Ubuntu, RHEL/CentOS/Fedora, Arch), Windows (via WSL ou Git Bash)
#

set -e

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

REPO_URL="https://github.com/MASITH-developpement/Azalscore.git"
BRANCH="main"
INSTALL_DIR="$HOME/Azalscore"

# ═══════════════════════════════════════════════════════════════
# COULEURS ET AFFICHAGE
# ═══════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logo Azalscore
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
    echo "║              Installation Universelle                         ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# ═══════════════════════════════════════════════════════════════
# DÉTECTION DU SYSTÈME
# ═══════════════════════════════════════════════════════════════

detect_os() {
    OS_TYPE=""
    OS_NAME=""
    OS_VERSION=""
    OS_ARCH=""
    PKG_MANAGER=""

    # Détecter l'architecture
    OS_ARCH=$(uname -m)
    case "$OS_ARCH" in
        x86_64|amd64) OS_ARCH="amd64" ;;
        arm64|aarch64) OS_ARCH="arm64" ;;
        armv7l) OS_ARCH="armv7" ;;
        i686|i386) OS_ARCH="386" ;;
    esac

    # Détecter le système d'exploitation
    case "$(uname -s)" in
        Darwin)
            OS_TYPE="macos"
            OS_NAME="macOS"
            OS_VERSION=$(sw_vers -productVersion)

            # Déterminer le nom de la version macOS
            local major_version=$(echo "$OS_VERSION" | cut -d. -f1)
            case "$major_version" in
                14) OS_NAME="macOS Sonoma" ;;
                13) OS_NAME="macOS Ventura" ;;
                12) OS_NAME="macOS Monterey" ;;
                11) OS_NAME="macOS Big Sur" ;;
                10)
                    local minor=$(echo "$OS_VERSION" | cut -d. -f2)
                    case "$minor" in
                        15) OS_NAME="macOS Catalina" ;;
                        14) OS_NAME="macOS Mojave" ;;
                        13) OS_NAME="macOS High Sierra" ;;
                        *) OS_NAME="macOS" ;;
                    esac
                    ;;
            esac
            ;;
        Linux)
            OS_TYPE="linux"
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                OS_NAME="$NAME"
                OS_VERSION="$VERSION_ID"

                # Détecter le gestionnaire de paquets
                if command -v apt-get &> /dev/null; then
                    PKG_MANAGER="apt"
                elif command -v dnf &> /dev/null; then
                    PKG_MANAGER="dnf"
                elif command -v yum &> /dev/null; then
                    PKG_MANAGER="yum"
                elif command -v pacman &> /dev/null; then
                    PKG_MANAGER="pacman"
                elif command -v zypper &> /dev/null; then
                    PKG_MANAGER="zypper"
                elif command -v apk &> /dev/null; then
                    PKG_MANAGER="apk"
                fi
            elif [ -f /etc/redhat-release ]; then
                OS_NAME="Red Hat / CentOS"
                PKG_MANAGER="yum"
            elif [ -f /etc/debian_version ]; then
                OS_NAME="Debian"
                PKG_MANAGER="apt"
            else
                OS_NAME="Linux (inconnu)"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_TYPE="windows"
            OS_NAME="Windows (Git Bash/MSYS2)"
            OS_VERSION=$(cmd.exe /c ver 2>/dev/null | grep -oP '\d+\.\d+' | head -1 || echo "unknown")
            ;;
        *)
            OS_TYPE="unknown"
            OS_NAME="Système inconnu"
            ;;
    esac
}

show_system_info() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                 DIAGNOSTIC SYSTÈME                            ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${MAGENTA}Système d'exploitation:${NC}"
    echo -e "  Type:         ${GREEN}$OS_TYPE${NC}"
    echo -e "  Nom:          ${GREEN}$OS_NAME${NC}"
    echo -e "  Version:      ${GREEN}$OS_VERSION${NC}"
    echo -e "  Architecture: ${GREEN}$OS_ARCH${NC}"

    if [ -n "$PKG_MANAGER" ]; then
        echo -e "  Gestionnaire: ${GREEN}$PKG_MANAGER${NC}"
    fi

    echo ""
    echo -e "${MAGENTA}Ressources système:${NC}"

    # RAM
    if [ "$OS_TYPE" = "macos" ]; then
        local ram_bytes=$(sysctl -n hw.memsize 2>/dev/null)
        local ram_gb=$((ram_bytes / 1073741824))
        echo -e "  RAM:          ${GREEN}${ram_gb} GB${NC}"

        # CPU
        local cpu_brand=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "N/A")
        echo -e "  CPU:          ${GREEN}$cpu_brand${NC}"

        # Disque
        local disk_free=$(df -h / | awk 'NR==2 {print $4}')
        echo -e "  Disque libre: ${GREEN}$disk_free${NC}"

    elif [ "$OS_TYPE" = "linux" ]; then
        local ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        local ram_gb=$((ram_kb / 1048576))
        echo -e "  RAM:          ${GREEN}${ram_gb} GB${NC}"

        # CPU
        local cpu_model=$(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
        echo -e "  CPU:          ${GREEN}$cpu_model${NC}"

        # Disque
        local disk_free=$(df -h / | awk 'NR==2 {print $4}')
        echo -e "  Disque libre: ${GREEN}$disk_free${NC}"
    fi

    echo ""
}

# ═══════════════════════════════════════════════════════════════
# VÉRIFICATION DES COMMANDES
# ═══════════════════════════════════════════════════════════════

check_command() {
    command -v "$1" &> /dev/null
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION - MACOS
# ═══════════════════════════════════════════════════════════════

install_macos_prerequisites() {
    log_info "Installation des prérequis pour macOS..."

    # Xcode Command Line Tools
    if xcode-select -p &> /dev/null; then
        log_success "Xcode Command Line Tools installés"
    else
        log_info "Installation de Xcode Command Line Tools..."
        xcode-select --install
        log_warning "Suivez les instructions à l'écran, puis appuyez sur Entrée"
        read -r
    fi

    # Homebrew
    if check_command brew; then
        log_success "Homebrew installé"
    else
        log_info "Installation de Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        if [[ "$OS_ARCH" == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        log_success "Homebrew installé"
    fi

    # Git
    if check_command git; then
        log_success "Git installé ($(git --version | awk '{print $3}'))"
    else
        log_info "Installation de Git..."
        brew install git
        log_success "Git installé"
    fi

    # Docker
    install_docker_macos

    # Node.js
    if check_command node; then
        log_success "Node.js installé ($(node -v))"
    else
        log_info "Installation de Node.js..."
        brew install node@20
        brew link node@20 2>/dev/null || true
        log_success "Node.js installé"
    fi
}

install_docker_macos() {
    if check_command docker; then
        log_success "Docker installé ($(docker --version | awk '{print $3}' | tr -d ','))"
        return 0
    fi

    log_info "Installation de Docker Desktop pour macOS..."

    local DOCKER_DMG="/tmp/Docker.dmg"
    local DOCKER_URL=""

    if [[ "$OS_ARCH" == "arm64" ]]; then
        log_info "Téléchargement pour Apple Silicon (M1/M2/M3)..."
        DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
    else
        log_info "Téléchargement pour Intel..."
        DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
    fi

    if curl -L -o "$DOCKER_DMG" "$DOCKER_URL" --progress-bar; then
        log_success "Téléchargement terminé"
    else
        log_error "Erreur lors du téléchargement"
        log_warning "Téléchargez manuellement: https://www.docker.com/products/docker-desktop/"
        return 1
    fi

    log_info "Installation de Docker Desktop..."
    local MOUNT_POINT=$(hdiutil attach "$DOCKER_DMG" -nobrowse 2>/dev/null | grep -o '/Volumes/Docker.*')

    if [ -z "$MOUNT_POINT" ]; then
        log_error "Erreur lors du montage du DMG"
        rm -f "$DOCKER_DMG"
        return 1
    fi

    [ -d "/Applications/Docker.app" ] && rm -rf "/Applications/Docker.app"
    cp -R "$MOUNT_POINT/Docker.app" /Applications/

    hdiutil detach "$MOUNT_POINT" -quiet
    rm -f "$DOCKER_DMG"

    log_success "Docker Desktop installé"

    log_info "Lancement de Docker Desktop..."
    open -a Docker

    log_warning "Acceptez les conditions d'utilisation si demandé"
    log_info "Attente du démarrage (90s max)..."

    local counter=0
    while ! docker info &> /dev/null && [ $counter -lt 90 ]; do
        sleep 3
        counter=$((counter + 3))
        echo -n "."
    done
    echo ""

    if docker info &> /dev/null; then
        log_success "Docker est prêt!"
    else
        log_warning "Docker n'est pas encore prêt. Configurez-le manuellement."
    fi
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION - LINUX
# ═══════════════════════════════════════════════════════════════

install_linux_prerequisites() {
    log_info "Installation des prérequis pour Linux ($OS_NAME)..."

    # Mise à jour des paquets
    case "$PKG_MANAGER" in
        apt)
            log_info "Mise à jour des paquets (apt)..."
            sudo apt-get update -y
            ;;
        dnf)
            log_info "Mise à jour des paquets (dnf)..."
            sudo dnf check-update -y || true
            ;;
        yum)
            log_info "Mise à jour des paquets (yum)..."
            sudo yum check-update -y || true
            ;;
        pacman)
            log_info "Mise à jour des paquets (pacman)..."
            sudo pacman -Sy --noconfirm
            ;;
        zypper)
            log_info "Mise à jour des paquets (zypper)..."
            sudo zypper refresh
            ;;
        apk)
            log_info "Mise à jour des paquets (apk)..."
            sudo apk update
            ;;
    esac

    # Git
    if check_command git; then
        log_success "Git installé ($(git --version | awk '{print $3}'))"
    else
        log_info "Installation de Git..."
        install_package git
        log_success "Git installé"
    fi

    # curl
    if check_command curl; then
        log_success "curl installé"
    else
        log_info "Installation de curl..."
        install_package curl
        log_success "curl installé"
    fi

    # Docker
    install_docker_linux

    # Node.js
    if check_command node; then
        log_success "Node.js installé ($(node -v))"
    else
        install_nodejs_linux
    fi
}

install_package() {
    local package="$1"
    case "$PKG_MANAGER" in
        apt) sudo apt-get install -y "$package" ;;
        dnf) sudo dnf install -y "$package" ;;
        yum) sudo yum install -y "$package" ;;
        pacman) sudo pacman -S --noconfirm "$package" ;;
        zypper) sudo zypper install -y "$package" ;;
        apk) sudo apk add "$package" ;;
        *) log_error "Gestionnaire de paquets non supporté"; return 1 ;;
    esac
}

install_docker_linux() {
    if check_command docker; then
        log_success "Docker installé ($(docker --version | awk '{print $3}' | tr -d ','))"
        return 0
    fi

    log_info "Installation de Docker pour Linux..."

    case "$PKG_MANAGER" in
        apt)
            # Installation officielle Docker pour Debian/Ubuntu
            log_info "Installation des dépendances..."
            sudo apt-get install -y ca-certificates curl gnupg lsb-release

            log_info "Ajout de la clé GPG Docker..."
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg

            log_info "Ajout du dépôt Docker..."
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
              $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
              sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

            sudo apt-get update -y
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;

        dnf|yum)
            # Installation pour Fedora/RHEL/CentOS
            log_info "Installation des dépendances..."
            sudo $PKG_MANAGER install -y yum-utils

            log_info "Ajout du dépôt Docker..."
            sudo $PKG_MANAGER-config-manager --add-repo https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/docker-ce.repo

            sudo $PKG_MANAGER install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;

        pacman)
            # Installation pour Arch Linux
            sudo pacman -S --noconfirm docker docker-compose
            ;;

        zypper)
            # Installation pour openSUSE
            sudo zypper install -y docker docker-compose
            ;;

        apk)
            # Installation pour Alpine
            sudo apk add docker docker-compose
            ;;

        *)
            log_error "Installation Docker non supportée pour ce système"
            log_warning "Installez Docker manuellement: https://docs.docker.com/engine/install/"
            return 1
            ;;
    esac

    # Démarrer et activer Docker
    log_info "Activation du service Docker..."
    sudo systemctl start docker 2>/dev/null || sudo service docker start 2>/dev/null || true
    sudo systemctl enable docker 2>/dev/null || true

    # Ajouter l'utilisateur au groupe docker
    log_info "Ajout de l'utilisateur au groupe docker..."
    sudo usermod -aG docker "$USER" 2>/dev/null || true

    log_success "Docker installé"
    log_warning "Vous devrez peut-être vous déconnecter/reconnecter pour utiliser Docker sans sudo"
}

install_nodejs_linux() {
    log_info "Installation de Node.js..."

    case "$PKG_MANAGER" in
        apt)
            # NodeSource pour Debian/Ubuntu
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        dnf)
            # NodeSource pour Fedora
            curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
            sudo dnf install -y nodejs
            ;;
        yum)
            # NodeSource pour RHEL/CentOS
            curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
            sudo yum install -y nodejs
            ;;
        pacman)
            sudo pacman -S --noconfirm nodejs npm
            ;;
        zypper)
            sudo zypper install -y nodejs20 npm20
            ;;
        apk)
            sudo apk add nodejs npm
            ;;
        *)
            log_warning "Installation Node.js via nvm..."
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            nvm install 20
            ;;
    esac

    log_success "Node.js installé"
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION - WINDOWS
# ═══════════════════════════════════════════════════════════════

install_windows_prerequisites() {
    log_info "Installation des prérequis pour Windows..."

    # Vérifier si on est dans WSL ou Git Bash
    if grep -qi microsoft /proc/version 2>/dev/null; then
        log_info "Environnement WSL détecté"
        install_linux_prerequisites
        return
    fi

    # Git Bash / MSYS2
    log_warning "Pour Windows natif, veuillez installer manuellement:"
    echo ""
    echo "  1. Docker Desktop: https://www.docker.com/products/docker-desktop/"
    echo "  2. Git: https://git-scm.com/download/win"
    echo "  3. Node.js: https://nodejs.org/"
    echo ""
    echo "  Ou utilisez WSL2 (recommandé):"
    echo "  wsl --install"
    echo ""

    # Vérifier ce qui est déjà installé
    if check_command git; then
        log_success "Git installé"
    else
        log_warning "Git non trouvé"
    fi

    if check_command docker; then
        log_success "Docker installé"
    else
        log_warning "Docker non trouvé"
    fi

    if check_command node; then
        log_success "Node.js installé"
    else
        log_warning "Node.js non trouvé"
    fi
}

# ═══════════════════════════════════════════════════════════════
# VÉRIFICATION FINALE
# ═══════════════════════════════════════════════════════════════

verify_installation() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}              VÉRIFICATION DE L'INSTALLATION                   ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    local all_ok=true

    # Git
    if check_command git; then
        log_success "Git: $(git --version | awk '{print $3}')"
    else
        log_error "Git: non installé"
        all_ok=false
    fi

    # Docker
    if check_command docker; then
        log_success "Docker: $(docker --version | awk '{print $3}' | tr -d ',')"
    else
        log_error "Docker: non installé"
        all_ok=false
    fi

    # Docker Compose
    if docker compose version &> /dev/null; then
        log_success "Docker Compose: $(docker compose version --short 2>/dev/null || echo 'v2')"
    elif check_command docker-compose; then
        log_success "Docker Compose: $(docker-compose --version | awk '{print $3}' | tr -d ',')"
    else
        log_error "Docker Compose: non disponible"
        all_ok=false
    fi

    # Node.js
    if check_command node; then
        log_success "Node.js: $(node -v)"
    else
        log_warning "Node.js: non installé (optionnel)"
    fi

    # npm
    if check_command npm; then
        log_success "npm: $(npm -v)"
    else
        log_warning "npm: non installé (optionnel)"
    fi

    echo ""

    if $all_ok; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}       ✓ Tous les prérequis sont installés!                    ${NC}"
        echo -e "${GREEN}                                                               ${NC}"
        echo -e "${GREEN}  Lancez Azalscore avec: ./azalscore-launcher.sh               ${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        return 0
    else
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ✗ Certains prérequis sont manquants.                         ${NC}"
        echo -e "${RED}    Veuillez les installer manuellement.                       ${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════

main() {
    show_logo

    # Détection du système
    detect_os
    show_system_info

    # Vérifier la compatibilité
    if [ "$OS_TYPE" = "unknown" ]; then
        log_error "Système d'exploitation non reconnu"
        exit 1
    fi

    echo -e "${BLUE}Cette installation va configurer:${NC}"
    echo "  • Git (contrôle de version)"
    echo "  • Docker & Docker Compose (conteneurisation)"
    echo "  • Node.js (optionnel, pour le développement)"
    echo ""
    echo -e "${YELLOW}Voulez-vous continuer? (o/n)${NC}"
    read -r response

    if [[ ! "$response" =~ ^[OoYy]$ ]]; then
        echo "Installation annulée."
        exit 0
    fi

    echo ""

    # Installation selon le système
    case "$OS_TYPE" in
        macos)
            install_macos_prerequisites
            ;;
        linux)
            install_linux_prerequisites
            ;;
        windows)
            install_windows_prerequisites
            ;;
    esac

    # Vérification finale
    verify_installation
}

# Exécuter
main "$@"
