#!/bin/bash
#
# Installation des prérequis pour Azalscore sur macOS
#

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       Installation des prérequis pour Azalscore               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Vérifier si on est sur macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}Ce script est conçu pour macOS uniquement.${NC}"
    exit 1
fi

# Fonction pour vérifier si une commande existe
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Installer Homebrew si nécessaire
install_homebrew() {
    if check_command brew; then
        echo -e "${GREEN}✓ Homebrew est déjà installé${NC}"
    else
        echo -e "${BLUE}Installation de Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Ajouter Homebrew au PATH pour les Mac Apple Silicon
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi

        echo -e "${GREEN}✓ Homebrew installé${NC}"
    fi
}

# Installer Git
install_git() {
    if check_command git; then
        local version=$(git --version | awk '{print $3}')
        echo -e "${GREEN}✓ Git est déjà installé (version $version)${NC}"
    else
        echo -e "${BLUE}Installation de Git...${NC}"
        brew install git
        echo -e "${GREEN}✓ Git installé${NC}"
    fi
}

# Installer Docker Desktop (téléchargement direct depuis Docker.com)
install_docker() {
    if check_command docker; then
        local version=$(docker --version | awk '{print $3}' | tr -d ',')
        echo -e "${GREEN}✓ Docker est déjà installé (version $version)${NC}"
    else
        echo -e "${BLUE}Installation de Docker Desktop...${NC}"

        local DOCKER_DMG="/tmp/Docker.dmg"
        local DOCKER_URL=""

        # Déterminer l'architecture
        if [[ $(uname -m) == "arm64" ]]; then
            echo "Détection: Mac avec puce Apple Silicon (M1/M2/M3)"
            DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
        else
            echo "Détection: Mac avec puce Intel"
            DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        fi

        echo -e "${BLUE}Téléchargement de Docker Desktop...${NC}"
        echo "URL: $DOCKER_URL"

        # Télécharger Docker Desktop
        if curl -L -o "$DOCKER_DMG" "$DOCKER_URL" --progress-bar; then
            echo -e "${GREEN}✓ Téléchargement terminé${NC}"
        else
            echo -e "${RED}✗ Erreur lors du téléchargement de Docker${NC}"
            echo -e "${YELLOW}Veuillez télécharger manuellement depuis: https://www.docker.com/products/docker-desktop/${NC}"
            return 1
        fi

        # Monter le DMG
        echo -e "${BLUE}Installation de Docker Desktop...${NC}"
        local MOUNT_POINT=$(hdiutil attach "$DOCKER_DMG" -nobrowse | grep -o '/Volumes/Docker.*')

        if [ -z "$MOUNT_POINT" ]; then
            echo -e "${RED}✗ Erreur lors du montage du DMG${NC}"
            rm -f "$DOCKER_DMG"
            return 1
        fi

        # Copier l'application dans /Applications
        echo "Copie de Docker.app vers /Applications..."
        if [ -d "/Applications/Docker.app" ]; then
            echo "Suppression de l'ancienne version..."
            rm -rf "/Applications/Docker.app"
        fi

        cp -R "$MOUNT_POINT/Docker.app" /Applications/

        # Démonter le DMG
        hdiutil detach "$MOUNT_POINT" -quiet
        rm -f "$DOCKER_DMG"

        echo -e "${GREEN}✓ Docker Desktop installé${NC}"

        # Lancer Docker Desktop
        echo -e "${BLUE}Lancement de Docker Desktop...${NC}"
        open -a Docker

        echo -e "${YELLOW}⚠ Docker Desktop démarre. Veuillez accepter les conditions d'utilisation si demandé.${NC}"
        echo -e "${YELLOW}Attente du démarrage de Docker (90 secondes max)...${NC}"

        local counter=0
        while ! docker info &> /dev/null && [ $counter -lt 90 ]; do
            sleep 3
            counter=$((counter + 3))
            echo -n "."
        done
        echo ""

        if docker info &> /dev/null; then
            echo -e "${GREEN}✓ Docker est prêt!${NC}"
        else
            echo -e "${YELLOW}⚠ Docker n'est pas encore prêt. Veuillez le configurer manuellement.${NC}"
            echo -e "${YELLOW}  Ouvrez Docker Desktop depuis vos Applications et suivez les instructions.${NC}"
        fi
    fi
}

# Installer Node.js (optionnel mais recommandé pour le développement frontend)
install_nodejs() {
    if check_command node; then
        local version=$(node -v)
        echo -e "${GREEN}✓ Node.js est déjà installé (version $version)${NC}"
    else
        echo -e "${BLUE}Installation de Node.js LTS...${NC}"
        brew install node@20
        brew link node@20

        echo -e "${GREEN}✓ Node.js installé${NC}"
    fi
}

