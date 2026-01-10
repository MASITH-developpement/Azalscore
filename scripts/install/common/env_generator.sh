#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Génération du fichier .env
#===============================================================================
# Ce module génère le fichier .env de manière sécurisée selon le mode
#===============================================================================

#===============================================================================
# FONCTIONS DE GÉNÉRATION
#===============================================================================

generate_env_file() {
    log INFO "Génération du fichier de configuration .env..."

    local env_file="${PROJECT_ROOT}/.env"
    local env_backup=""

    # Sauvegarder l'ancien .env s'il existe
    if [[ -f "${env_file}" ]]; then
        env_backup="${env_file}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "${env_file}" "${env_backup}"
        log INFO "Ancien .env sauvegardé: ${env_backup}"
    fi

    # Générer selon le mode
    case "${INSTALL_MODE}" in
        dev)
            generate_dev_env "${env_file}"
            ;;
        prod)
            generate_prod_env "${env_file}"
            ;;
        cloud)
            generate_cloud_env "${env_file}"
            ;;
    esac

    # Sécuriser les permissions
    chmod 600 "${env_file}"

    # Vérifier que .env est dans .gitignore
    ensure_gitignore

    log OK "Fichier .env généré: ${env_file}"
}

generate_dev_env() {
    local env_file="$1"

    log INFO "Génération de la configuration développement..."

    local db_password="${GENERATED_SECRETS["POSTGRES_PASSWORD"]}"
    local secret_key="${GENERATED_SECRETS["SECRET_KEY"]}"
    local bootstrap_secret="${GENERATED_SECRETS["BOOTSTRAP_SECRET"]}"

    cat > "${env_file}" << EOF
#===============================================================================
# AZALSCORE - Configuration Développement
#===============================================================================
# Généré automatiquement le $(date '+%Y-%m-%d %H:%M:%S')
# NE PAS VERSIONNER CE FICHIER
#===============================================================================

#-------------------------------------------------------------------------------
# Environnement
#-------------------------------------------------------------------------------
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

#-------------------------------------------------------------------------------
# Base de données PostgreSQL
#-------------------------------------------------------------------------------
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=${db_password}
DATABASE_URL=postgresql+psycopg2://azals_user:${db_password}@localhost:5432/azals

# Pool de connexions (développement)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

#-------------------------------------------------------------------------------
# Sécurité
#-------------------------------------------------------------------------------
# Clé secrète pour JWT et sessions (256 bits)
SECRET_KEY=${secret_key}

# Secret pour le bootstrap admin initial
BOOTSTRAP_SECRET=${bootstrap_secret}

#-------------------------------------------------------------------------------
# UUID Database (sécurité)
#-------------------------------------------------------------------------------
DB_STRICT_UUID=true
DB_RESET_UUID=false
DB_AUTO_RESET_ON_VIOLATION=false

#-------------------------------------------------------------------------------
# CORS (développement)
#-------------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000

#-------------------------------------------------------------------------------
# Rate Limiting
#-------------------------------------------------------------------------------
RATE_LIMIT_PER_MINUTE=100
AUTH_RATE_LIMIT_PER_MINUTE=10

#-------------------------------------------------------------------------------
# API
#-------------------------------------------------------------------------------
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

#-------------------------------------------------------------------------------
# Version
#-------------------------------------------------------------------------------
VERSION=0.3.0
EOF
}

