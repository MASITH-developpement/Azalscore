#!/bin/bash
#
# Azalscore - Installation pour Debian/Ubuntu
# Compatible: Debian 10+, Ubuntu 20.04+
#
# Usage: curl -fsSL https://raw.githubusercontent.com/MASITH-developpement/Azalscore/main/launcher/debian/install-debian.sh | bash
#    ou: ./install-debian.sh
#

set -e

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

REPO_URL="https://github.com/MASITH-developpement/Azalscore.git"
BRANCH="main"
INSTALL_DIR="$HOME/Azalscore"
LOG_FILE="/tmp/azalscore-install.log"

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

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

log() { echo -e "$1" | tee -a "$LOG_FILE"; }
log_info() { log "${BLUE}[INFO]${NC} $1"; }
log_success() { log "${GREEN}[OK]${NC} $1"; }
log_warning() { log "${YELLOW}[!]${NC} $1"; }
log_error() { log "${RED}[ERREUR]${NC} $1"; }
log_step() { log "${MAGENTA}>>> $1${NC}"; }

check_command() { command -v "$1" &> /dev/null; }

show_logo() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     █████╗ ███████╗ █████╗ ██╗     ███████╗ ██████╗ ██████╗   ║
║    ██╔══██╗╚══███╔╝██╔══██╗██║     ██╔════╝██╔════╝██╔═══██╗  ║
║    ███████║  ███╔╝ ███████║██║     ███████╗██║     ██║   ██║  ║
║    ██╔══██║ ███╔╝  ██╔══██║██║     ╚════██║██║     ██║   ██║  ║
║    ██║  ██║███████╗██║  ██║███████╗███████║╚██████╗╚██████╔╝  ║
║    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═════╝   ║
║                                                               ║
║              Installation Debian/Ubuntu                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# ═══════════════════════════════════════════════════════════════
# DETECTION DU SYSTEME
# ═══════════════════════════════════════════════════════════════

detect_system() {
    log_step "Detection du systeme"

    if [ ! -f /etc/os-release ]; then
        log_error "Fichier /etc/os-release non trouve. Systeme non supporte."
        exit 1
    fi

    . /etc/os-release

    OS_ID="$ID"
    OS_NAME="$NAME"
    OS_VERSION="$VERSION_ID"
    OS_CODENAME="${VERSION_CODENAME:-$(lsb_release -cs 2>/dev/null || echo 'unknown')}"
    OS_ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)

    case "$OS_ID" in
        debian|ubuntu|linuxmint|pop|elementary|zorin)
            log_success "Systeme compatible detecte: $OS_NAME $OS_VERSION ($OS_CODENAME)"
            ;;
        *)
            log_warning "Systeme non officiellement supporte: $OS_NAME"
            log_warning "L'installation va tenter de continuer..."
            ;;
    esac

    # Afficher les ressources
    echo ""
    log_info "Architecture: $OS_ARCH"
    log_info "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
    log_info "Disque libre: $(df -h / | awk 'NR==2 {print $4}')"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# VERIFICATION DES PRIVILEGES
# ═══════════════════════════════════════════════════════════════

check_privileges() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "Ce script ne doit pas etre execute en tant que root."
        log_warning "Il utilisera sudo pour les operations necessitant des privileges."
        log_warning ""
        log_warning "Executez: ./install-debian.sh (sans sudo)"
        exit 1
    fi

    # Verifier que sudo fonctionne
    if ! sudo -v 2>/dev/null; then
        log_error "sudo n'est pas configure pour cet utilisateur."
        log_error "Ajoutez votre utilisateur au groupe sudo:"
        log_error "  su - root"
        log_error "  usermod -aG sudo $USER"
        log_error "  exit"
        log_error "Puis reconnectez-vous."
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# MISE A JOUR DU SYSTEME
# ═══════════════════════════════════════════════════════════════

