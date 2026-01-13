#!/bin/bash
# AZALS - Déploiement Serveur Local
# ==================================
# Déploie AZALSCORE sur un serveur local via SSH
#
# Usage: ./scripts/deploy/deploy-local.sh [USER@HOST]
# Exemple: ./scripts/deploy/deploy-local.sh root@192.168.1.185

set -e

# Configuration par défaut
DEFAULT_HOST="root@192.168.1.185"
REMOTE_HOST="${1:-$DEFAULT_HOST}"
REMOTE_DIR="/opt/azalscore"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================"
echo "  AZALSCORE - Déploiement Local"
echo "  Cible: $REMOTE_HOST"
echo "========================================"

# Vérifier la connexion SSH
log_info "Test de connexion SSH..."
if ! ssh -o ConnectTimeout=5 "$REMOTE_HOST" "echo 'SSH OK'" &>/dev/null; then
    log_error "Impossible de se connecter à $REMOTE_HOST"
    log_info "Vérifiez:"
    log_info "  1. Le serveur est allumé"
    log_info "  2. SSH est activé"
    log_info "  3. Vos clés SSH sont configurées"
    exit 1
fi
log_success "Connexion SSH établie"

# Installer Docker sur le serveur distant si nécessaire
log_info "Vérification de Docker sur le serveur..."
ssh "$REMOTE_HOST" << 'ENDSSH'
if ! command -v docker &> /dev/null; then
    echo "[INFO] Installation de Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "[INFO] Installation de Docker Compose..."
    apt-get update && apt-get install -y docker-compose-plugin || {
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    }
fi

echo "[OK] Docker est prêt"
ENDSSH
log_success "Docker configuré"

# Créer le répertoire distant
log_info "Préparation du répertoire distant..."
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Synchroniser les fichiers
log_info "Synchronisation des fichiers (peut prendre quelques minutes)..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude '.env.local' \
    --exclude 'venv' \
    --exclude '.venv' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude '.pytest_cache' \
    --exclude 'test.db' \
    "$PROJECT_ROOT/" "$REMOTE_HOST:$REMOTE_DIR/"
log_success "Fichiers synchronisés"

# Créer le fichier .env.production sur le serveur
log_info "Configuration de l'environnement production..."
ssh "$REMOTE_HOST" << ENDSSH
cd $REMOTE_DIR

# Générer les secrets si .env.production n'existe pas
if [ ! -f .env.production ]; then
    echo "[INFO] Génération du fichier .env.production..."

    SECRET_KEY=\$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48)
    BOOTSTRAP_SECRET=\$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48)

    cat > .env.production << EOF
# AZALS Production - Généré automatiquement
# Serveur: 192.168.1.185

# Database
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=\$(openssl rand -base64 24 | tr -d '/+=')
DATABASE_URL=postgresql://azals_user:\${POSTGRES_PASSWORD}@postgres:5432/azals

# Security
SECRET_KEY=\${SECRET_KEY}
BOOTSTRAP_SECRET=\${BOOTSTRAP_SECRET}

# Application
AZALS_ENV=production
DEBUG=false
CORS_ORIGINS=http://192.168.1.185,http://localhost

# Redis
REDIS_URL=redis://redis:6379/0

# MASITH Tenant
MASITH_TENANT_ID=masith
MASITH_ADMIN_EMAIL=contact@masith.fr
MASITH_ADMIN_PASSWORD=Gobelet2026!

# Monitoring (optionnel)
GRAFANA_USER=admin
GRAFANA_PASSWORD=\$(openssl rand -base64 12 | tr -d '/+=')
EOF

    echo "[OK] Fichier .env.production créé"
else
    echo "[INFO] .env.production existe déjà"
fi
ENDSSH
log_success "Environnement configuré"

# Construire et démarrer les conteneurs
log_info "Construction et démarrage des conteneurs Docker..."
ssh "$REMOTE_HOST" << ENDSSH
cd $REMOTE_DIR

# Arrêter les anciens conteneurs si existants
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Construire les images
echo "[INFO] Construction des images (peut prendre 5-10 minutes)..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Démarrer les services
echo "[INFO] Démarrage des services..."
docker-compose -f docker-compose.prod.yml up -d

# Attendre que tout soit prêt
echo "[INFO] Attente du démarrage des services..."
sleep 30

# Vérifier l'état
docker-compose -f docker-compose.prod.yml ps
ENDSSH
log_success "Conteneurs démarrés"

# Vérifier que l'API répond
log_info "Vérification de l'API..."
sleep 10
if ssh "$REMOTE_HOST" "curl -sf http://localhost:8000/health/live" &>/dev/null; then
    log_success "API opérationnelle"
else
    log_warning "L'API n'est pas encore prête (normal au premier démarrage)"
    log_info "Vérifiez les logs: ssh $REMOTE_HOST 'docker-compose -f $REMOTE_DIR/docker-compose.prod.yml logs -f api'"
fi

echo ""
echo "========================================"
echo "  DÉPLOIEMENT TERMINÉ"
echo "========================================"
echo ""
echo "URLs d'accès:"
echo "  - Frontend: http://192.168.1.185"
echo "  - API:      http://192.168.1.185:8000"
echo "  - API Docs: http://192.168.1.185:8000/docs"
echo "  - Grafana:  http://192.168.1.185:3000"
echo ""
echo "Connexion admin:"
echo "  - Email:    contact@masith.fr"
echo "  - Password: Gobelet2026!"
echo ""
echo "Commandes utiles:"
echo "  - Logs:     ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose -f docker-compose.prod.yml logs -f'"
echo "  - Status:   ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose -f docker-compose.prod.yml ps'"
echo "  - Restart:  ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose -f docker-compose.prod.yml restart'"
echo ""
