#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Installation OVH VPS / Serveur Dédié
#===============================================================================
# Script d'installation complet et sécurisé pour serveurs OVH
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/MASITH-developpement/Azalscore/main/scripts/install/ovh/install_ovh.sh | sudo bash
#
# Ou:
#   ./install_ovh.sh
#
# Ce script:
#   1. Sécurise le serveur (hardening)
#   2. Installe les dépendances
#   3. Configure PostgreSQL
#   4. Installe AZALSCORE
#   5. Configure Nginx + SSL
#   6. Active le service systemd
#===============================================================================

set -euo pipefail
IFS=$'\n\t'

#===============================================================================
# CONFIGURATION
#===============================================================================

readonly SCRIPT_VERSION="1.0.0"
readonly INSTALL_DIR="/opt/azalscore"
readonly SERVICE_USER="azals"
readonly SERVICE_GROUP="azals"
readonly GITHUB_REPO="MASITH-developpement/Azalscore"
readonly BRANCH="main"

# Couleurs
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'
readonly BOLD='\033[1m'

# Variables d'état
DOMAIN=""
EMAIL=""
ENABLE_SSL=false
SKIP_HARDENING=false

#===============================================================================
# FONCTIONS UTILITAIRES
#===============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        INFO)  echo -e "${BLUE}[INFO]${NC} ${message}" ;;
        OK)    echo -e "${GREEN}[OK]${NC} ${message}" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} ${message}" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} ${message}" ;;
    esac

    echo "[${timestamp}] [${level}] ${message}" >> /var/log/azalscore-install.log
}

die() {
    log ERROR "$1"
    exit 1
}

print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
    ___   _____   _   _     _____  _____ _____ _____ _____
   / _ \ |__  /  / \ | |   /  ___|/  __ \  _  | ___ \  ___|
  / /_\ \  / /  / _ \| |   \ `--. | /  \/ | | | |_/ / |__
  |  _  | / /  / ___ \ |    `--. \| |   | | | |    /|  __|
  |_| |_|/_/  /_/   \_\_|___/\__/ | \__/\ \_/ / |\ \| |___
                       \_____\____/ \____/\___/\_| \_\____/

EOF
    echo -e "${NC}"
    echo -e "${BOLD}Installation OVH - VPS/Dédié v${SCRIPT_VERSION}${NC}"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        die "Ce script doit être exécuté en tant que root"
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        die "Système d'exploitation non supporté"
    fi

    source /etc/os-release

    case "${ID}" in
        debian|ubuntu)
            log OK "OS détecté: ${PRETTY_NAME}"
            ;;
        *)
            die "Seuls Debian et Ubuntu sont supportés"
            ;;
    esac
}

get_user_input() {
    echo ""
    echo -e "${BOLD}Configuration de l'installation:${NC}"
    echo ""

    # Domaine
    read -rp "Domaine (ex: azals.example.com): " DOMAIN
    if [[ -z "${DOMAIN}" ]]; then
        log WARN "Pas de domaine configuré - accès par IP uniquement"
        DOMAIN=""
    fi

    # Email pour Let's Encrypt
    if [[ -n "${DOMAIN}" ]]; then
        read -rp "Email pour Let's Encrypt: " EMAIL
        if [[ -n "${EMAIL}" ]]; then
            ENABLE_SSL=true
        fi
    fi

    # Hardening
    read -rp "Appliquer le hardening de sécurité? [Y/n] " response
    if [[ "${response,,}" =~ ^(n|no)$ ]]; then
        SKIP_HARDENING=true
    fi

    echo ""
    echo -e "${BOLD}Récapitulatif:${NC}"
    echo "  Domaine: ${DOMAIN:-'(aucun)'}"
    echo "  SSL:     ${ENABLE_SSL}"
    echo "  Hardening: $([[ "${SKIP_HARDENING}" == "true" ]] && echo 'Non' || echo 'Oui')"
    echo ""

    read -rp "Continuer l'installation? [Y/n] " response
    if [[ "${response,,}" =~ ^(n|no)$ ]]; then
        log INFO "Installation annulée"
        exit 0
    fi
}

#===============================================================================
# PHASE 1: PRÉPARATION DU SYSTÈME
#===============================================================================

prepare_system() {
    log INFO "Phase 1: Préparation du système..."

    # Mettre à jour le système
    log INFO "Mise à jour du système..."
    apt-get update -qq
    apt-get upgrade -y -qq

    # Installer les paquets de base
    log INFO "Installation des paquets de base..."
    apt-get install -y -qq \
        curl \
        wget \
        git \
        gnupg \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        lsb-release \
        unzip \
        htop \
        vim \
        tmux

    log OK "Système préparé"
}

#===============================================================================
# PHASE 2: HARDENING
#===============================================================================