generate_prod_env() {
    local env_file="$1"

    log INFO "Génération de la configuration production..."

    local db_password="${GENERATED_SECRETS["POSTGRES_PASSWORD"]}"
    local secret_key="${GENERATED_SECRETS["SECRET_KEY"]}"
    local bootstrap_secret="${GENERATED_SECRETS["BOOTSTRAP_SECRET"]}"
    local encryption_key="${GENERATED_SECRETS["ENCRYPTION_KEY"]}"
    local redis_password="${GENERATED_SECRETS["REDIS_PASSWORD"]:-}"

    # Demander le domaine en mode interactif
    local domain="azals.example.com"
    if [[ "${INTERACTIVE}" == "true" ]]; then
        echo ""
        read -rp "Entrez le domaine de production (ex: azals.example.com): " domain
        [[ -z "${domain}" ]] && domain="azals.example.com"
    fi

    cat > "${env_file}" << EOF
#===============================================================================
# AZALSCORE - Configuration Production
#===============================================================================
# Généré automatiquement le $(date '+%Y-%m-%d %H:%M:%S')
# NE JAMAIS VERSIONNER CE FICHIER
# CONSERVER UNE COPIE SÉCURISÉE DES SECRETS
#===============================================================================

#-------------------------------------------------------------------------------
# Environnement
#-------------------------------------------------------------------------------
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

#-------------------------------------------------------------------------------
# Base de données PostgreSQL
#-------------------------------------------------------------------------------
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=${db_password}
DATABASE_URL=postgresql+psycopg2://azals_user:${db_password}@localhost:5432/azals

# Pool de connexions (production)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

#-------------------------------------------------------------------------------
# Sécurité (CRITIQUE - Ne jamais exposer)
#-------------------------------------------------------------------------------
# Clé secrète pour JWT et sessions (256 bits)
SECRET_KEY=${secret_key}

# Secret pour le bootstrap admin initial
BOOTSTRAP_SECRET=${bootstrap_secret}

# Clé de chiffrement AES-256 (Fernet)
ENCRYPTION_KEY=${encryption_key}

#-------------------------------------------------------------------------------
# UUID Database (sécurité - STRICT EN PRODUCTION)
#-------------------------------------------------------------------------------
DB_STRICT_UUID=true
DB_RESET_UUID=false
DB_AUTO_RESET_ON_VIOLATION=false

#-------------------------------------------------------------------------------
# CORS (production - JAMAIS de localhost)
#-------------------------------------------------------------------------------
CORS_ORIGINS=https://${domain},https://www.${domain}

#-------------------------------------------------------------------------------
# Rate Limiting (production - plus strict)
#-------------------------------------------------------------------------------
RATE_LIMIT_PER_MINUTE=60
AUTH_RATE_LIMIT_PER_MINUTE=5

#-------------------------------------------------------------------------------
# Redis (optionnel - pour rate limiting distribué)
#-------------------------------------------------------------------------------
REDIS_URL=redis://:${redis_password}@localhost:6379/0

#-------------------------------------------------------------------------------
# API
#-------------------------------------------------------------------------------
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=${CPU_CORES:-4}

#-------------------------------------------------------------------------------
# Logging production
#-------------------------------------------------------------------------------
LOG_FORMAT=json

#-------------------------------------------------------------------------------
# Version
#-------------------------------------------------------------------------------
VERSION=0.3.0
EOF
}

generate_cloud_env() {
    local env_file="$1"

    log INFO "Génération de la configuration cloud..."

    local secret_key="${GENERATED_SECRETS["SECRET_KEY"]}"
    local bootstrap_secret="${GENERATED_SECRETS["BOOTSTRAP_SECRET"]}"
    local encryption_key="${GENERATED_SECRETS["ENCRYPTION_KEY"]}"

    cat > "${env_file}" << EOF
#===============================================================================
# AZALSCORE - Configuration Cloud (Template)
#===============================================================================
# Généré automatiquement le $(date '+%Y-%m-%d %H:%M:%S')
#
# INSTRUCTIONS:
# 1. Copiez les valeurs ci-dessous dans les variables d'environnement
#    de votre plateforme cloud (Railway/Render/Fly.io)
# 2. DATABASE_URL sera fourni par le service de base de données managé
# 3. Ajustez CORS_ORIGINS selon votre domaine
#===============================================================================

#-------------------------------------------------------------------------------
# Variables à configurer sur la plateforme cloud
#-------------------------------------------------------------------------------

# Environnement
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Sécurité (COPIER CES VALEURS DANS VOTRE DASHBOARD)
SECRET_KEY=${secret_key}
BOOTSTRAP_SECRET=${bootstrap_secret}
ENCRYPTION_KEY=${encryption_key}

# UUID (OBLIGATOIRE)
DB_STRICT_UUID=true
DB_RESET_UUID=false
DB_AUTO_RESET_ON_VIOLATION=false

# CORS (REMPLACER PAR VOTRE DOMAINE)
CORS_ORIGINS=https://votre-app.railway.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
AUTH_RATE_LIMIT_PER_MINUTE=5

# Pool DB
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

#-------------------------------------------------------------------------------
# Variables fournies par la plateforme (NE PAS DÉFINIR MANUELLEMENT)
#-------------------------------------------------------------------------------
# DATABASE_URL=<fourni par Railway/Render>
# PORT=<fourni par la plateforme>
# REDIS_URL=<si Redis addon>
EOF

    # Créer aussi les fichiers de configuration spécifiques
    generate_cloud_instructions
}

