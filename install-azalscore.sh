#!/bin/bash
#===============================================================================
# AZALSCORE - Script d'installation serveur OVH
# Version: 1.0.0
# Cible: Ubuntu 22.04 LTS
# Usage: sudo bash install-azalscore.sh
#===============================================================================

set -e  # Arrêt immédiat en cas d'erreur

#-------------------------------------------------------------------------------
# Variables
#-------------------------------------------------------------------------------
AZALSCORE_DIR="/home/ubuntu/azalscore"
AZALSCORE_USER="ubuntu"
LOG_FILE="/var/log/azalscore-install.log"

#-------------------------------------------------------------------------------
# Fonctions utilitaires
#-------------------------------------------------------------------------------
log_info() {
    echo -e "\n\033[1;34m[INFO]\033[0m $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "\033[1;32m[OK]\033[0m $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "\033[1;33m[WARN]\033[0m $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_FILE"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté avec sudo"
        exit 1
    fi
}

#-------------------------------------------------------------------------------
# Étape 1: Mise à jour et sécurisation du système
#-------------------------------------------------------------------------------
setup_system() {
    log_info "=== ÉTAPE 1: Mise à jour et sécurisation du système ==="

    # Mise à jour des paquets
    log_info "Mise à jour des paquets système..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get upgrade -y
    log_success "Système mis à jour"

    # Installation des paquets essentiels
    log_info "Installation des paquets essentiels..."
    apt-get install -y \
        curl \
        git \
        ufw \
        ca-certificates \
        gnupg \
        lsb-release \
        wget \
        apt-transport-https \
        software-properties-common
    log_success "Paquets essentiels installés"
}

#-------------------------------------------------------------------------------
# Étape 2: Configuration du pare-feu UFW
#-------------------------------------------------------------------------------
setup_firewall() {
    log_info "=== ÉTAPE 2: Configuration du pare-feu UFW ==="

    # Réinitialisation UFW si déjà configuré
    if ufw status | grep -q "active"; then
        log_warning "UFW déjà actif, vérification de la configuration..."
    fi

    # Configuration des règles
    log_info "Configuration des règles UFW..."
    ufw default deny incoming
    ufw default allow outgoing

    # Autoriser SSH (critique - à faire en premier)
    ufw allow 22/tcp comment 'SSH'

    # Autoriser HTTP et HTTPS
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'

    # Activer UFW sans prompt
    echo "y" | ufw enable

    log_success "Pare-feu UFW configuré et activé"
    ufw status verbose
}

#-------------------------------------------------------------------------------
# Étape 3: Sécurisation SSH
#-------------------------------------------------------------------------------
secure_ssh() {
    log_info "=== ÉTAPE 3: Sécurisation SSH ==="

    SSH_CONFIG="/etc/ssh/sshd_config"
    RESTART_SSH=false

    # Vérifier et désactiver PasswordAuthentication
    if grep -q "^PasswordAuthentication yes" "$SSH_CONFIG"; then
        log_info "Désactivation de PasswordAuthentication..."
        sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' "$SSH_CONFIG"
        RESTART_SSH=true
    elif grep -q "^#PasswordAuthentication" "$SSH_CONFIG"; then
        log_info "Configuration de PasswordAuthentication..."
        sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' "$SSH_CONFIG"
        RESTART_SSH=true
    elif ! grep -q "^PasswordAuthentication no" "$SSH_CONFIG"; then
        echo "PasswordAuthentication no" >> "$SSH_CONFIG"
        RESTART_SSH=true
    fi

    # Désactiver l'authentification root par mot de passe
    if grep -q "^PermitRootLogin yes" "$SSH_CONFIG"; then
        sed -i 's/^PermitRootLogin yes/PermitRootLogin prohibit-password/' "$SSH_CONFIG"
        RESTART_SSH=true
    fi

    # Redémarrer SSH si nécessaire
    if [ "$RESTART_SSH" = true ]; then
        log_info "Redémarrage du service SSH..."
        systemctl restart sshd
        log_success "Service SSH redémarré"
    else
        log_success "Configuration SSH déjà sécurisée"
    fi
}

#-------------------------------------------------------------------------------
# Étape 4: Installation Docker (méthode officielle)
#-------------------------------------------------------------------------------
install_docker() {
    log_info "=== ÉTAPE 4: Installation de Docker ==="

    # Vérifier si Docker est déjà installé
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        log_warning "Docker déjà installé: $DOCKER_VERSION"
        log_info "Vérification des mises à jour..."
    fi

    # Supprimer les anciennes versions
    log_info "Suppression des anciennes versions Docker..."
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Ajouter la clé GPG officielle Docker
    log_info "Ajout de la clé GPG Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Ajouter le dépôt Docker
    log_info "Ajout du dépôt Docker..."
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Installation de Docker
    log_info "Installation des paquets Docker..."
    apt-get update -y
    apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    # Ajouter l'utilisateur ubuntu au groupe docker
    log_info "Ajout de l'utilisateur ubuntu au groupe docker..."
    usermod -aG docker "$AZALSCORE_USER"

    # Activer et démarrer Docker
    systemctl enable docker
    systemctl start docker

    log_success "Docker installé avec succès"
    docker --version
    docker compose version

    log_warning "IMPORTANT: Une reconnexion SSH est nécessaire pour utiliser docker sans sudo"
}

#-------------------------------------------------------------------------------
# Étape 5: Création de l'arborescence AZALSCORE
#-------------------------------------------------------------------------------
create_directory_structure() {
    log_info "=== ÉTAPE 5: Création de l'arborescence AZALSCORE ==="

    # Créer le répertoire principal
    log_info "Création de la structure de répertoires..."

    mkdir -p "$AZALSCORE_DIR"/{app,nginx,data,logs,scripts}

    # Définir les permissions
    chown -R "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR"
    chmod -R 755 "$AZALSCORE_DIR"

    # Créer un fichier .gitkeep dans chaque répertoire
    for dir in app nginx data logs scripts; do
        touch "$AZALSCORE_DIR/$dir/.gitkeep"
    done

    log_success "Arborescence créée:"
    tree "$AZALSCORE_DIR" 2>/dev/null || ls -la "$AZALSCORE_DIR"
}

#-------------------------------------------------------------------------------
# Étape 6: Installation Node.js LTS
#-------------------------------------------------------------------------------
install_nodejs() {
    log_info "=== ÉTAPE 6: Installation de Node.js LTS ==="

    # Vérifier si Node.js est déjà installé
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_warning "Node.js déjà installé: $NODE_VERSION"
    fi

    # Installation via NodeSource (Node.js 20 LTS)
    log_info "Installation de Node.js 20 LTS via NodeSource..."

    # Supprimer l'ancienne configuration NodeSource si elle existe
    rm -f /etc/apt/sources.list.d/nodesource.list
    rm -f /etc/apt/keyrings/nodesource.gpg

    # Télécharger et exécuter le script d'installation NodeSource
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -

    # Installer Node.js
    apt-get install -y nodejs

    # Vérifier l'installation
    log_success "Node.js installé:"
    node --version
    npm --version

    # Configurer npm pour l'utilisateur ubuntu (éviter les problèmes de permissions)
    log_info "Configuration de npm pour l'utilisateur ubuntu..."
    sudo -u "$AZALSCORE_USER" mkdir -p "/home/$AZALSCORE_USER/.npm-global"
    sudo -u "$AZALSCORE_USER" npm config set prefix "/home/$AZALSCORE_USER/.npm-global"

    # Ajouter au PATH dans .bashrc si pas déjà présent
    BASHRC="/home/$AZALSCORE_USER/.bashrc"
    if ! grep -q ".npm-global/bin" "$BASHRC"; then
        echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> "$BASHRC"
    fi

    log_success "Node.js LTS configuré"
}

#-------------------------------------------------------------------------------
# Étape 7: Installation de Claude Code CLI
#-------------------------------------------------------------------------------
install_claude_code() {
    log_info "=== ÉTAPE 7: Installation de Claude Code CLI ==="

    # Installer Claude Code globalement via npm
    log_info "Installation de Claude Code CLI..."
    npm install -g @anthropic-ai/claude-code

    # Vérifier l'installation
    if command -v claude &> /dev/null; then
        log_success "Claude Code CLI installé avec succès"
        claude --version 2>/dev/null || echo "Claude Code installé"
    else
        # Essayer via le chemin npm global de l'utilisateur
        log_info "Tentative d'installation pour l'utilisateur ubuntu..."
        sudo -u "$AZALSCORE_USER" bash -c 'export PATH="$HOME/.npm-global/bin:$PATH" && npm install -g @anthropic-ai/claude-code'
    fi

    # Créer un script de démarrage pour Claude Code
    log_info "Création du script de démarrage Claude Code..."
    cat > "$AZALSCORE_DIR/scripts/start-claude.sh" << 'EOF'
#!/bin/bash
# Script de démarrage Claude Code pour AZALSCORE
cd /home/ubuntu/azalscore
export PATH="$HOME/.npm-global/bin:$PATH"
claude
EOF
    chmod +x "$AZALSCORE_DIR/scripts/start-claude.sh"
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/scripts/start-claude.sh"

    log_success "Claude Code CLI configuré"
}

#-------------------------------------------------------------------------------
# Étape 8: Configuration du démarrage automatique
#-------------------------------------------------------------------------------
setup_autostart() {
    log_info "=== ÉTAPE 8: Configuration du démarrage automatique ==="

    # Créer le script de démarrage AZALSCORE
    log_info "Création du script de démarrage AZALSCORE..."
    cat > "$AZALSCORE_DIR/scripts/start-azalscore.sh" << 'EOF'
#!/bin/bash
# Script de démarrage AZALSCORE
set -e

AZALSCORE_DIR="/home/ubuntu/azalscore"
LOG_FILE="$AZALSCORE_DIR/logs/startup.log"

echo "[$(date)] Démarrage AZALSCORE..." >> "$LOG_FILE"

cd "$AZALSCORE_DIR"

# Vérifier que docker-compose.yml existe
if [ -f "$AZALSCORE_DIR/docker-compose.yml" ] || [ -f "$AZALSCORE_DIR/docker-compose.prod.yml" ]; then
    COMPOSE_FILE=""
    if [ -f "$AZALSCORE_DIR/docker-compose.prod.yml" ]; then
        COMPOSE_FILE="$AZALSCORE_DIR/docker-compose.prod.yml"
    else
        COMPOSE_FILE="$AZALSCORE_DIR/docker-compose.yml"
    fi

    echo "[$(date)] Utilisation de: $COMPOSE_FILE" >> "$LOG_FILE"
    docker compose -f "$COMPOSE_FILE" up -d >> "$LOG_FILE" 2>&1
    echo "[$(date)] AZALSCORE démarré avec succès" >> "$LOG_FILE"
else
    echo "[$(date)] ATTENTION: Aucun fichier docker-compose trouvé" >> "$LOG_FILE"
fi
EOF
    chmod +x "$AZALSCORE_DIR/scripts/start-azalscore.sh"
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/scripts/start-azalscore.sh"

    # Créer le script d'arrêt AZALSCORE
    log_info "Création du script d'arrêt AZALSCORE..."
    cat > "$AZALSCORE_DIR/scripts/stop-azalscore.sh" << 'EOF'
#!/bin/bash
# Script d'arrêt AZALSCORE
set -e

AZALSCORE_DIR="/home/ubuntu/azalscore"
LOG_FILE="$AZALSCORE_DIR/logs/startup.log"

echo "[$(date)] Arrêt AZALSCORE..." >> "$LOG_FILE"

cd "$AZALSCORE_DIR"

if [ -f "$AZALSCORE_DIR/docker-compose.prod.yml" ]; then
    docker compose -f "$AZALSCORE_DIR/docker-compose.prod.yml" down >> "$LOG_FILE" 2>&1
elif [ -f "$AZALSCORE_DIR/docker-compose.yml" ]; then
    docker compose -f "$AZALSCORE_DIR/docker-compose.yml" down >> "$LOG_FILE" 2>&1
fi

echo "[$(date)] AZALSCORE arrêté" >> "$LOG_FILE"
EOF
    chmod +x "$AZALSCORE_DIR/scripts/stop-azalscore.sh"
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/scripts/stop-azalscore.sh"

    # Créer le script de restart AZALSCORE
    log_info "Création du script de restart AZALSCORE..."
    cat > "$AZALSCORE_DIR/scripts/restart-azalscore.sh" << 'EOF'
#!/bin/bash
# Script de restart AZALSCORE
/home/ubuntu/azalscore/scripts/stop-azalscore.sh
sleep 2
/home/ubuntu/azalscore/scripts/start-azalscore.sh
EOF
    chmod +x "$AZALSCORE_DIR/scripts/restart-azalscore.sh"
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/scripts/restart-azalscore.sh"

    # Créer le service systemd AZALSCORE
    log_info "Création du service systemd AZALSCORE..."
    cat > /etc/systemd/system/azalscore.service << 'EOF'
[Unit]
Description=AZALSCORE Application
Documentation=https://github.com/your-repo/azalscore
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/azalscore
ExecStart=/home/ubuntu/azalscore/scripts/start-azalscore.sh
ExecStop=/home/ubuntu/azalscore/scripts/stop-azalscore.sh
ExecReload=/home/ubuntu/azalscore/scripts/restart-azalscore.sh
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

    # Recharger systemd et activer le service
    log_info "Activation du service AZALSCORE au démarrage..."
    systemctl daemon-reload
    systemctl enable azalscore.service

    log_success "Service AZALSCORE configuré pour démarrage automatique"

    # Créer un script de status
    log_info "Création du script de status..."
    cat > "$AZALSCORE_DIR/scripts/status-azalscore.sh" << 'EOF'
#!/bin/bash
# Script de status AZALSCORE
echo "=== Status Service AZALSCORE ==="
systemctl status azalscore.service --no-pager
echo ""
echo "=== Conteneurs Docker ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Logs récents ==="
tail -20 /home/ubuntu/azalscore/logs/startup.log 2>/dev/null || echo "Pas de logs disponibles"
EOF
    chmod +x "$AZALSCORE_DIR/scripts/status-azalscore.sh"
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/scripts/status-azalscore.sh"

    log_success "Scripts de gestion créés"
}

#-------------------------------------------------------------------------------
# Étape 9: Configuration finale
#-------------------------------------------------------------------------------
final_setup() {
    log_info "=== ÉTAPE 9: Configuration finale ==="

    # Créer un fichier de configuration AZALSCORE
    log_info "Création du fichier de configuration..."
    cat > "$AZALSCORE_DIR/.env.example" << 'EOF'
# AZALSCORE Configuration
# Copier ce fichier vers .env et remplir les valeurs

# Application
APP_ENV=production
APP_DEBUG=false
APP_URL=https://votre-domaine.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/azalscore

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
ANTHROPIC_API_KEY=your-api-key-here

# Security
SECRET_KEY=change-this-to-a-secure-random-string
EOF
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/.env.example"

    # Créer un script de vérification de santé
    log_info "Création du script de vérification..."
    cat > "$AZALSCORE_DIR/scripts/health-check.sh" << 'EOF'
#!/bin/bash
echo "=== AZALSCORE Health Check ==="
echo ""
echo "1. Docker:"
docker --version 2>/dev/null && echo "   Status: OK" || echo "   Status: ERREUR"
echo ""
echo "2. Docker Compose:"
docker compose version 2>/dev/null && echo "   Status: OK" || echo "   Status: ERREUR"
echo ""
echo "3. Node.js:"
node --version 2>/dev/null && echo "   Status: OK" || echo "   Status: ERREUR"
echo ""
echo "4. npm:"
npm --version 2>/dev/null && echo "   Status: OK" || echo "   Status: ERREUR"
echo ""
echo "5. Claude Code:"
export PATH="$HOME/.npm-global/bin:$PATH"
which claude &>/dev/null && echo "   Status: OK" || echo "   Status: Non trouvé (vérifiez le PATH)"
echo ""
echo "6. Firewall (UFW):"
sudo ufw status | head -5
echo ""
echo "7. Espace disque:"
df -h / | tail -1
echo ""
echo "8. Mémoire:"
free -h | head -2
echo ""
echo "=== Fin du Health Check ==="
EOF
    chmod +x "$AZALSCORE_DIR/scripts/health-check.sh"
    chown "$AZALSCORE_USER":"$AZALSCORE_USER" "$AZALSCORE_DIR/scripts/health-check.sh"

    log_success "Configuration finale terminée"
}

#-------------------------------------------------------------------------------
# Résumé de l'installation
#-------------------------------------------------------------------------------
print_summary() {
    echo ""
    echo "==============================================================================="
    echo -e "\033[1;32m INSTALLATION AZALSCORE TERMINÉE AVEC SUCCÈS \033[0m"
    echo "==============================================================================="
    echo ""
    echo "Récapitulatif:"
    echo "  - Système: Ubuntu 22.04 LTS mis à jour et sécurisé"
    echo "  - Pare-feu: UFW activé (ports 22, 80, 443)"
    echo "  - Docker: Installé avec docker-compose-plugin"
    echo "  - Node.js: Version LTS installée"
    echo "  - Claude Code: CLI installé"
    echo "  - Service systemd: azalscore.service activé (démarrage auto)"
    echo ""
    echo "Répertoire AZALSCORE: $AZALSCORE_DIR"
    echo ""
    echo "Scripts de gestion disponibles:"
    echo "  - ~/azalscore/scripts/start-azalscore.sh   : Démarrer l'application"
    echo "  - ~/azalscore/scripts/stop-azalscore.sh    : Arrêter l'application"
    echo "  - ~/azalscore/scripts/restart-azalscore.sh : Redémarrer l'application"
    echo "  - ~/azalscore/scripts/status-azalscore.sh  : Voir le status"
    echo ""
    echo "Commandes systemctl:"
    echo "  - sudo systemctl start azalscore    : Démarrer"
    echo "  - sudo systemctl stop azalscore     : Arrêter"
    echo "  - sudo systemctl restart azalscore  : Redémarrer"
    echo "  - sudo systemctl status azalscore   : Status"
    echo ""
    echo "==============================================================================="
    echo -e "\033[1;33m ACTIONS REQUISES \033[0m"
    echo "==============================================================================="
    echo ""
    echo "1. DÉCONNECTEZ-VOUS et RECONNECTEZ-VOUS en SSH pour appliquer les"
    echo "   permissions Docker:"
    echo ""
    echo "   exit"
    echo "   ssh ubuntu@57.128.7.20"
    echo ""
    echo "2. Vérifiez l'installation avec:"
    echo ""
    echo "   ~/azalscore/scripts/health-check.sh"
    echo ""
    echo "3. Pour lancer Claude Code sur le serveur:"
    echo ""
    echo "   cd ~/azalscore && claude"
    echo "   # OU"
    echo "   ~/azalscore/scripts/start-claude.sh"
    echo ""
    echo "4. N'oubliez pas de configurer votre clé API Anthropic:"
    echo ""
    echo "   export ANTHROPIC_API_KEY='votre-clé-api'"
    echo ""
    echo "==============================================================================="
    echo "Log d'installation: $LOG_FILE"
    echo "==============================================================================="
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------
main() {
    echo ""
    echo "==============================================================================="
    echo " AZALSCORE - Installation Serveur OVH"
    echo " $(date)"
    echo "==============================================================================="
    echo ""

    # Vérification des droits root
    check_root

    # Créer le fichier de log
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"

    # Exécution des étapes
    setup_system
    setup_firewall
    secure_ssh
    install_docker
    create_directory_structure
    install_nodejs
    install_claude_code
    setup_autostart
    final_setup

    # Afficher le résumé
    print_summary
}

# Exécution
main "$@"