apply_hardening() {
    if [[ "${SKIP_HARDENING}" == "true" ]]; then
        log INFO "Hardening ignoré"
        return
    fi

    log INFO "Phase 2: Application du hardening..."

    # Charger le script de hardening
    source "$(dirname "$0")/hardening.sh" 2>/dev/null || {
        log INFO "Téléchargement du script de hardening..."
        curl -fsSL "https://raw.githubusercontent.com/${GITHUB_REPO}/${BRANCH}/scripts/install/ovh/hardening.sh" -o /tmp/hardening.sh
        source /tmp/hardening.sh
    }

    # Exécuter le hardening
    run_hardening

    log OK "Hardening appliqué"
}

#===============================================================================
# PHASE 3: INSTALLATION DES DÉPENDANCES
#===============================================================================

install_dependencies() {
    log INFO "Phase 3: Installation des dépendances..."

    # Python 3.12
    log INFO "Installation de Python 3.12..."
    if ! command -v python3.12 &> /dev/null; then
        add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
        apt-get update -qq
        apt-get install -y -qq python3.12 python3.12-venv python3.12-dev python3-pip
    fi

    # PostgreSQL 15
    log INFO "Installation de PostgreSQL 15..."
    if ! command -v psql &> /dev/null; then
        curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
            gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg

        echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | \
            tee /etc/apt/sources.list.d/pgdg.list

        apt-get update -qq
        apt-get install -y -qq postgresql-15 postgresql-contrib-15
    fi

    # Redis
    log INFO "Installation de Redis..."
    apt-get install -y -qq redis-server

    # Nginx
    log INFO "Installation de Nginx..."
    apt-get install -y -qq nginx

    # Certbot (si SSL activé)
    if [[ "${ENABLE_SSL}" == "true" ]]; then
        log INFO "Installation de Certbot..."
        apt-get install -y -qq certbot python3-certbot-nginx
    fi

    # Dépendances Python
    log INFO "Installation des dépendances de build..."
    apt-get install -y -qq \
        build-essential \
        libpq-dev \
        libffi-dev \
        libssl-dev

    log OK "Dépendances installées"
}

#===============================================================================
# PHASE 4: CRÉATION DE L'UTILISATEUR
#===============================================================================

create_service_user() {
    log INFO "Phase 4: Création de l'utilisateur système..."

    if id "${SERVICE_USER}" &>/dev/null; then
        log INFO "Utilisateur ${SERVICE_USER} existe déjà"
    else
        groupadd --system "${SERVICE_GROUP}"
        useradd \
            --system \
            --gid "${SERVICE_GROUP}" \
            --home-dir "${INSTALL_DIR}" \
            --shell /usr/sbin/nologin \
            --comment "AZALSCORE Service Account" \
            "${SERVICE_USER}"

        log OK "Utilisateur ${SERVICE_USER} créé"
    fi
}

#===============================================================================
# PHASE 5: TÉLÉCHARGEMENT DE AZALSCORE
#===============================================================================

download_azalscore() {
    log INFO "Phase 5: Téléchargement de AZALSCORE..."

    # Créer le répertoire
    mkdir -p "${INSTALL_DIR}"

    # Cloner le dépôt
    if [[ -d "${INSTALL_DIR}/.git" ]]; then
        log INFO "Mise à jour du dépôt existant..."
        cd "${INSTALL_DIR}"
        git fetch origin
        git reset --hard "origin/${BRANCH}"
    else
        log INFO "Clonage du dépôt..."
        git clone --branch "${BRANCH}" --depth 1 \
            "https://github.com/${GITHUB_REPO}.git" "${INSTALL_DIR}"
    fi

    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}"

    log OK "AZALSCORE téléchargé"
}

#===============================================================================
# PHASE 6: CONFIGURATION POSTGRESQL
#===============================================================================

configure_postgresql() {
    log INFO "Phase 6: Configuration de PostgreSQL..."

    # Démarrer PostgreSQL
    systemctl enable postgresql
    systemctl start postgresql

    # Générer le mot de passe
    local db_password
    db_password=$(openssl rand -hex 24)

    # Créer l'utilisateur et la base
    sudo -u postgres psql -c "DROP USER IF EXISTS azals_user;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER azals_user WITH PASSWORD '${db_password}';"
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS azals;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE azals OWNER azals_user;"
    sudo -u postgres psql -d azals -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    sudo -u postgres psql -d azals -c "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"

    # Sauvegarder le mot de passe pour .env
    echo "${db_password}" > /tmp/.db_password
    chmod 600 /tmp/.db_password

    log OK "PostgreSQL configuré"
}

#===============================================================================
# PHASE 7: CONFIGURATION REDIS
#===============================================================================

