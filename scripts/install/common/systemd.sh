#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Configuration systemd
#===============================================================================
# Ce module configure le service systemd pour la production
#===============================================================================

#===============================================================================
# VARIABLES
#===============================================================================

readonly SERVICE_NAME="azalscore"
readonly SERVICE_USER="azals"
readonly SERVICE_GROUP="azals"
readonly INSTALL_DIR="/opt/azalscore"

#===============================================================================
# CONFIGURATION SYSTEMD
#===============================================================================

setup_systemd() {
    log INFO "Configuration du service systemd..."

    if [[ "${OS_TYPE}" != "linux" ]]; then
        log WARN "systemd non disponible sur ${OS_TYPE}"
        return
    fi

    # Créer l'utilisateur système
    create_service_user

    # Créer le fichier de service
    create_service_file

    # Configurer les permissions
    setup_service_permissions

    # Activer et démarrer le service
    enable_service

    log OK "Service systemd configuré"
}

#===============================================================================
# CRÉATION UTILISATEUR SYSTÈME
#===============================================================================

create_service_user() {
    log INFO "Création de l'utilisateur système ${SERVICE_USER}..."

    # Vérifier si l'utilisateur existe
    if id "${SERVICE_USER}" &>/dev/null; then
        log INFO "Utilisateur ${SERVICE_USER} existe déjà"
        return
    fi

    # Créer le groupe
    sudo groupadd --system "${SERVICE_GROUP}" 2>/dev/null || true

    # Créer l'utilisateur
    sudo useradd \
        --system \
        --gid "${SERVICE_GROUP}" \
        --home-dir "${INSTALL_DIR}" \
        --shell /usr/sbin/nologin \
        --comment "AZALSCORE Service Account" \
        "${SERVICE_USER}"

    log OK "Utilisateur ${SERVICE_USER} créé"
}

#===============================================================================
# FICHIER DE SERVICE
#===============================================================================

create_service_file() {
    log INFO "Création du fichier de service systemd..."

    local service_file="/etc/systemd/system/${SERVICE_NAME}.service"
    local env_file="${PROJECT_ROOT}/.env"
    local venv_python="${PROJECT_ROOT}/venv/bin/python"
    local workers="${CPU_CORES:-4}"

    sudo tee "${service_file}" > /dev/null << EOF
[Unit]
Description=AZALSCORE ERP API Server
Documentation=https://github.com/MASITH-developpement/Azalscore
After=network.target postgresql.service
Wants=postgresql.service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=exec
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${PROJECT_ROOT}

# Environnement
Environment="PATH=${PROJECT_ROOT}/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${env_file}

# Sécurité renforcée
Environment="AZALS_ENV=prod"
Environment="DEBUG=false"
Environment="DB_STRICT_UUID=true"
Environment="DB_AUTO_RESET_ON_VIOLATION=false"
Environment="DB_RESET_UUID=false"

# Commande de démarrage
ExecStart=${PROJECT_ROOT}/venv/bin/gunicorn app.main:app \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --workers ${workers} \\
    --threads 2 \\
    --bind 127.0.0.1:8000 \\
    --timeout 120 \\
    --keep-alive 5 \\
    --graceful-timeout 30 \\
    --access-logfile /var/log/azalscore/access.log \\
    --error-logfile /var/log/azalscore/error.log \\
    --capture-output

# Rechargement gracieux
ExecReload=/bin/kill -s HUP \$MAINPID

# Arrêt
ExecStop=/bin/kill -s TERM \$MAINPID
TimeoutStopSec=30

# Redémarrage automatique
Restart=always
RestartSec=5

# Limites de ressources
LimitNOFILE=65536
LimitNPROC=4096

# Sécurité systemd
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${PROJECT_ROOT}/logs /var/log/azalscore
ReadOnlyPaths=${PROJECT_ROOT}

# Sandboxing
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes

# Réseau
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
EOF

    log OK "Fichier de service créé: ${service_file}"

    # Créer le répertoire de logs
    sudo mkdir -p /var/log/azalscore
    sudo chown "${SERVICE_USER}:${SERVICE_GROUP}" /var/log/azalscore
    sudo chmod 755 /var/log/azalscore

    # Créer la configuration logrotate
    create_logrotate_config
}

#===============================================================================
# LOGROTATE
#===============================================================================

create_logrotate_config() {
    log INFO "Configuration de la rotation des logs..."

    local logrotate_file="/etc/logrotate.d/${SERVICE_NAME}"

    sudo tee "${logrotate_file}" > /dev/null << 'EOF'
/var/log/azalscore/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 azals azals
    sharedscripts
    postrotate
        systemctl reload azalscore > /dev/null 2>&1 || true
    endscript
}
EOF

    log OK "Configuration logrotate créée"
}

#===============================================================================
# PERMISSIONS
#===============================================================================

