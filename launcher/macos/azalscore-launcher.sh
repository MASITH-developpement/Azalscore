#!/bin/bash
#
# Azalscore Launcher pour macOS
# Ce script installe, met à jour et lance Azalscore
#

set -e

# Configuration
REPO_URL="https://github.com/MASITH-developpement/Azalscore.git"
BRANCH="main"
INSTALL_DIR="$HOME/Azalscore"
LOG_FILE="$HOME/.azalscore/launcher.log"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Créer le dossier de logs
mkdir -p "$(dirname "$LOG_FILE")"

# Fonction de log
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$message" | tee -a "$LOG_FILE"
}

# Afficher le logo
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
    echo "║                   Launcher pour macOS                         ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Vérifier si une commande existe
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Vérifier les prérequis
check_prerequisites() {
    log "${BLUE}Vérification des prérequis...${NC}"
    local missing=()

    # Vérifier Git
    if check_command git; then
        log "${GREEN}✓ Git est installé${NC}"
    else
        missing+=("git")
        log "${RED}✗ Git n'est pas installé${NC}"
    fi

    # Vérifier Docker
    if check_command docker; then
        log "${GREEN}✓ Docker est installé${NC}"
        # Vérifier si Docker est en cours d'exécution
        if docker info &> /dev/null; then
            log "${GREEN}✓ Docker est en cours d'exécution${NC}"
        else
            log "${YELLOW}⚠ Docker n'est pas démarré. Tentative de démarrage...${NC}"
            open -a Docker
            log "${YELLOW}Attente du démarrage de Docker (30 secondes max)...${NC}"
            local counter=0
            while ! docker info &> /dev/null && [ $counter -lt 30 ]; do
                sleep 1
                counter=$((counter + 1))
                echo -n "."
            done
            echo ""
            if docker info &> /dev/null; then
                log "${GREEN}✓ Docker est maintenant en cours d'exécution${NC}"
            else
                log "${RED}✗ Impossible de démarrer Docker. Veuillez le démarrer manuellement.${NC}"
                return 1
            fi
        fi
    else
        missing+=("docker")
        log "${RED}✗ Docker n'est pas installé${NC}"
    fi

    # Vérifier Docker Compose
    if docker compose version &> /dev/null || check_command docker-compose; then
        log "${GREEN}✓ Docker Compose est disponible${NC}"
    else
        missing+=("docker-compose")
        log "${RED}✗ Docker Compose n'est pas disponible${NC}"
    fi

    # Vérifier Node.js (optionnel pour le développement frontend)
    if check_command node; then
        local node_version=$(node -v)
        log "${GREEN}✓ Node.js est installé ($node_version)${NC}"
    else
        log "${YELLOW}⚠ Node.js n'est pas installé (optionnel pour le développement frontend)${NC}"
    fi

    # Si des prérequis manquent
    if [ ${#missing[@]} -gt 0 ]; then
        log "${RED}Prérequis manquants: ${missing[*]}${NC}"
        log "${YELLOW}Exécutez d'abord: ./install-prerequisites.sh${NC}"
        return 1
    fi

    return 0
}

# Cloner ou mettre à jour le dépôt
update_repository() {
    log "${BLUE}Mise à jour du dépôt depuis la branche $BRANCH...${NC}"

    if [ -d "$INSTALL_DIR/.git" ]; then
        log "Dépôt existant détecté. Mise à jour..."
        cd "$INSTALL_DIR"

        # Sauvegarder les modifications locales
        if ! git diff --quiet 2>/dev/null; then
            log "${YELLOW}Modifications locales détectées. Sauvegarde avec stash...${NC}"
            git stash push -m "Sauvegarde automatique avant mise à jour $(date '+%Y-%m-%d %H:%M:%S')"
        fi

        # Récupérer les dernières modifications
        git fetch origin "$BRANCH"

        # Mettre à jour vers la dernière version
        git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" origin/"$BRANCH"
        git reset --hard origin/"$BRANCH"

        log "${GREEN}✓ Dépôt mis à jour avec succès${NC}"
    else
        log "Premier lancement. Clonage du dépôt..."

        # Supprimer le dossier s'il existe mais n'est pas un repo git
        if [ -d "$INSTALL_DIR" ]; then
            log "${YELLOW}Dossier existant non-git détecté. Suppression...${NC}"
            rm -rf "$INSTALL_DIR"
        fi

        # Cloner le dépôt
        git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"

        log "${GREEN}✓ Dépôt cloné avec succès${NC}"
    fi
}

# Configurer l'environnement
setup_environment() {
    log "${BLUE}Configuration de l'environnement...${NC}"
    cd "$INSTALL_DIR"

    # Créer le fichier .env s'il n'existe pas
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log "Création du fichier .env à partir de .env.example..."
            cp .env.example .env

            # Générer des clés secrètes
            SECRET_KEY=$(openssl rand -hex 32)
            BOOTSTRAP_SECRET=$(openssl rand -hex 32)
            DB_PASSWORD=$(openssl rand -hex 16)

            # Remplacer les valeurs par défaut (macOS sed)
            sed -i '' "s/CHANGEME_PASSWORD/$DB_PASSWORD/g" .env 2>/dev/null || sed -i "s/CHANGEME_PASSWORD/$DB_PASSWORD/g" .env
            sed -i '' "s/CHANGEME_SECRET_KEY/$SECRET_KEY/g" .env 2>/dev/null || sed -i "s/CHANGEME_SECRET_KEY/$SECRET_KEY/g" .env
            sed -i '' "s/CHANGEME_BOOTSTRAP_SECRET/$BOOTSTRAP_SECRET/g" .env 2>/dev/null || sed -i "s/CHANGEME_BOOTSTRAP_SECRET/$BOOTSTRAP_SECRET/g" .env

            log "${GREEN}✓ Fichier .env créé avec des clés sécurisées${NC}"
        else
            log "${RED}✗ Fichier .env.example non trouvé${NC}"
            return 1
        fi
    else
        log "${GREEN}✓ Fichier .env existant conservé${NC}"
    fi
}

# Construire et démarrer les conteneurs
start_application() {
    log "${BLUE}Démarrage de l'application...${NC}"
    cd "$INSTALL_DIR"

    # Arrêter les conteneurs existants
    log "Arrêt des conteneurs existants..."
    docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

    # Construire et démarrer
    log "Construction et démarrage des conteneurs..."
    if docker compose up --build -d 2>/dev/null; then
        log "${GREEN}✓ Conteneurs démarrés avec docker compose${NC}"
    elif docker-compose up --build -d 2>/dev/null; then
        log "${GREEN}✓ Conteneurs démarrés avec docker-compose${NC}"
    else
        log "${RED}✗ Erreur lors du démarrage des conteneurs${NC}"
        return 1
    fi

    # Attendre que l'API soit prête
    log "Attente du démarrage de l'API..."
    local counter=0
    local max_wait=60
    while [ $counter -lt $max_wait ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log "${GREEN}✓ API prête!${NC}"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    echo ""

    if [ $counter -ge $max_wait ]; then
        log "${YELLOW}⚠ L'API n'est pas encore prête. Vérifiez les logs avec: docker compose logs -f${NC}"
    fi
}

# Installer les dépendances frontend (optionnel)
setup_frontend() {
    if check_command node && check_command npm; then
        log "${BLUE}Installation des dépendances frontend...${NC}"
        cd "$INSTALL_DIR/frontend"

        if [ ! -d "node_modules" ]; then
            npm install
            log "${GREEN}✓ Dépendances frontend installées${NC}"
        else
            log "${GREEN}✓ Dépendances frontend déjà installées${NC}"
        fi
    fi
}

# Démarrer le frontend en mode développement
start_frontend_dev() {
    if check_command node && check_command npm; then
        log "${BLUE}Démarrage du frontend en mode développement...${NC}"
        cd "$INSTALL_DIR/frontend"

        # Vérifier si le frontend est déjà en cours d'exécution
        if lsof -i :3000 > /dev/null 2>&1; then
            log "${YELLOW}⚠ Le port 3000 est déjà utilisé${NC}"
        else
            # Démarrer le frontend en arrière-plan
            npm run dev > "$HOME/.azalscore/frontend.log" 2>&1 &
            log "${GREEN}✓ Frontend démarré sur http://localhost:3000${NC}"
        fi
    fi
}

# Afficher les informations de connexion
show_info() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}            Azalscore est maintenant en cours d'exécution!      ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}URLs d'accès:${NC}"
    echo -e "  ${BLUE}API Backend:${NC}     http://localhost:8000"
    echo -e "  ${BLUE}Documentation:${NC}   http://localhost:8000/docs"
    echo -e "  ${BLUE}Health Check:${NC}    http://localhost:8000/health"
    if check_command node; then
        echo -e "  ${BLUE}Frontend:${NC}        http://localhost:3000"
    fi
    echo ""
    echo -e "${CYAN}Commandes utiles:${NC}"
    echo -e "  ${BLUE}Voir les logs:${NC}   cd $INSTALL_DIR && docker compose logs -f"
    echo -e "  ${BLUE}Arrêter:${NC}         cd $INSTALL_DIR && docker compose down"
    echo -e "  ${BLUE}Redémarrer:${NC}      cd $INSTALL_DIR && docker compose restart"
    echo ""
    echo -e "${CYAN}Fichiers de log:${NC}"
    echo -e "  ${BLUE}Launcher:${NC}        $LOG_FILE"
    if [ -f "$HOME/.azalscore/frontend.log" ]; then
        echo -e "  ${BLUE}Frontend:${NC}        $HOME/.azalscore/frontend.log"
    fi
    echo ""
}

# Arrêter l'application
stop_application() {
    log "${BLUE}Arrêt de l'application...${NC}"
    cd "$INSTALL_DIR"

    docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

    # Arrêter le frontend si en cours d'exécution
    pkill -f "npm run dev" 2>/dev/null || true

    log "${GREEN}✓ Application arrêtée${NC}"
}

# Afficher l'aide
show_help() {
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start       Démarrer Azalscore (par défaut)"
    echo "  stop        Arrêter Azalscore"
    echo "  restart     Redémarrer Azalscore"
    echo "  update      Mettre à jour depuis GitHub sans redémarrer"
    echo "  logs        Afficher les logs des conteneurs"
    echo "  status      Afficher l'état des conteneurs"
    echo "  frontend    Démarrer le frontend en mode développement"
    echo "  help        Afficher cette aide"
    echo ""
}

# Menu principal
main() {
    show_logo

    local action="${1:-start}"

    case "$action" in
        start)
            check_prerequisites || exit 1
            update_repository
            setup_environment
            setup_frontend
            start_application
            show_info
            ;;
        stop)
            stop_application
            ;;
        restart)
            stop_application
            sleep 2
            check_prerequisites || exit 1
            start_application
            show_info
            ;;
        update)
            check_prerequisites || exit 1
            update_repository
            log "${GREEN}✓ Mise à jour terminée. Utilisez 'restart' pour appliquer les changements.${NC}"
            ;;
        logs)
            cd "$INSTALL_DIR"
            docker compose logs -f 2>/dev/null || docker-compose logs -f
            ;;
        status)
            cd "$INSTALL_DIR"
            docker compose ps 2>/dev/null || docker-compose ps
            ;;
        frontend)
            setup_frontend
            start_frontend_dev
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log "${RED}Option non reconnue: $action${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Exécuter le script
main "$@"
