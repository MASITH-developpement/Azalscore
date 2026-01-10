#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Installation et configuration PostgreSQL
#===============================================================================
# Ce module installe et configure PostgreSQL de manière sécurisée
#===============================================================================

#===============================================================================
# VARIABLES
#===============================================================================

readonly PG_VERSION="15"
readonly PG_DB_NAME="azals"
readonly PG_USER_NAME="azals_user"

#===============================================================================
# INSTALLATION POSTGRESQL
#===============================================================================

setup_postgres() {
    log INFO "Configuration de PostgreSQL..."

    if [[ "${POSTGRES_LOCAL}" == "false" ]]; then
        log INFO "Utilisation d'une instance PostgreSQL existante"
        verify_postgres_connection
        return
    fi

    case "${DISTRO}" in
        debian|ubuntu|linuxmint|pop)
            install_postgres_debian
            ;;
        fedora|centos|rhel|rocky|almalinux)
            install_postgres_fedora
            ;;
        arch|manjaro)
            install_postgres_arch
            ;;
        macos)
            install_postgres_macos
            ;;
        *)
            log WARN "Installation automatique PostgreSQL non supportée pour ${DISTRO}"
            log INFO "Veuillez installer PostgreSQL ${PG_VERSION}+ manuellement"
            return
            ;;
    esac

    configure_postgres
    create_database_and_user
}

install_postgres_debian() {
    log INFO "Installation de PostgreSQL sur Debian/Ubuntu..."

    # Ajouter le dépôt officiel PostgreSQL
    if [[ ! -f /etc/apt/sources.list.d/pgdg.list ]]; then
        log INFO "Ajout du dépôt PostgreSQL officiel..."

        sudo apt-get install -y -qq curl ca-certificates gnupg

        # Importer la clé GPG
        curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
            sudo gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg

        # Ajouter le dépôt
        echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | \
            sudo tee /etc/apt/sources.list.d/pgdg.list

        sudo apt-get update -qq
    fi

    # Installer PostgreSQL
    sudo apt-get install -y -qq postgresql-${PG_VERSION} postgresql-contrib-${PG_VERSION}

    # Démarrer le service
    sudo systemctl enable postgresql
    sudo systemctl start postgresql

    log OK "PostgreSQL ${PG_VERSION} installé"
}

install_postgres_fedora() {
    log INFO "Installation de PostgreSQL sur Fedora/RHEL..."

    # Installer PostgreSQL
    sudo dnf install -y -q postgresql${PG_VERSION}-server postgresql${PG_VERSION}-contrib

    # Initialiser la base de données
    if [[ ! -d /var/lib/pgsql/${PG_VERSION}/data/base ]]; then
        sudo /usr/pgsql-${PG_VERSION}/bin/postgresql-${PG_VERSION}-setup initdb
    fi

    # Démarrer le service
    sudo systemctl enable postgresql-${PG_VERSION}
    sudo systemctl start postgresql-${PG_VERSION}

    log OK "PostgreSQL ${PG_VERSION} installé"
}

install_postgres_arch() {
    log INFO "Installation de PostgreSQL sur Arch Linux..."

    sudo pacman -Sy --noconfirm postgresql

    # Initialiser la base de données
    if [[ ! -d /var/lib/postgres/data/base ]]; then
        sudo -u postgres initdb -D /var/lib/postgres/data
    fi

    # Démarrer le service
    sudo systemctl enable postgresql
    sudo systemctl start postgresql

    log OK "PostgreSQL installé"
}

install_postgres_macos() {
    log INFO "Installation de PostgreSQL sur macOS..."

    # Installer via Homebrew
    brew install postgresql@${PG_VERSION}

    # Démarrer le service
    brew services start postgresql@${PG_VERSION}

    # Ajouter au PATH
    if [[ -d "/opt/homebrew/opt/postgresql@${PG_VERSION}/bin" ]]; then
        export PATH="/opt/homebrew/opt/postgresql@${PG_VERSION}/bin:$PATH"
    elif [[ -d "/usr/local/opt/postgresql@${PG_VERSION}/bin" ]]; then
        export PATH="/usr/local/opt/postgresql@${PG_VERSION}/bin:$PATH"
    fi

    log OK "PostgreSQL ${PG_VERSION} installé"
}