configure_redis() {
    log INFO "Phase 7: Configuration de Redis..."

    # Générer le mot de passe Redis
    local redis_password
    redis_password=$(openssl rand -hex 16)

    # Configurer Redis
    cat > /etc/redis/redis.conf.d/azalscore.conf << EOF
# AZALSCORE Redis Configuration
requirepass ${redis_password}
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
EOF

    # Sauvegarder le mot de passe
    echo "${redis_password}" > /tmp/.redis_password
    chmod 600 /tmp/.redis_password

    # Redémarrer Redis
    systemctl enable redis-server
    systemctl restart redis-server

    log OK "Redis configuré"
}

#===============================================================================
# PHASE 8: ENVIRONNEMENT VIRTUEL ET DÉPENDANCES
#===============================================================================

setup_python_env() {
    log INFO "Phase 8: Configuration de l'environnement Python..."

    cd "${INSTALL_DIR}"

    # Créer le venv
    python3.12 -m venv venv
    source venv/bin/activate

    # Mettre à jour pip
    pip install --upgrade pip setuptools wheel --quiet

    # Installer les dépendances
    pip install -r requirements.txt --quiet

    deactivate

    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}/venv"

    log OK "Environnement Python configuré"
}

#===============================================================================
# PHASE 9: GÉNÉRATION DU FICHIER .ENV
#===============================================================================

generate_env_file() {
    log INFO "Phase 9: Génération du fichier .env..."

    local db_password
    db_password=$(cat /tmp/.db_password)
    rm -f /tmp/.db_password

    local redis_password
    redis_password=$(cat /tmp/.redis_password 2>/dev/null || echo "")
    rm -f /tmp/.redis_password

    local secret_key
    secret_key=$(openssl rand -hex 32)

    local bootstrap_secret
    bootstrap_secret=$(openssl rand -hex 32)

    local encryption_key
    encryption_key=$(python3.12 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)

    local cors_origins="http://localhost"
    if [[ -n "${DOMAIN}" ]]; then
        cors_origins="https://${DOMAIN}"
    fi

    cat > "${INSTALL_DIR}/.env" << EOF
#===============================================================================
# AZALSCORE - Configuration Production (OVH)
#===============================================================================
# Généré automatiquement le $(date '+%Y-%m-%d %H:%M:%S')
# CONSERVER CE FICHIER EN LIEU SÛR
#===============================================================================

# Environnement
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Base de données
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=${db_password}
DATABASE_URL=postgresql+psycopg2://azals_user:${db_password}@localhost:5432/azals

# Pool de connexions
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Sécurité
SECRET_KEY=${secret_key}
BOOTSTRAP_SECRET=${bootstrap_secret}
ENCRYPTION_KEY=${encryption_key}

# UUID Security
DB_STRICT_UUID=true
DB_RESET_UUID=false
DB_AUTO_RESET_ON_VIOLATION=false

# CORS
CORS_ORIGINS=${cors_origins}

# Redis
REDIS_URL=redis://:${redis_password}@localhost:6379/0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
AUTH_RATE_LIMIT_PER_MINUTE=5

# API
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=$(nproc)
EOF

    chmod 600 "${INSTALL_DIR}/.env"
    chown "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}/.env"

    log OK "Fichier .env généré"
}

#===============================================================================
# PHASE 10: MIGRATIONS
#===============================================================================

run_migrations() {
    log INFO "Phase 10: Exécution des migrations..."

    cd "${INSTALL_DIR}"
    source venv/bin/activate

    # Charger les variables d'environnement
    set -a
    source .env
    set +a

    # Exécuter les migrations
    alembic upgrade head

    deactivate

    log OK "Migrations appliquées"
}

#===============================================================================
# PHASE 11: SERVICE SYSTEMD
#===============================================================================

setup_systemd() {
    log INFO "Phase 11: Configuration du service systemd..."

    local workers
    workers=$(nproc)

    cat > /etc/systemd/system/azalscore.service << EOF
[Unit]
Description=AZALSCORE ERP API Server
Documentation=https://github.com/${GITHUB_REPO}
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=exec
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${INSTALL_DIR}

Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${INSTALL_DIR}/.env
Environment="AZALS_ENV=prod"
Environment="DEBUG=false"

ExecStart=${INSTALL_DIR}/venv/bin/gunicorn app.main:app \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --workers ${workers} \\
    --bind 127.0.0.1:8000 \\
    --timeout 120 \\
    --access-logfile /var/log/azalscore/access.log \\
    --error-logfile /var/log/azalscore/error.log

ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5

# Sécurité
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${INSTALL_DIR}/logs /var/log/azalscore
ReadOnlyPaths=${INSTALL_DIR}

[Install]
WantedBy=multi-user.target
EOF

    # Créer le répertoire de logs
    mkdir -p /var/log/azalscore
    chown "${SERVICE_USER}:${SERVICE_GROUP}" /var/log/azalscore

    # Logrotate
    cat > /etc/logrotate.d/azalscore << 'EOF'
/var/log/azalscore/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 640 azals azals
    sharedscripts
    postrotate
        systemctl reload azalscore > /dev/null 2>&1 || true
    endscript
}
EOF

    systemctl daemon-reload
    systemctl enable azalscore

    log OK "Service systemd configuré"
}

