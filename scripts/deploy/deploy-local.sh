#!/bin/bash
# AZALS - Déploiement Serveur Local avec GitHub
# ==============================================
# Déploie AZALSCORE sur un serveur local via SSH
# avec mise à jour automatique depuis GitHub branche develop
#
# Usage:
#   ./scripts/deploy/deploy-local.sh [USER@HOST] [COMMANDE]
#
# Commandes:
#   install   - Installation complète (défaut)
#   update    - Mise à jour depuis GitHub develop
#   restart   - Redémarrer les services
#   logs      - Voir les logs
#   status    - État des services
#
# Exemples:
#   ./scripts/deploy/deploy-local.sh root@192.168.1.185
#   ./scripts/deploy/deploy-local.sh root@192.168.1.185 update
#   ./scripts/deploy/deploy-local.sh root@192.168.1.185 logs

set -e

# Configuration
DEFAULT_HOST="root@192.168.1.185"
REMOTE_HOST="${1:-$DEFAULT_HOST}"
COMMAND="${2:-install}"
REMOTE_DIR="/opt/azalscore"
GITHUB_REPO="https://github.com/MASITH-developpement/Azalscore.git"
GITHUB_BRANCH="develop"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

header() {
    echo ""
    echo "========================================"
    echo "  AZALSCORE - $1"
    echo "  Serveur: $REMOTE_HOST"
    echo "  Branche: $GITHUB_BRANCH"
    echo "========================================"
    echo ""
}

# Vérifier la connexion SSH
check_ssh() {
    log_info "Test de connexion SSH..."
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_HOST" "echo 'OK'" &>/dev/null; then
        log_error "Impossible de se connecter à $REMOTE_HOST"
        echo ""
        echo "Vérifiez:"
        echo "  1. Le serveur est allumé"
        echo "  2. SSH est activé"
        echo "  3. Clé SSH configurée: ssh-copy-id $REMOTE_HOST"
        exit 1
    fi
    log_success "Connexion SSH établie"
}

# Installer Docker sur le serveur
install_docker() {
    log_step "Installation de Docker..."
    ssh "$REMOTE_HOST" << 'ENDSSH'
set -e

# Installer Docker si absent
if ! command -v docker &> /dev/null; then
    echo "[INFO] Installation de Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo "[OK] Docker installé"
else
    echo "[OK] Docker déjà installé"
fi

# Installer git si absent
if ! command -v git &> /dev/null; then
    apt-get install -y git
fi

docker --version
docker compose version
ENDSSH
    log_success "Docker prêt"
}

# Cloner ou mettre à jour depuis GitHub
setup_github() {
    log_step "Configuration GitHub (branche $GITHUB_BRANCH)..."
    ssh "$REMOTE_HOST" << ENDSSH
set -e
cd /opt

if [ -d "$REMOTE_DIR/.git" ]; then
    echo "[INFO] Repository existant, mise à jour..."
    cd $REMOTE_DIR
    git fetch origin
    git checkout $GITHUB_BRANCH
    git pull origin $GITHUB_BRANCH
    echo "[OK] Code mis à jour depuis GitHub"
else
    echo "[INFO] Clonage du repository..."
    rm -rf $REMOTE_DIR
    git clone -b $GITHUB_BRANCH $GITHUB_REPO $REMOTE_DIR
    echo "[OK] Repository cloné"
fi

cd $REMOTE_DIR
echo "Commit actuel: \$(git log -1 --oneline)"
ENDSSH
    log_success "Code synchronisé avec GitHub"
}

# Configurer l'environnement
setup_env() {
    log_step "Configuration de l'environnement..."
    ssh "$REMOTE_HOST" << 'ENDSSH'
set -e
cd /opt/azalscore

if [ ! -f .env.production ]; then
    echo "[INFO] Création de .env.production..."

    # Générer des secrets sécurisés
    POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')
    SECRET_KEY=$(openssl rand -base64 48 | tr -d '/+=')
    BOOTSTRAP_SECRET=$(openssl rand -base64 48 | tr -d '/+=')
    GRAFANA_PASSWORD=$(openssl rand -base64 16 | tr -d '/+=')

    cat > .env.production << EOF
# AZALS Production - Serveur Local
# Généré le $(date)
# GitHub: develop

# Database
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://azals_user:${POSTGRES_PASSWORD}@postgres:5432/azals

# Security
SECRET_KEY=${SECRET_KEY}
BOOTSTRAP_SECRET=${BOOTSTRAP_SECRET}

# Application
AZALS_ENV=production
DEBUG=false
CORS_ORIGINS=http://192.168.1.185,http://localhost,http://127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# MASITH Tenant (admin initial)
MASITH_TENANT_ID=masith
MASITH_ADMIN_EMAIL=contact@masith.fr
MASITH_ADMIN_PASSWORD=Gobelet2026!

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# Stripe (à configurer si paiements activés)
# STRIPE_SECRET_KEY=sk_live_...
# STRIPE_WEBHOOK_SECRET=whsec_...

# Email SMTP (à configurer)
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=
# SMTP_PASSWORD=
# SMTP_FROM=noreply@azalscore.com
EOF

    echo "[OK] .env.production créé"
    echo ""
    echo "IMPORTANT: Notez le mot de passe Grafana: ${GRAFANA_PASSWORD}"
else
    echo "[OK] .env.production existe déjà"
fi
ENDSSH
    log_success "Environnement configuré"
}