generate_cloud_instructions() {
    local instructions_file="${PROJECT_ROOT}/.env.cloud-instructions"

    cat > "${instructions_file}" << 'EOF'
================================================================================
AZALSCORE - Instructions de déploiement Cloud
================================================================================

RAILWAY
-------
1. Créer un nouveau projet sur railway.app
2. Ajouter un service PostgreSQL
3. Connecter votre dépôt GitHub
4. Dans "Variables", ajouter:
   - Copier toutes les variables de .env (sauf DATABASE_URL)
   - Railway fournit DATABASE_URL automatiquement

RENDER
------
1. Créer un nouveau Web Service sur render.com
2. Connecter votre dépôt GitHub
3. Configurer:
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
4. Ajouter une base PostgreSQL managée
5. Dans Environment, ajouter les variables de .env

FLY.IO
------
1. Installer flyctl: curl -L https://fly.io/install.sh | sh
2. fly launch
3. fly postgres create
4. fly secrets set SECRET_KEY=xxx BOOTSTRAP_SECRET=xxx ...
5. fly deploy

================================================================================
IMPORTANT
================================================================================
- Ne JAMAIS mettre DEBUG=true en production
- Ne JAMAIS autoriser localhost dans CORS_ORIGINS
- Toujours utiliser HTTPS
- Sauvegarder les secrets dans un gestionnaire de mots de passe
================================================================================
EOF

    chmod 600 "${instructions_file}"
    log INFO "Instructions cloud créées: ${instructions_file}"
}

#===============================================================================
# SÉCURITÉ
#===============================================================================

ensure_gitignore() {
    local gitignore="${PROJECT_ROOT}/.gitignore"

    local patterns=(
        ".env"
        ".env.local"
        ".env.*.local"
        ".env.production"
        ".env.backup*"
        ".env.cloud-instructions"
        "secrets.json"
        "*.key"
        "*.pem"
    )

    if [[ ! -f "${gitignore}" ]]; then
        touch "${gitignore}"
    fi

    for pattern in "${patterns[@]}"; do
        if ! grep -qxF "${pattern}" "${gitignore}" 2>/dev/null; then
            echo "${pattern}" >> "${gitignore}"
            log DEBUG "Ajouté à .gitignore: ${pattern}"
        fi
    done
}

#===============================================================================
# VALIDATION
#===============================================================================

validate_env_file() {
    local env_file="${PROJECT_ROOT}/.env"

    log INFO "Validation du fichier .env..."

    if [[ ! -f "${env_file}" ]]; then
        log ERROR "Fichier .env non trouvé"
        return 1
    fi

    # Vérifier les variables obligatoires
    local required_vars=(
        "ENVIRONMENT"
        "DATABASE_URL"
        "SECRET_KEY"
        "BOOTSTRAP_SECRET"
    )

    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        required_vars+=("ENCRYPTION_KEY")
    fi

    local missing=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "${env_file}" 2>/dev/null; then
            missing+=("${var}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log ERROR "Variables manquantes dans .env: ${missing[*]}"
        return 1
    fi

    # Vérifications spécifiques production
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        # DEBUG doit être false
        if grep -q "^DEBUG=true" "${env_file}" 2>/dev/null; then
            log ERROR "DEBUG=true interdit en production"
            return 1
        fi

        # Pas de localhost dans CORS
        if grep "^CORS_ORIGINS=" "${env_file}" 2>/dev/null | grep -qi "localhost"; then
            log ERROR "localhost interdit dans CORS_ORIGINS en production"
            return 1
        fi
    fi

    log OK "Fichier .env valide"
    return 0
}