# Installer les outils de développement Xcode
install_xcode_tools() {
    if xcode-select -p &> /dev/null; then
        echo -e "${GREEN}✓ Xcode Command Line Tools sont déjà installés${NC}"
    else
        echo -e "${BLUE}Installation de Xcode Command Line Tools...${NC}"
        xcode-select --install

        # Attendre que l'installation soit terminée
        echo -e "${YELLOW}⚠ Une fenêtre d'installation va s'ouvrir. Veuillez suivre les instructions.${NC}"
        echo -e "${YELLOW}Appuyez sur Entrée une fois l'installation terminée...${NC}"
        read -r
    fi
}

# Vérifier la configuration après installation
verify_installation() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}         Vérification de l'installation                        ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    local all_ok=true

    # Vérifier Git
    if check_command git; then
        echo -e "${GREEN}✓ Git:${NC} $(git --version)"
    else
        echo -e "${RED}✗ Git: non installé${NC}"
        all_ok=false
    fi

    # Vérifier Docker
    if check_command docker; then
        echo -e "${GREEN}✓ Docker:${NC} $(docker --version)"
    else
        echo -e "${RED}✗ Docker: non installé${NC}"
        all_ok=false
    fi

    # Vérifier Docker Compose
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✓ Docker Compose:${NC} $(docker compose version --short)"
    elif check_command docker-compose; then
        echo -e "${GREEN}✓ Docker Compose:${NC} $(docker-compose --version)"
    else
        echo -e "${RED}✗ Docker Compose: non disponible${NC}"
        all_ok=false
    fi

    # Vérifier Node.js
    if check_command node; then
        echo -e "${GREEN}✓ Node.js:${NC} $(node -v)"
    else
        echo -e "${YELLOW}⚠ Node.js: non installé (optionnel)${NC}"
    fi

    # Vérifier npm
    if check_command npm; then
        echo -e "${GREEN}✓ npm:${NC} $(npm -v)"
    else
        echo -e "${YELLOW}⚠ npm: non installé (optionnel)${NC}"
    fi

    echo ""

    if $all_ok; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  Tous les prérequis sont installés! Vous pouvez maintenant    ${NC}"
        echo -e "${GREEN}  exécuter: ./azalscore-launcher.sh                            ${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    else
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  Certains prérequis sont manquants. Veuillez les installer    ${NC}"
        echo -e "${RED}  manuellement ou relancer ce script.                          ${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        exit 1
    fi
}

# Configuration de Docker (si installé)
configure_docker() {
    if check_command docker; then
        echo ""
        echo -e "${BLUE}Configuration de Docker...${NC}"

        # Vérifier si Docker est démarré
        if ! docker info &> /dev/null; then
            echo -e "${YELLOW}Docker n'est pas en cours d'exécution.${NC}"
            echo -e "${YELLOW}Tentative de démarrage de Docker Desktop...${NC}"
            open -a Docker

            echo "Attente du démarrage de Docker (60 secondes max)..."
            local counter=0
            while ! docker info &> /dev/null && [ $counter -lt 60 ]; do
                sleep 2
                counter=$((counter + 2))
                echo -n "."
            done
            echo ""

            if docker info &> /dev/null; then
                echo -e "${GREEN}✓ Docker est maintenant en cours d'exécution${NC}"
            else
                echo -e "${YELLOW}⚠ Docker n'a pas démarré. Veuillez le démarrer manuellement.${NC}"
            fi
        else
            echo -e "${GREEN}✓ Docker est en cours d'exécution${NC}"
        fi
    fi
}

# Menu principal
main() {
    echo ""
    echo -e "${BLUE}Cette installation va configurer les éléments suivants:${NC}"
    echo "  1. Xcode Command Line Tools (outils de développement)"
    echo "  2. Homebrew (gestionnaire de paquets)"
    echo "  3. Git (contrôle de version)"
    echo "  4. Docker Desktop (conteneurisation)"
    echo "  5. Node.js LTS (optionnel, pour le développement frontend)"
    echo ""
    echo -e "${YELLOW}Voulez-vous continuer? (o/n)${NC}"
    read -r response

    if [[ ! "$response" =~ ^[OoYy]$ ]]; then
        echo "Installation annulée."
        exit 0
    fi

    echo ""

    # Installation dans l'ordre des dépendances
    install_xcode_tools
    install_homebrew
    install_git
    install_docker
    install_nodejs
    configure_docker
    verify_installation
}

# Exécuter le script
main "$@"