setup_service_permissions() {
    log INFO "Configuration des permissions..."

    # Propriétaire du projet
    sudo chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${PROJECT_ROOT}"

    # Permissions des répertoires
    sudo chmod 755 "${PROJECT_ROOT}"
    sudo chmod -R 755 "${PROJECT_ROOT}/app"
    sudo chmod -R 755 "${PROJECT_ROOT}/venv"

    # Fichier .env sécurisé
    sudo chmod 600 "${PROJECT_ROOT}/.env"

    # Répertoire de logs
    mkdir -p "${PROJECT_ROOT}/logs"
    sudo chown "${SERVICE_USER}:${SERVICE_GROUP}" "${PROJECT_ROOT}/logs"
    sudo chmod 755 "${PROJECT_ROOT}/logs"

    log OK "Permissions configurées"
}

#===============================================================================
# ACTIVATION DU SERVICE
#===============================================================================

enable_service() {
    log INFO "Activation du service systemd..."

    # Recharger la configuration systemd
    sudo systemctl daemon-reload

    # Activer le démarrage automatique
    sudo systemctl enable "${SERVICE_NAME}"

    # Demander si on démarre maintenant
    if [[ "${INTERACTIVE}" == "true" ]]; then
        echo ""
        read -rp "Démarrer le service maintenant? [Y/n] " response
        if [[ ! "${response,,}" =~ ^(n|no)$ ]]; then
            start_service
        fi
    fi

    log OK "Service ${SERVICE_NAME} activé"
}

start_service() {
    log INFO "Démarrage du service..."

    sudo systemctl start "${SERVICE_NAME}"

    # Vérifier le statut
    sleep 2

    if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
        log OK "Service ${SERVICE_NAME} démarré avec succès"

        # Afficher les informations
        echo ""
        echo -e "${BOLD}Statut du service:${NC}"
        sudo systemctl status "${SERVICE_NAME}" --no-pager | head -15
        echo ""
    else
        log ERROR "Échec du démarrage du service"
        echo ""
        echo -e "${BOLD}Logs d'erreur:${NC}"
        sudo journalctl -u "${SERVICE_NAME}" --no-pager -n 20
        echo ""
    fi
}

#===============================================================================
# COMMANDES DE GESTION
#===============================================================================

print_service_commands() {
    echo ""
    echo -e "${BOLD}Commandes de gestion du service:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Démarrer:     sudo systemctl start ${SERVICE_NAME}"
    echo "  Arrêter:      sudo systemctl stop ${SERVICE_NAME}"
    echo "  Redémarrer:   sudo systemctl restart ${SERVICE_NAME}"
    echo "  Recharger:    sudo systemctl reload ${SERVICE_NAME}"
    echo "  Statut:       sudo systemctl status ${SERVICE_NAME}"
    echo "  Logs:         sudo journalctl -u ${SERVICE_NAME} -f"
    echo ""
    echo "  Logs accès:   tail -f /var/log/azalscore/access.log"
    echo "  Logs erreurs: tail -f /var/log/azalscore/error.log"
    echo ""
}

#===============================================================================
# SERVICE SOCKET (optionnel)
#===============================================================================

create_socket_service() {
    # Configuration optionnelle avec socket activation
    # Permet un démarrage plus rapide et une meilleure gestion des connexions

    local socket_file="/etc/systemd/system/${SERVICE_NAME}.socket"

    sudo tee "${socket_file}" > /dev/null << EOF
[Unit]
Description=AZALSCORE API Socket
PartOf=${SERVICE_NAME}.service

[Socket]
ListenStream=127.0.0.1:8000
NoDelay=true
ReusePort=true

[Install]
WantedBy=sockets.target
EOF

    log INFO "Socket systemd créé (optionnel)"
}

#===============================================================================
# TIMER POUR TÂCHES PLANIFIÉES
#===============================================================================

create_maintenance_timer() {
    log INFO "Création du timer de maintenance..."

    # Service de maintenance
    local maintenance_service="/etc/systemd/system/${SERVICE_NAME}-maintenance.service"

    sudo tee "${maintenance_service}" > /dev/null << EOF
[Unit]
Description=AZALSCORE Maintenance Tasks
After=postgresql.service

[Service]
Type=oneshot
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${PROJECT_ROOT}
Environment="PATH=${PROJECT_ROOT}/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${PROJECT_ROOT}/.env
ExecStart=${PROJECT_ROOT}/venv/bin/python -m app.tasks.maintenance
EOF

    # Timer pour exécution quotidienne
    local maintenance_timer="/etc/systemd/system/${SERVICE_NAME}-maintenance.timer"

    sudo tee "${maintenance_timer}" > /dev/null << EOF
[Unit]
Description=AZALSCORE Daily Maintenance

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable "${SERVICE_NAME}-maintenance.timer" 2>/dev/null || true

    log OK "Timer de maintenance créé"
}