#===============================================================================
# PHASE 12: CONFIGURATION NGINX
#===============================================================================

setup_nginx() {
    log INFO "Phase 12: Configuration de Nginx..."

    local server_name="_"
    if [[ -n "${DOMAIN}" ]]; then
        server_name="${DOMAIN}"
    fi

    cat > /etc/nginx/sites-available/azalscore << EOF
# AZALSCORE Nginx Configuration

upstream azalscore_api {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name ${server_name};

    # Redirection HTTPS (si SSL activé)
    # return 301 https://\$server_name\$request_uri;

    location / {
        proxy_pass http://azalscore_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://azalscore_api/health;
        access_log off;
    }

    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

    # Activer le site
    rm -f /etc/nginx/sites-enabled/default
    ln -sf /etc/nginx/sites-available/azalscore /etc/nginx/sites-enabled/

    # Tester la configuration
    nginx -t

    systemctl enable nginx
    systemctl restart nginx

    log OK "Nginx configuré"
}

#===============================================================================
# PHASE 13: SSL AVEC LET'S ENCRYPT
#===============================================================================

setup_ssl() {
    if [[ "${ENABLE_SSL}" != "true" ]] || [[ -z "${DOMAIN}" ]]; then
        log INFO "SSL ignoré (pas de domaine ou SSL désactivé)"
        return
    fi

    log INFO "Phase 13: Configuration SSL avec Let's Encrypt..."

    # Obtenir le certificat
    certbot --nginx \
        --non-interactive \
        --agree-tos \
        --email "${EMAIL}" \
        --redirect \
        --hsts \
        --staple-ocsp \
        -d "${DOMAIN}"

    # Configurer le renouvellement automatique
    systemctl enable certbot.timer
    systemctl start certbot.timer

    log OK "SSL configuré"
}

#===============================================================================
# PHASE 14: DÉMARRAGE DES SERVICES
#===============================================================================

start_services() {
    log INFO "Phase 14: Démarrage des services..."

    systemctl start azalscore

    # Vérifier le démarrage
    sleep 3

    if systemctl is-active --quiet azalscore; then
        log OK "AZALSCORE démarré avec succès"
    else
        log ERROR "Échec du démarrage de AZALSCORE"
        journalctl -u azalscore --no-pager -n 20
        exit 1
    fi
}

#===============================================================================
# PHASE 15: RÉSUMÉ FINAL
#===============================================================================

print_summary() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}   AZALSCORE - Installation terminée avec succès!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    echo -e "${BOLD}Accès:${NC}"
    if [[ -n "${DOMAIN}" ]] && [[ "${ENABLE_SSL}" == "true" ]]; then
        echo "  URL: https://${DOMAIN}"
    elif [[ -n "${DOMAIN}" ]]; then
        echo "  URL: http://${DOMAIN}"
    else
        local ip
        ip=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
        echo "  URL: http://${ip}"
    fi
    echo ""

    echo -e "${BOLD}Fichiers importants:${NC}"
    echo "  Configuration:  ${INSTALL_DIR}/.env"
    echo "  Logs:           /var/log/azalscore/"
    echo "  Installation:   /var/log/azalscore-install.log"
    echo ""

    echo -e "${BOLD}Commandes utiles:${NC}"
    echo "  Statut:       sudo systemctl status azalscore"
    echo "  Logs:         sudo journalctl -u azalscore -f"
    echo "  Redémarrer:   sudo systemctl restart azalscore"
    echo ""

    echo -e "${BOLD}Sécurité:${NC}"
    echo "  1. Conservez une copie sécurisée de ${INSTALL_DIR}/.env"
    echo "  2. Configurez les sauvegardes automatiques"
    echo "  3. Surveillez les logs de sécurité"
    echo ""
}

#===============================================================================
# POINT D'ENTRÉE
#===============================================================================

main() {
    # Initialiser le log
    mkdir -p /var/log
    : > /var/log/azalscore-install.log

    print_banner
    check_root
    check_os
    get_user_input

    prepare_system
    apply_hardening
    install_dependencies
    create_service_user
    download_azalscore
    configure_postgresql
    configure_redis
    setup_python_env
    generate_env_file
    run_migrations
    setup_systemd
    setup_nginx
    setup_ssl
    start_services
    print_summary
}

# Exécution
main "$@"
