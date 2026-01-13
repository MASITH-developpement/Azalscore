#!/bin/bash
# AZALS - Script de déploiement automatique
# =========================================
# Usage: ./scripts/deploy/deploy.sh [railway|ovh|docker]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier les prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi

    log_success "Prérequis vérifiés"
}

# Générer les secrets manquants
generate_secrets() {
    log_info "Génération des secrets..."

    if [ -z "$SECRET_KEY" ]; then
        export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
        log_warning "SECRET_KEY générée automatiquement"
    fi

    if [ -z "$BOOTSTRAP_SECRET" ]; then
        export BOOTSTRAP_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
        log_warning "BOOTSTRAP_SECRET générée automatiquement"
    fi

    if [ -z "$ENCRYPTION_KEY" ]; then
        export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        log_warning "ENCRYPTION_KEY générée automatiquement"
    fi
}

# Créer le fichier .env si absent
create_env_file() {
    if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
        log_info "Création du fichier .env.production..."

        cat > "$PROJECT_ROOT/.env.production" << EOF
# AZALS Production Environment
# Généré automatiquement le $(date)

# Database (OBLIGATOIRE - remplacez par votre URL)
DATABASE_URL=${DATABASE_URL:-postgresql://azals:azals@localhost:5432/azals}

# Security
SECRET_KEY=${SECRET_KEY}
BOOTSTRAP_SECRET=${BOOTSTRAP_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Application
AZALS_ENV=production
DEBUG=false
CORS_ORIGINS=${CORS_ORIGINS:-https://votre-domaine.com}

# Stripe (optionnel)
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-}

# Email (optionnel)
SMTP_HOST=${SMTP_HOST:-}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USER=${SMTP_USER:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
SMTP_FROM=${SMTP_FROM:-}

# MASITH Tenant
MASITH_TENANT_ID=masith
MASITH_ADMIN_EMAIL=contact@masith.fr
MASITH_ADMIN_PASSWORD=Gobelet2026!
EOF

        log_success "Fichier .env.production créé"
        log_warning "IMPORTANT: Modifiez DATABASE_URL et CORS_ORIGINS avant de déployer!"
    fi
}

# Déploiement Docker standard
deploy_docker() {
    log_info "Déploiement Docker standard..."

    cd "$PROJECT_ROOT"

    # Construire les images
    log_info "Construction des images Docker..."
    docker-compose -f docker-compose.prod.yml build

    # Démarrer les services
    log_info "Démarrage des services..."
    docker-compose -f docker-compose.prod.yml up -d

    log_success "Déploiement Docker terminé"
    log_info "API: http://localhost:8000"
    log_info "Frontend: http://localhost:80"
}

# Déploiement Railway
deploy_railway() {
    log_info "Préparation pour Railway..."

    if ! command -v railway &> /dev/null; then
        log_warning "CLI Railway non installé. Installation..."
        npm install -g @railway/cli
    fi

    cd "$PROJECT_ROOT"

    log_info "Connexion à Railway..."
    railway login

    log_info "Déploiement sur Railway..."
    railway up

    log_success "Déploiement Railway lancé"
}

# Déploiement OVH (VPS)
deploy_ovh() {
    log_info "Déploiement OVH (VPS)..."

    if [ -z "$OVH_HOST" ]; then
        log_error "Variable OVH_HOST non définie"
        log_info "Usage: OVH_HOST=user@ip ./deploy.sh ovh"
        exit 1
    fi

    cd "$PROJECT_ROOT"

    # Copier les fichiers sur le serveur
    log_info "Copie des fichiers vers $OVH_HOST..."
    rsync -avz --exclude '.git' --exclude 'node_modules' --exclude '__pycache__' \
        --exclude '.env' --exclude 'venv' \
        . "$OVH_HOST:/opt/azalscore/"

    # Exécuter le déploiement sur le serveur
    log_info "Exécution du déploiement distant..."
    ssh "$OVH_HOST" << 'ENDSSH'
        cd /opt/azalscore
        docker-compose -f docker-compose.prod.yml pull
        docker-compose -f docker-compose.prod.yml up -d --build
ENDSSH

    log_success "Déploiement OVH terminé"
}

# Afficher l'aide
show_help() {
    echo "AZALS - Script de déploiement automatique"
    echo ""
    echo "Usage: ./deploy.sh [COMMANDE]"
    echo ""
    echo "Commandes:"
    echo "  docker    Déploiement Docker local/VPS standard"
    echo "  railway   Déploiement sur Railway"
    echo "  ovh       Déploiement sur VPS OVH (nécessite OVH_HOST)"
    echo "  help      Afficher cette aide"
    echo ""
    echo "Variables d'environnement:"
    echo "  DATABASE_URL     URL PostgreSQL (obligatoire)"
    echo "  SECRET_KEY       Clé JWT (générée si absente)"
    echo "  CORS_ORIGINS     Origins CORS (obligatoire en prod)"
    echo "  OVH_HOST         user@ip pour déploiement OVH"
    echo ""
}

# Point d'entrée
main() {
    echo "========================================"
    echo "  AZALSCORE - Déploiement Automatique  "
    echo "========================================"

    check_prerequisites
    generate_secrets
    create_env_file

    case "${1:-docker}" in
        docker)
            deploy_docker
            ;;
        railway)
            deploy_railway
            ;;
        ovh)
            deploy_ovh
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