#===============================================================================
# CONFIGURATION POSTGRESQL
#===============================================================================

configure_postgres() {
    log INFO "Configuration de PostgreSQL..."

    # Trouver le répertoire de configuration
    local pg_conf=""
    local pg_hba=""

    if [[ "${OS_TYPE}" == "darwin" ]]; then
        pg_conf="$(brew --prefix)/var/postgresql@${PG_VERSION}/postgresql.conf"
        pg_hba="$(brew --prefix)/var/postgresql@${PG_VERSION}/pg_hba.conf"
    else
        # Linux - trouver le chemin
        for path in \
            "/etc/postgresql/${PG_VERSION}/main" \
            "/var/lib/pgsql/${PG_VERSION}/data" \
            "/var/lib/postgres/data"; do
            if [[ -f "${path}/postgresql.conf" ]]; then
                pg_conf="${path}/postgresql.conf"
                pg_hba="${path}/pg_hba.conf"
                break
            fi
        done
    fi

    if [[ -z "${pg_conf}" ]] || [[ ! -f "${pg_conf}" ]]; then
        log WARN "Fichier postgresql.conf non trouvé"
        return
    fi

    # Backup des fichiers de configuration
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        sudo cp "${pg_conf}" "${pg_conf}.backup.$(date +%Y%m%d)"
        sudo cp "${pg_hba}" "${pg_hba}.backup.$(date +%Y%m%d)"
    fi

    # Configuration production
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        log INFO "Application des paramètres de production..."

        # Créer un fichier de configuration personnalisé
        local custom_conf
        custom_conf=$(dirname "${pg_conf}")/conf.d/azalscore.conf

        sudo mkdir -p "$(dirname "${custom_conf}")"

        sudo tee "${custom_conf}" > /dev/null << EOF
# AZALSCORE - Configuration PostgreSQL Production
# Généré le $(date '+%Y-%m-%d %H:%M:%S')

# Connexions
listen_addresses = 'localhost'
max_connections = 100

# Mémoire (ajuster selon RAM disponible)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB

# WAL et durabilité
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Sécurité
password_encryption = scram-sha-256
ssl = on
EOF

        # Activer l'inclusion du fichier personnalisé
        if ! grep -q "include_dir = 'conf.d'" "${pg_conf}" 2>/dev/null; then
            echo "include_dir = 'conf.d'" | sudo tee -a "${pg_conf}" > /dev/null
        fi
    fi

    # Redémarrer PostgreSQL pour appliquer les changements
    if [[ "${OS_TYPE}" == "darwin" ]]; then
        brew services restart postgresql@${PG_VERSION}
    else
        sudo systemctl restart postgresql 2>/dev/null || \
        sudo systemctl restart postgresql-${PG_VERSION} 2>/dev/null || true
    fi

    # Attendre que PostgreSQL soit prêt
    sleep 2

    log OK "PostgreSQL configuré"
}

#===============================================================================
# CRÉATION BASE DE DONNÉES ET UTILISATEUR
#===============================================================================

create_database_and_user() {
    log INFO "Création de la base de données et de l'utilisateur..."

    local db_password="${GENERATED_SECRETS["POSTGRES_PASSWORD"]}"

    # Créer l'utilisateur si nécessaire
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${PG_USER_NAME}'" 2>/dev/null | grep -q 1; then
        log INFO "Création de l'utilisateur ${PG_USER_NAME}..."

        sudo -u postgres psql -c "CREATE USER ${PG_USER_NAME} WITH PASSWORD '${db_password}';" 2>/dev/null

        log OK "Utilisateur ${PG_USER_NAME} créé"
    else
        # Mettre à jour le mot de passe
        log INFO "Mise à jour du mot de passe pour ${PG_USER_NAME}..."
        sudo -u postgres psql -c "ALTER USER ${PG_USER_NAME} WITH PASSWORD '${db_password}';" 2>/dev/null
    fi

    # Créer la base de données si nécessaire
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${PG_DB_NAME}'" 2>/dev/null | grep -q 1; then
        log INFO "Création de la base de données ${PG_DB_NAME}..."

        sudo -u postgres psql -c "CREATE DATABASE ${PG_DB_NAME} OWNER ${PG_USER_NAME};" 2>/dev/null

        # Accorder tous les privilèges
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${PG_DB_NAME} TO ${PG_USER_NAME};" 2>/dev/null

        # Extensions utiles
        sudo -u postgres psql -d "${PG_DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" 2>/dev/null
        sudo -u postgres psql -d "${PG_DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";" 2>/dev/null

        log OK "Base de données ${PG_DB_NAME} créée"
    else
        log INFO "Base de données ${PG_DB_NAME} existe déjà"
    fi

    # Configurer pg_hba.conf pour l'authentification par mot de passe
    configure_pg_hba
}

