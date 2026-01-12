#!/bin/bash
# ============================================================
# AZALSCORE - Script de Déploiement Production
# ============================================================
# Usage: ./deploy_production.sh [railway|render|vps]
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================
# VÉRIFICATIONS PRÉ-DÉPLOIEMENT
# ============================================================

check_prerequisites() {
    log_info "Vérification des prérequis..."

    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 non trouvé"
        exit 1
    fi
    log_success "Python $(python3 --version)"

    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker non trouvé (optionnel pour Railway/Render)"
    else
        log_success "Docker $(docker --version | cut -d' ' -f3)"
    fi

    # Vérifier fichier .env
    if [ ! -f ".env.production" ]; then
        log_warning ".env.production non trouvé, création..."
        create_env_file
    fi
    log_success ".env.production présent"
}

create_env_file() {
    cat > .env.production << 'EOF'
# ============================================================
# AZALSCORE - Configuration Production
# ============================================================
# ATTENTION: Remplacer TOUTES les valeurs avant déploiement !
# ============================================================

# Environnement
ENVIRONMENT=production
DEBUG=false

# Base de données PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/azals
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Secrets (GÉNÉRER DES VALEURS UNIQUES !)
# python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=CHANGEZ_MOI_AVEC_UNE_VRAIE_CLE_64_CARACTERES_MINIMUM
BOOTSTRAP_SECRET=CHANGEZ_MOI_AUSSI_AVEC_UNE_VRAIE_CLE_64_CARACTERES

# Chiffrement AES-256
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=CHANGEZ_MOI_CLE_FERNET

# CORS (domaines autorisés)
CORS_ORIGINS=https://app.azalscore.com,https://azalscore.com

# Redis (cache et rate limiting)
REDIS_URL=redis://localhost:6379/0

# Stripe
STRIPE_API_KEY_LIVE=sk_live_votre_cle
STRIPE_PUBLISHABLE_KEY_LIVE=pk_live_votre_cle
STRIPE_WEBHOOK_SECRET=whsec_votre_secret
STRIPE_LIVE_MODE=true

# Email (Resend)
RESEND_API_KEY=re_votre_cle
EMAIL_FROM=noreply@azalscore.com

# Monitoring (optionnel)
SENTRY_DSN=
GRAFANA_PASSWORD=

# UUID strict
DB_STRICT_UUID=true
DB_AUTO_RESET_ON_VIOLATION=false
EOF
    log_success ".env.production créé - MODIFIEZ LES VALEURS !"
}

# ============================================================
# GÉNÉRATION DES SECRETS
# ============================================================

generate_secrets() {
    log_info "Génération des secrets..."
    
    echo ""
    echo "=== SECRETS À COPIER DANS .env.production ==="
    echo ""
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
    echo ""
    echo "BOOTSTRAP_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
    echo ""
    echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null || echo 'Installer cryptography: pip install cryptography')"
    echo ""
    echo "=============================================="
}

# ============================================================
# DÉPLOIEMENT RAILWAY
# ============================================================

deploy_railway() {
    log_info "Déploiement sur Railway..."

    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI non installé"
        echo "Installation: npm i -g @railway/cli"
        exit 1
    fi

    # Vérifier login
    if ! railway whoami &> /dev/null; then
        log_info "Connexion à Railway..."
        railway login
    fi

    # Créer le projet si nécessaire
    if [ ! -f "railway.json" ]; then
        log_info "Création du projet Railway..."
        railway init
    fi

    # Ajouter PostgreSQL
    log_info "Configuration PostgreSQL..."
    railway add --plugin postgresql || true

    # Ajouter Redis
    log_info "Configuration Redis..."
    railway add --plugin redis || true

    # Variables d'environnement
    log_info "Configuration des variables..."
    railway variables set ENVIRONMENT=production
    railway variables set DEBUG=false
    
    echo ""
    log_warning "IMPORTANT: Configurez les secrets via le dashboard Railway !"
    echo "https://railway.app/dashboard"
    echo ""

    # Déployer
    log_info "Déploiement en cours..."
    railway up

    log_success "Déploiement Railway terminé !"
    railway status
}

# ============================================================
# DÉPLOIEMENT RENDER
# ============================================================

deploy_render() {
    log_info "Déploiement sur Render..."

    if [ ! -f "render.yaml" ]; then
        log_info "Création render.yaml..."
        create_render_yaml
    fi

    echo ""
    echo "=== INSTRUCTIONS RENDER ==="
    echo ""
    echo "1. Connectez-vous sur https://render.com"
    echo "2. New > Blueprint"
    echo "3. Connectez votre repo GitHub"
    echo "4. Render détectera automatiquement render.yaml"
    echo "5. Configurez les secrets dans le dashboard"
    echo ""
    log_success "render.yaml prêt !"
}

create_render_yaml() {
    cat > render.yaml << 'EOF'
# AZALSCORE - Render Blueprint
services:
  - type: web
    name: azalscore-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: DATABASE_URL
        fromDatabase:
          name: azalscore-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: azalscore-redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: BOOTSTRAP_SECRET
        generateValue: true

databases:
  - name: azalscore-db
    plan: starter
    postgresMajorVersion: 15

redis:
  - name: azalscore-redis
    plan: starter
EOF
}

# ============================================================
# DÉPLOIEMENT VPS (Docker Compose)
# ============================================================

deploy_vps() {
    log_info "Déploiement VPS (Docker Compose)..."

    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose non trouvé"
        exit 1
    fi

    # Vérifier .env.production
    if [ ! -f ".env.production" ]; then
        log_error "Créez .env.production d'abord"
        exit 1
    fi

    # Copier .env
    cp .env.production .env

    # Build et start
    log_info "Build des images..."
    docker-compose -f docker-compose.prod.yml build

    log_info "Démarrage des services..."
    docker-compose -f docker-compose.prod.yml up -d

    log_info "Vérification santé..."
    sleep 10
    
    if curl -sf http://localhost:8000/health > /dev/null; then
        log_success "API opérationnelle sur http://localhost:8000"
    else
        log_warning "L'API ne répond pas encore, vérifiez les logs"
    fi

    docker-compose -f docker-compose.prod.yml ps
    log_success "Déploiement VPS terminé !"
}

# ============================================================
# TESTS PRÉ-PRODUCTION
# ============================================================

run_tests() {
    log_info "Exécution des tests..."

    # Tests Python
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short || {
            log_error "Tests échoués !"
            exit 1
        }
        log_success "Tests Python OK"
    else
        log_warning "pytest non trouvé, tests ignorés"
    fi
}

# ============================================================
# MAIN
# ============================================================

main() {
    echo ""
    echo "================================================"
    echo "   AZALSCORE - Déploiement Production"
    echo "================================================"
    echo ""

    case "${1:-help}" in
        railway)
            check_prerequisites
            run_tests
            deploy_railway
            ;;
        render)
            check_prerequisites
            deploy_render
            ;;
        vps)
            check_prerequisites
            run_tests
            deploy_vps
            ;;
        secrets)
            generate_secrets
            ;;
        test)
            run_tests
            ;;
        *)
            echo "Usage: $0 {railway|render|vps|secrets|test}"
            echo ""
            echo "  railway  - Déployer sur Railway.app"
            echo "  render   - Préparer pour Render.com"
            echo "  vps      - Déployer avec Docker Compose"
            echo "  secrets  - Générer les secrets"
            echo "  test     - Lancer les tests"
            echo ""
            exit 1
            ;;
    esac
}

main "$@"