# Construire et démarrer
build_and_start() {
    log_step "Construction et démarrage des services..."
    ssh "$REMOTE_HOST" << 'ENDSSH'
set -e
cd /opt/azalscore

echo "[INFO] Arrêt des anciens conteneurs..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

echo "[INFO] Construction des images Docker (5-10 min)..."
docker compose -f docker-compose.prod.yml build

echo "[INFO] Démarrage des services..."
docker compose -f docker-compose.prod.yml up -d

echo "[INFO] Attente du démarrage..."
sleep 20

echo ""
echo "[STATUS] État des services:"
docker compose -f docker-compose.prod.yml ps
ENDSSH
    log_success "Services démarrés"
}

# Mise à jour depuis GitHub
do_update() {
    header "Mise à jour"
    check_ssh

    log_step "Mise à jour depuis GitHub ($GITHUB_BRANCH)..."
    ssh "$REMOTE_HOST" << ENDSSH
set -e
cd $REMOTE_DIR

echo "[INFO] Pull des dernières modifications..."
git fetch origin
git checkout $GITHUB_BRANCH
git pull origin $GITHUB_BRANCH

echo ""
echo "Commit actuel: \$(git log -1 --oneline)"
echo ""

echo "[INFO] Reconstruction des images..."
docker compose -f docker-compose.prod.yml build

echo "[INFO] Redémarrage des services..."
docker compose -f docker-compose.prod.yml up -d

sleep 10
echo ""
docker compose -f docker-compose.prod.yml ps
ENDSSH

    log_success "Mise à jour terminée"
    show_urls
}

# Redémarrer les services
do_restart() {
    header "Redémarrage"
    check_ssh
    ssh "$REMOTE_HOST" "cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml restart"
    log_success "Services redémarrés"
}

# Voir les logs
do_logs() {
    header "Logs"
    check_ssh
    ssh "$REMOTE_HOST" "cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml logs -f --tail=100"
}

# État des services
do_status() {
    header "Status"
    check_ssh
    ssh "$REMOTE_HOST" << ENDSSH
cd $REMOTE_DIR
echo "=== Services Docker ==="
docker compose -f docker-compose.prod.yml ps
echo ""
echo "=== Version Git ==="
git log -1 --oneline
echo "Branche: \$(git branch --show-current)"
echo ""
echo "=== Santé API ==="
curl -s http://localhost:8000/health/live || echo "API non disponible"
ENDSSH
}

# Installation complète
do_install() {
    header "Installation"
    check_ssh
    install_docker
    setup_github
    setup_env
    build_and_start
    show_urls
}

# Afficher les URLs
show_urls() {
    echo ""
    echo "========================================"
    echo "  DÉPLOIEMENT RÉUSSI"
    echo "========================================"
    echo ""
    echo "URLs d'accès:"
    echo "  - Frontend:  http://192.168.1.185"
    echo "  - API:       http://192.168.1.185:8000"
    echo "  - API Docs:  http://192.168.1.185:8000/docs"
    echo "  - Grafana:   http://192.168.1.185:3000"
    echo ""
    echo "Connexion admin AZALSCORE:"
    echo "  - Email:     contact@masith.fr"
    echo "  - Password:  Gobelet2026!"
    echo ""
    echo "Commandes utiles:"
    echo "  - Mise à jour:  $0 $REMOTE_HOST update"
    echo "  - Logs:         $0 $REMOTE_HOST logs"
    echo "  - Status:       $0 $REMOTE_HOST status"
    echo "  - Restart:      $0 $REMOTE_HOST restart"
    echo ""
}

# Aide
show_help() {
    echo "AZALSCORE - Script de déploiement local"
    echo ""
    echo "Usage: $0 [USER@HOST] [COMMANDE]"
    echo ""
    echo "Commandes:"
    echo "  install   Installation complète (défaut)"
    echo "  update    Mise à jour depuis GitHub develop"
    echo "  restart   Redémarrer les services"
    echo "  logs      Voir les logs en temps réel"
    echo "  status    État des services"
    echo "  help      Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 root@192.168.1.185"
    echo "  $0 root@192.168.1.185 update"
    echo "  $0 ubuntu@192.168.1.185 logs"
    echo ""
}

# Point d'entrée
case "$COMMAND" in
    install)
        do_install
        ;;
    update)
        do_update
        ;;
    restart)
        do_restart
        ;;
    logs)
        do_logs
        ;;
    status)
        do_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Commande inconnue: $COMMAND"
        show_help
        exit 1
        ;;
esac