configure_pg_hba() {
    log INFO "Configuration de l'authentification PostgreSQL..."

    local pg_hba=""

    if [[ "${OS_TYPE}" == "darwin" ]]; then
        pg_hba="$(brew --prefix)/var/postgresql@${PG_VERSION}/pg_hba.conf"
    else
        for path in \
            "/etc/postgresql/${PG_VERSION}/main/pg_hba.conf" \
            "/var/lib/pgsql/${PG_VERSION}/data/pg_hba.conf" \
            "/var/lib/postgres/data/pg_hba.conf"; do
            if [[ -f "${path}" ]]; then
                pg_hba="${path}"
                break
            fi
        done
    fi

    if [[ -z "${pg_hba}" ]] || [[ ! -f "${pg_hba}" ]]; then
        log WARN "Fichier pg_hba.conf non trouvé"
        return
    fi

    # Vérifier si la règle existe déjà
    if ! grep -q "azals_user" "${pg_hba}" 2>/dev/null; then
        # Ajouter la règle d'authentification
        local hba_line="local   ${PG_DB_NAME}     ${PG_USER_NAME}                               scram-sha-256"

        # Insérer avant la première règle existante
        sudo sed -i.bak "/^local.*all.*all/i ${hba_line}" "${pg_hba}" 2>/dev/null || \
        echo "${hba_line}" | sudo tee -a "${pg_hba}" > /dev/null

        # Ajouter aussi pour les connexions TCP
        local hba_tcp="host    ${PG_DB_NAME}     ${PG_USER_NAME}     127.0.0.1/32          scram-sha-256"
        echo "${hba_tcp}" | sudo tee -a "${pg_hba}" > /dev/null

        # Recharger la configuration
        sudo -u postgres psql -c "SELECT pg_reload_conf();" 2>/dev/null || true
    fi

    log OK "Authentification PostgreSQL configurée"
}

#===============================================================================
# VÉRIFICATION DE LA CONNEXION
#===============================================================================

verify_postgres_connection() {
    log INFO "Vérification de la connexion PostgreSQL..."

    local db_password="${GENERATED_SECRETS["POSTGRES_PASSWORD"]}"
    local connection_string="postgresql://${PG_USER_NAME}:${db_password}@localhost:5432/${PG_DB_NAME}"

    # Test de connexion
    if PGPASSWORD="${db_password}" psql -h localhost -U "${PG_USER_NAME}" -d "${PG_DB_NAME}" -c "SELECT 1;" &> /dev/null; then
        log OK "Connexion PostgreSQL réussie"
        return 0
    else
        log ERROR "Échec de la connexion PostgreSQL"
        log INFO "Vérifiez que PostgreSQL est démarré et que les credentials sont corrects"
        return 1
    fi
}

#===============================================================================
# SAUVEGARDE
#===============================================================================

backup_postgres() {
    # Crée une sauvegarde de la base de données
    local backup_dir="${PROJECT_ROOT}/backups"
    local backup_file="${backup_dir}/azals_$(date +%Y%m%d_%H%M%S).sql.gz"

    mkdir -p "${backup_dir}"

    log INFO "Création de la sauvegarde PostgreSQL..."

    local db_password="${GENERATED_SECRETS["POSTGRES_PASSWORD"]}"

    PGPASSWORD="${db_password}" pg_dump -h localhost -U "${PG_USER_NAME}" "${PG_DB_NAME}" | \
        gzip > "${backup_file}"

    if [[ -f "${backup_file}" ]]; then
        chmod 600 "${backup_file}"
        log OK "Sauvegarde créée: ${backup_file}"
    else
        log ERROR "Échec de la sauvegarde"
    fi
}
