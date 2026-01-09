#!/bin/bash
#
# Azalscore - Demarrage rapide pour Debian/Ubuntu
# Prereqis: Docker doit etre installe et en cours d'execution
#
# Usage: ./quick-start.sh
#

set -e

INSTALL_DIR="$HOME/Azalscore"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[ERREUR]${NC} $1"; }

# Verifier Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker n'est pas installe."
    log_error "Executez d'abord: ./install-debian.sh"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker n'est pas en cours d'execution."
    log_info "Demarrage de Docker..."
    sudo systemctl start docker || sudo service docker start
    sleep 3
fi

# Aller dans le repertoire
if [ ! -d "$INSTALL_DIR" ]; then
    log_error "Azalscore n'est pas installe dans $INSTALL_DIR"
    exit 1
fi

cd "$INSTALL_DIR"

# Creer .env si necessaire
if [ ! -f ".env" ]; then
    log_info "Creation du fichier .env..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        # Generer des cles
        SECRET=$(openssl rand -hex 32)
        sed -i "s/CHANGEME_PASSWORD/$(openssl rand -hex 16)/g" .env
        sed -i "s/CHANGEME_SECRET_KEY/$SECRET/g" .env
    fi
fi

# Demarrer l'application
log_info "Demarrage d'Azalscore..."

docker compose down 2>/dev/null || true
docker compose up --build -d

# Attendre que l'API soit prete
log_info "Attente du demarrage de l'API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Verifier
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           Azalscore est pret!                                 ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}API:${NC}          http://localhost:8000"
    echo -e "  ${CYAN}Documentation:${NC} http://localhost:8000/docs"
    echo -e "  ${CYAN}Frontend:${NC}     http://localhost:3000"
    echo ""
    echo -e "  ${YELLOW}Logs:${NC}  docker compose logs -f"
    echo -e "  ${YELLOW}Stop:${NC}  docker compose down"
    echo ""
else
    log_error "L'API n'est pas encore prete."
    log_info "Verifiez les logs: docker compose logs -f"
fi