update_system() {
    log_step "Mise a jour des paquets"

    sudo apt-get update -y
    log_success "Liste des paquets mise a jour"
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION DES PREREQUIS DE BASE
# ═══════════════════════════════════════════════════════════════

install_base_packages() {
    log_step "Installation des paquets de base"

    local packages=(
        apt-transport-https
        ca-certificates
        curl
        gnupg
        lsb-release
        software-properties-common
        wget
        git
    )

    sudo apt-get install -y "${packages[@]}"
    log_success "Paquets de base installes"
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION DE GIT
# ═══════════════════════════════════════════════════════════════

install_git() {
    log_step "Verification de Git"

    if check_command git; then
        log_success "Git deja installe: $(git --version | awk '{print $3}')"
    else
        log_info "Installation de Git..."
        sudo apt-get install -y git
        log_success "Git installe: $(git --version | awk '{print $3}')"
    fi
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION DE DOCKER
# ═══════════════════════════════════════════════════════════════

install_docker() {
    log_step "Installation de Docker"

    if check_command docker; then
        log_success "Docker deja installe: $(docker --version | awk '{print $3}' | tr -d ',')"

        # Verifier si Docker fonctionne
        if docker info &> /dev/null; then
            log_success "Docker fonctionne correctement"
        else
            log_warning "Docker installe mais non fonctionnel"
            configure_docker_user
        fi
        return 0
    fi

    log_info "Suppression des anciennes versions de Docker..."
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    log_info "Ajout de la cle GPG officielle Docker..."
    sudo install -m 0755 -d /etc/apt/keyrings

    # Determiner la distribution (debian ou ubuntu)
    local distro="$OS_ID"
    if [ "$distro" != "debian" ] && [ "$distro" != "ubuntu" ]; then
        # Pour les derivees, utiliser la base
        if [ -n "$ID_LIKE" ]; then
            if echo "$ID_LIKE" | grep -q "ubuntu"; then
                distro="ubuntu"
            elif echo "$ID_LIKE" | grep -q "debian"; then
                distro="debian"
            fi
        fi
    fi

    curl -fsSL "https://download.docker.com/linux/$distro/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    log_info "Ajout du depot Docker..."
    echo \
        "deb [arch=$OS_ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$distro \
        $OS_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    log_info "Installation des paquets Docker..."
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    log_success "Docker installe: $(docker --version | awk '{print $3}' | tr -d ',')"

    configure_docker_user
}

configure_docker_user() {
    log_info "Configuration des permissions Docker..."

    # Ajouter l'utilisateur au groupe docker
    if ! groups "$USER" | grep -q docker; then
        sudo usermod -aG docker "$USER"
        log_success "Utilisateur $USER ajoute au groupe docker"
    fi

    # Demarrer et activer Docker
    sudo systemctl start docker 2>/dev/null || true
    sudo systemctl enable docker 2>/dev/null || true

    log_success "Service Docker configure"

    # Note importante
    echo ""
    log_warning "═══════════════════════════════════════════════════════════════"
    log_warning "IMPORTANT: Pour utiliser Docker sans sudo, vous devez:"
    log_warning "  1. Vous deconnecter et vous reconnecter"
    log_warning "  OU"
    log_warning "  2. Executer: newgrp docker"
    log_warning "═══════════════════════════════════════════════════════════════"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION DE NODE.JS
# ═══════════════════════════════════════════════════════════════

install_nodejs() {
    log_step "Installation de Node.js"

    if check_command node; then
        local node_version=$(node -v | tr -d 'v')
        local major_version=$(echo "$node_version" | cut -d. -f1)

        if [ "$major_version" -ge 18 ]; then
            log_success "Node.js deja installe: v$node_version"
            return 0
        else
            log_warning "Node.js $node_version detecte. Version 18+ recommandee."
        fi
    fi

    log_info "Installation de Node.js 20 LTS via NodeSource..."

    # Installer via NodeSource
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs

    log_success "Node.js installe: $(node -v)"
    log_success "npm installe: $(npm -v)"
}

# ═══════════════════════════════════════════════════════════════
# CLONAGE DU DEPOT
# ═══════════════════════════════════════════════════════════════

clone_repository() {
    log_step "Installation du depot Azalscore"

    if [ -d "$INSTALL_DIR/.git" ]; then
        log_info "Depot existant, mise a jour..."
        cd "$INSTALL_DIR"

        # Sauvegarder les modifications locales
        if ! git diff --quiet 2>/dev/null; then
            git stash push -m "Sauvegarde $(date '+%Y-%m-%d %H:%M')" || true
        fi

        git fetch origin "$BRANCH"
        git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" origin/"$BRANCH"
        git pull origin "$BRANCH"

        log_success "Depot mis a jour"
    else
        log_info "Clonage du depot..."

        [ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
        git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"

        log_success "Depot clone dans $INSTALL_DIR"
    fi
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION DE L'ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════════

setup_environment() {
    log_step "Configuration de l'environnement"

    cd "$INSTALL_DIR"

    if [ -f ".env" ]; then
        log_success "Fichier .env existant conserve"
        return 0
    fi

    if [ ! -f ".env.example" ]; then
        log_error "Fichier .env.example non trouve"
        return 1
    fi

    log_info "Creation du fichier .env..."
    cp .env.example .env

    # Generer des cles securisees
    local SECRET_KEY=$(openssl rand -hex 32)
    local BOOTSTRAP_SECRET=$(openssl rand -hex 32)
    local ENCRYPTION_KEY=$(openssl rand -hex 32)
    local DB_PASSWORD=$(openssl rand -hex 16)

    # Remplacer les valeurs par defaut
    sed -i "s/CHANGEME_PASSWORD/$DB_PASSWORD/g" .env
    sed -i "s/CHANGEME_SECRET_KEY/$SECRET_KEY/g" .env
    sed -i "s/CHANGEME_BOOTSTRAP_SECRET/$BOOTSTRAP_SECRET/g" .env
    sed -i "s/CHANGEME_ENCRYPTION_KEY/$ENCRYPTION_KEY/g" .env

    # Configurer pour le developpement local
    sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=development/g" .env

    log_success "Fichier .env configure avec des cles securisees"
}

# ═══════════════════════════════════════════════════════════════
# CREATION DES RACCOURCIS
# ═══════════════════════════════════════════════════════════════

create_shortcuts() {
    log_step "Creation des raccourcis"

    # Creer un lien symbolique vers le launcher
    local LAUNCHER="$INSTALL_DIR/launcher/azalscore.sh"

    if [ -f "$LAUNCHER" ]; then
        chmod +x "$LAUNCHER"
        chmod +x "$INSTALL_DIR/launcher/install.sh" 2>/dev/null || true
        chmod +x "$INSTALL_DIR/launcher/debian/install-debian.sh" 2>/dev/null || true

        # Creer un alias dans le profil
        local PROFILE="$HOME/.bashrc"
        if [ -f "$HOME/.zshrc" ]; then
            PROFILE="$HOME/.zshrc"
        fi

        if ! grep -q "alias azalscore=" "$PROFILE" 2>/dev/null; then
            echo "" >> "$PROFILE"
            echo "# Azalscore" >> "$PROFILE"
            echo "alias azalscore='$LAUNCHER'" >> "$PROFILE"
            log_success "Alias 'azalscore' ajoute a $PROFILE"
        fi

        # Creer un lien dans /usr/local/bin si possible
        if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ] || sudo test -w "/usr/local/bin"; then
            sudo ln -sf "$LAUNCHER" /usr/local/bin/azalscore 2>/dev/null || true
            log_success "Commande 'azalscore' disponible globalement"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════
# VERIFICATION FINALE
# ═══════════════════════════════════════════════════════════════

verify_installation() {
    echo ""
    log_step "Verification de l'installation"
    echo ""

    local errors=0

    # Git
    if check_command git; then
        log_success "Git: $(git --version | awk '{print $3}')"
    else
        log_error "Git: non installe"
        ((errors++))
    fi

    # Docker
    if check_command docker; then
        log_success "Docker: $(docker --version | awk '{print $3}' | tr -d ',')"
    else
        log_error "Docker: non installe"
        ((errors++))
    fi

    # Docker Compose
    if docker compose version &> /dev/null; then
        log_success "Docker Compose: $(docker compose version --short)"
    else
        log_error "Docker Compose: non disponible"
        ((errors++))
    fi

    # Node.js
    if check_command node; then
        log_success "Node.js: $(node -v)"
    else
        log_warning "Node.js: non installe (optionnel)"
    fi

    # Depot
    if [ -d "$INSTALL_DIR/.git" ]; then
        log_success "Azalscore: installe dans $INSTALL_DIR"
    else
        log_error "Azalscore: depot non clone"
        ((errors++))
    fi

    # Fichier .env
    if [ -f "$INSTALL_DIR/.env" ]; then
        log_success "Configuration: .env present"
    else
        log_warning "Configuration: .env manquant"
    fi

    echo ""

    return $errors
}

# ═══════════════════════════════════════════════════════════════
# AFFICHAGE DES INSTRUCTIONS FINALES
# ═══════════════════════════════════════════════════════════════

show_success() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}            INSTALLATION TERMINEE AVEC SUCCES!                 ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Pour demarrer Azalscore:${NC}"
    echo ""
    echo -e "  ${YELLOW}1. Reconnectez-vous ou executez:${NC}"
    echo -e "     ${GREEN}newgrp docker${NC}"
    echo ""
    echo -e "  ${YELLOW}2. Puis lancez:${NC}"
    echo -e "     ${GREEN}cd $INSTALL_DIR && ./launcher/azalscore.sh start${NC}"
    echo ""
    echo -e "  ${YELLOW}Ou apres reconnexion:${NC}"
    echo -e "     ${GREEN}azalscore start${NC}"
    echo ""
    echo -e "${CYAN}Commandes disponibles:${NC}"
    echo -e "  ${BLUE}azalscore start${NC}     - Demarrer l'application"
    echo -e "  ${BLUE}azalscore stop${NC}      - Arreter l'application"
    echo -e "  ${BLUE}azalscore restart${NC}   - Redemarrer"
    echo -e "  ${BLUE}azalscore logs${NC}      - Afficher les logs"
    echo -e "  ${BLUE}azalscore status${NC}    - Etat des conteneurs"
    echo -e "  ${BLUE}azalscore diagnose${NC}  - Diagnostic du systeme"
    echo ""
    echo -e "${CYAN}URLs (apres demarrage):${NC}"
    echo -e "  ${BLUE}API Backend:${NC}     http://localhost:8000"
    echo -e "  ${BLUE}Documentation:${NC}   http://localhost:8000/docs"
    echo -e "  ${BLUE}Frontend:${NC}        http://localhost:3000"
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
}

show_failure() {
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}     INSTALLATION INCOMPLETE - Verifiez les erreurs ci-dessus   ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Log disponible: $LOG_FILE"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════

main() {
    # Initialiser le log
    echo "=== Installation Azalscore - $(date) ===" > "$LOG_FILE"

    show_logo

    detect_system
    check_privileges

    echo ""
    echo -e "${BLUE}Cette installation va configurer:${NC}"
    echo "  - Git (controle de version)"
    echo "  - Docker & Docker Compose (conteneurisation)"
    echo "  - Node.js 20 LTS (developpement frontend)"
    echo "  - Depot Azalscore"
    echo ""

    read -p "Voulez-vous continuer? (o/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
        echo "Installation annulee."
        exit 0
    fi

    echo ""

    # Etapes d'installation
    update_system
    install_base_packages
    install_git
    install_docker
    install_nodejs
    clone_repository
    setup_environment
    create_shortcuts

    # Verification
    if verify_installation; then
        show_success
    else
        show_failure
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════

main "$@"
