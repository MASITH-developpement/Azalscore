#!/bin/bash
# ==============================================================================
# AZALSCORE - DÉPLOIEMENT AUTOMATIQUE COMPLET RENDER.COM
# ==============================================================================
# Ce script déploie AZALSCORE sur Render.com SANS AUCUNE INTERVENTION.
#
# PRÉREQUIS: Clé API Render (une seule fois)
#   1. Aller sur https://dashboard.render.com/account/api-keys
#   2. Créer une clé API
#   3. Exporter: export RENDER_API_KEY="rnd_xxxxxxxxx"
#   4. Lancer ce script
#
# OU: Lancer directement et le script demandera la clé une seule fois.
#
# USAGE:
#   ./deploy-render-auto.sh
#
# ==============================================================================

set -e

# ==============================================================================
# CONFIGURATION
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
readonly RENDER_API="https://api.render.com/v1"
readonly REGION="frankfurt"

# Noms des services (uniques)
readonly TIMESTAMP=$(date +%s)
readonly API_NAME="azalscore-api"
readonly FRONTEND_NAME="azalscore-frontend"
readonly DB_NAME="azalscore-db"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

log() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Génère un secret sécurisé
generate_secret() {
    local length="${1:-64}"
    python3 -c "import secrets; print(secrets.token_urlsafe($length))" 2>/dev/null || \
    openssl rand -base64 "$length" | tr -dc 'a-zA-Z0-9' | head -c "$length"
}

# Génère une clé Fernet
generate_fernet_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || \
    python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
}

# Appel API Render
render_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    local args=(-s -X "$method" -H "Authorization: Bearer ${RENDER_API_KEY}" -H "Content-Type: application/json")

    if [ -n "$data" ]; then
        args+=(-d "$data")
    fi

    curl "${args[@]}" "${RENDER_API}${endpoint}"
}

# Attend qu'un service soit prêt
wait_for_service() {
    local service_id="$1"
    local timeout="${2:-300}"
    local elapsed=0

    log "Attente du service $service_id..."

    while [ $elapsed -lt $timeout ]; do
        local status=$(render_api GET "/services/${service_id}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('suspended', 'unknown'))" 2>/dev/null)

        if [ "$status" = "not_suspended" ] || [ "$status" = "False" ]; then
            log "Service prêt!"
            return 0
        fi

        sleep 10
        elapsed=$((elapsed + 10))
        echo -n "."
    done

    warn "Timeout atteint, le service peut encore être en cours de déploiement"
    return 0
}

# ==============================================================================
# VÉRIFICATION PRÉREQUIS
# ==============================================================================

check_prerequisites() {
    log "Vérification des prérequis..."

    # Vérifier curl
    if ! command -v curl &> /dev/null; then
        error "curl est requis. Installez-le avec: apt install curl"
    fi

    # Vérifier python3
    if ! command -v python3 &> /dev/null; then
        error "python3 est requis. Installez-le avec: apt install python3"
    fi

    # Vérifier jq ou utiliser python pour le JSON
    if ! command -v jq &> /dev/null; then
        log "jq non trouvé, utilisation de python3 pour le parsing JSON"
    fi

    log "Prérequis OK"
}

# ==============================================================================
# AUTHENTIFICATION RENDER
# ==============================================================================

setup_render_auth() {
    if [ -z "${RENDER_API_KEY:-}" ]; then
        echo ""
        echo "=============================================="
        echo "CONFIGURATION RENDER.COM (une seule fois)"
        echo "=============================================="
        echo ""
        echo "Pour déployer automatiquement, j'ai besoin de votre clé API Render."
        echo ""
        echo "1. Ouvrez: https://dashboard.render.com/account/api-keys"
        echo "2. Cliquez sur 'Create API Key'"
        echo "3. Copiez la clé générée"
        echo ""
        read -p "Collez votre clé API Render: " RENDER_API_KEY
        echo ""

        if [ -z "$RENDER_API_KEY" ]; then
            error "Clé API requise pour continuer"
        fi

        # Sauvegarde pour les prochaines fois
        echo "export RENDER_API_KEY=\"${RENDER_API_KEY}\"" >> ~/.bashrc
        log "Clé API sauvegardée dans ~/.bashrc"
    fi

    # Vérifier que la clé fonctionne
    log "Vérification de la clé API..."
    local owner_info=$(render_api GET "/owners" 2>/dev/null)

    if echo "$owner_info" | grep -q "error\|unauthorized\|invalid"; then
        error "Clé API invalide. Vérifiez sur https://dashboard.render.com/account/api-keys"
    fi

    # Extraire l'owner ID
    OWNER_ID=$(echo "$owner_info" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data[0]['owner']['id'] if data else '')" 2>/dev/null)

    if [ -z "$OWNER_ID" ]; then
        error "Impossible de récupérer l'owner ID"
    fi

    log "Authentification OK (Owner: ${OWNER_ID:0:8}...)"
}

# ==============================================================================
# GÉNÉRATION DES SECRETS
# ==============================================================================

generate_all_secrets() {
    log "Génération des secrets sécurisés..."

    SECRET_KEY=$(generate_secret 64)
    BOOTSTRAP_SECRET=$(generate_secret 64)
    ENCRYPTION_KEY=$(generate_fernet_key)
    ADMIN_PASSWORD=$(generate_secret 16)

    log "Secrets générés:"
    log "  - SECRET_KEY: ${SECRET_KEY:0:20}..."
    log "  - BOOTSTRAP_SECRET: ${BOOTSTRAP_SECRET:0:20}..."
    log "  - ENCRYPTION_KEY: ${ENCRYPTION_KEY:0:20}..."
    log "  - ADMIN_PASSWORD: ${ADMIN_PASSWORD}"

    # Sauvegarder les secrets localement
    cat > "${ROOT_DIR}/.env.render" << EOF
# AZALSCORE - Secrets générés le $(date)
# GARDEZ CE FICHIER EN SÉCURITÉ!

SECRET_KEY=${SECRET_KEY}
BOOTSTRAP_SECRET=${BOOTSTRAP_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
ADMIN_EMAIL=admin@azalscore.local
ADMIN_PASSWORD=${ADMIN_PASSWORD}
EOF
    chmod 600 "${ROOT_DIR}/.env.render"
    log "Secrets sauvegardés dans .env.render"
}

# ==============================================================================
# CRÉATION DE LA BASE DE DONNÉES
# ==============================================================================

create_database() {
    log "Création de la base de données PostgreSQL..."

    local db_payload=$(cat << EOF
{
    "name": "${DB_NAME}",
    "region": "${REGION}",
    "plan": "free",
    "databaseName": "azalscore",
    "databaseUser": "azalscore_user",
    "ownerId": "${OWNER_ID}"
}
EOF
)

    local response=$(render_api POST "/postgres" "$db_payload")

    if echo "$response" | grep -q "error"; then
        # Peut-être que la DB existe déjà
        log "La base de données existe peut-être déjà, recherche..."

        local existing=$(render_api GET "/postgres" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for db in data:
    if db.get('postgres', {}).get('name') == '${DB_NAME}':
        print(db['postgres']['id'])
        break
" 2>/dev/null)

        if [ -n "$existing" ]; then
            DB_ID="$existing"
            log "Base de données existante trouvée: $DB_ID"
        else
            warn "Impossible de créer la base de données: $response"
            return 1
        fi
    else
        DB_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('postgres', {}).get('id', ''))" 2>/dev/null)
        log "Base de données créée: $DB_ID"
    fi

    # Attendre que la DB soit prête et récupérer l'URL
    log "Attente de la disponibilité de la base de données..."
    sleep 30  # PostgreSQL prend du temps à démarrer

    local db_info=$(render_api GET "/postgres/${DB_ID}")
    DATABASE_URL=$(echo "$db_info" | python3 -c "import sys,json; print(json.load(sys.stdin).get('postgres', {}).get('connectionInfo', {}).get('internalConnectionString', ''))" 2>/dev/null)

    if [ -z "$DATABASE_URL" ]; then
        warn "URL de connexion non disponible immédiatement, utilisation de la référence"
        DATABASE_URL="internal"
    fi

    log "Base de données configurée"
}

# ==============================================================================
# CRÉATION DU SERVICE API
# ==============================================================================

create_api_service() {
    log "Création du service API..."

    # Récupérer l'URL du repo GitHub
    local repo_url=$(git -C "${ROOT_DIR}" remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|')

    if [ -z "$repo_url" ]; then
        error "Impossible de récupérer l'URL du repo Git"
    fi

    log "Repo: $repo_url"

    local api_payload=$(cat << EOF
{
    "name": "${API_NAME}",
    "type": "web_service",
    "region": "${REGION}",
    "plan": "free",
    "ownerId": "${OWNER_ID}",
    "autoDeploy": "yes",
    "repo": "${repo_url}",
    "branch": "main",
    "rootDir": ".",
    "buildCommand": "pip install -r requirements.txt",
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port \$PORT",
    "envVars": [
        {"key": "PYTHON_VERSION", "value": "3.11.7"},
        {"key": "ENVIRONMENT", "value": "staging"},
        {"key": "DEBUG", "value": "false"},
        {"key": "LOG_LEVEL", "value": "INFO"},
        {"key": "SECRET_KEY", "value": "${SECRET_KEY}"},
        {"key": "BOOTSTRAP_SECRET", "value": "${BOOTSTRAP_SECRET}"},
        {"key": "ENCRYPTION_KEY", "value": "${ENCRYPTION_KEY}"},
        {"key": "ADMIN_EMAIL", "value": "admin@azalscore.local"},
        {"key": "ADMIN_PASSWORD", "value": "${ADMIN_PASSWORD}"},
        {"key": "CORS_ORIGINS", "value": "https://${FRONTEND_NAME}.onrender.com,http://localhost:5173"}
    ],
    "serviceDetails": {
        "envSpecificDetails": {
            "dockerCommand": "",
            "dockerContext": "",
            "dockerfilePath": ""
        },
        "healthCheckPath": "/health",
        "numInstances": 1,
        "openPorts": [{"port": 10000, "protocol": "TCP"}],
        "pullRequestPreviewsEnabled": "no"
    }
}
EOF
)

    local response=$(render_api POST "/services" "$api_payload")

    if echo "$response" | grep -q "error"; then
        warn "Erreur création API: $response"
        # Chercher service existant
        API_ID=$(render_api GET "/services" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for svc in data:
    if svc.get('service', {}).get('name') == '${API_NAME}':
        print(svc['service']['id'])
        break
" 2>/dev/null)

        if [ -z "$API_ID" ]; then
            error "Impossible de créer le service API"
        fi
        log "Service API existant trouvé: $API_ID"
    else
        API_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('service', {}).get('id', ''))" 2>/dev/null)
        log "Service API créé: $API_ID"
    fi

    API_URL="https://${API_NAME}.onrender.com"
    log "URL API: $API_URL"
}

# ==============================================================================
# CRÉATION DU SERVICE FRONTEND
# ==============================================================================

create_frontend_service() {
    log "Création du service Frontend..."

    local repo_url=$(git -C "${ROOT_DIR}" remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|')

    local frontend_payload=$(cat << EOF
{
    "name": "${FRONTEND_NAME}",
    "type": "static_site",
    "region": "${REGION}",
    "ownerId": "${OWNER_ID}",
    "autoDeploy": "yes",
    "repo": "${repo_url}",
    "branch": "main",
    "rootDir": "frontend",
    "buildCommand": "npm ci && npm run build",
    "publishPath": "dist",
    "envVars": [
        {"key": "NODE_VERSION", "value": "18"},
        {"key": "VITE_API_URL", "value": "${API_URL}"}
    ],
    "routes": [
        {"type": "rewrite", "source": "/*", "destination": "/index.html"}
    ],
    "headers": [
        {"path": "/*", "name": "X-Frame-Options", "value": "SAMEORIGIN"},
        {"path": "/*", "name": "X-Content-Type-Options", "value": "nosniff"}
    ]
}
EOF
)

    local response=$(render_api POST "/services" "$frontend_payload")

    if echo "$response" | grep -q "error"; then
        warn "Erreur création Frontend: $response"
        FRONTEND_ID=$(render_api GET "/services" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for svc in data:
    if svc.get('service', {}).get('name') == '${FRONTEND_NAME}':
        print(svc['service']['id'])
        break
" 2>/dev/null)

        if [ -z "$FRONTEND_ID" ]; then
            warn "Impossible de créer le frontend via API, continuons..."
        else
            log "Service Frontend existant trouvé: $FRONTEND_ID"
        fi
    else
        FRONTEND_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('service', {}).get('id', ''))" 2>/dev/null)
        log "Service Frontend créé: $FRONTEND_ID"
    fi

    FRONTEND_URL="https://${FRONTEND_NAME}.onrender.com"
    log "URL Frontend: $FRONTEND_URL"
}

# ==============================================================================
# CONNEXION DB AU SERVICE API
# ==============================================================================

connect_database_to_api() {
    if [ -n "$DB_ID" ] && [ -n "$API_ID" ]; then
        log "Connexion de la base de données au service API..."

        # Ajouter la variable DATABASE_URL depuis la DB
        local env_payload=$(cat << EOF
{
    "envVars": [
        {"key": "DATABASE_URL", "value": "${DATABASE_URL}"}
    ]
}
EOF
)

        render_api PATCH "/services/${API_ID}/env-vars" "$env_payload" > /dev/null 2>&1 || true
        log "Base de données connectée"
    fi
}

# ==============================================================================
# DÉPLOIEMENT
# ==============================================================================

trigger_deploy() {
    log "Déclenchement du déploiement..."

    if [ -n "$API_ID" ]; then
        render_api POST "/services/${API_ID}/deploys" '{"clearCache": "do_not_clear"}' > /dev/null 2>&1 || true
        log "Déploiement API déclenché"
    fi

    if [ -n "$FRONTEND_ID" ]; then
        render_api POST "/services/${FRONTEND_ID}/deploys" '{"clearCache": "do_not_clear"}' > /dev/null 2>&1 || true
        log "Déploiement Frontend déclenché"
    fi
}

# ==============================================================================
# ATTENTE ET VÉRIFICATION
# ==============================================================================

wait_and_verify() {
    log "Attente du déploiement (cela peut prendre 5-10 minutes)..."

    local max_wait=600  # 10 minutes
    local elapsed=0
    local api_ready=false
    local frontend_ready=false

    while [ $elapsed -lt $max_wait ]; do
        # Vérifier l'API
        if ! $api_ready; then
            if curl -sf "${API_URL}/health" > /dev/null 2>&1; then
                log "✓ API en ligne!"
                api_ready=true
            fi
        fi

        # Vérifier le Frontend
        if ! $frontend_ready; then
            if curl -sf "${FRONTEND_URL}" > /dev/null 2>&1; then
                log "✓ Frontend en ligne!"
                frontend_ready=true
            fi
        fi

        if $api_ready && $frontend_ready; then
            break
        fi

        echo -n "."
        sleep 15
        elapsed=$((elapsed + 15))
    done

    echo ""

    if ! $api_ready; then
        warn "L'API n'est pas encore accessible. Le déploiement peut prendre plus de temps."
        warn "Vérifiez sur https://dashboard.render.com"
    fi
}

# ==============================================================================
# RAPPORT FINAL
# ==============================================================================

print_summary() {
    echo ""
    echo "=============================================="
    echo "     DÉPLOIEMENT AZALSCORE TERMINÉ!"
    echo "=============================================="
    echo ""
    echo "🌐 URLs:"
    echo "   Frontend: ${FRONTEND_URL}"
    echo "   API:      ${API_URL}"
    echo "   Health:   ${API_URL}/health"
    echo "   Docs:     ${API_URL}/docs"
    echo ""
    echo "🔐 Identifiants Admin:"
    echo "   Email:    admin@azalscore.local"
    echo "   Password: ${ADMIN_PASSWORD}"
    echo ""
    echo "⚠️  IMPORTANT: Changez le mot de passe à la première connexion!"
    echo ""
    echo "📁 Secrets sauvegardés dans: ${ROOT_DIR}/.env.render"
    echo ""
    echo "📊 Dashboard Render: https://dashboard.render.com"
    echo ""
    echo "=============================================="

    # Sauvegarder le résumé
    cat > "${ROOT_DIR}/DEPLOYMENT_INFO.txt" << EOF
AZALSCORE - Informations de Déploiement
=======================================
Date: $(date)

URLs:
- Frontend: ${FRONTEND_URL}
- API: ${API_URL}
- Documentation: ${API_URL}/docs

Identifiants Admin:
- Email: admin@azalscore.local
- Password: ${ADMIN_PASSWORD}

IMPORTANT: Changez le mot de passe à la première connexion!

Secrets dans: .env.render
EOF

    log "Informations sauvegardées dans DEPLOYMENT_INFO.txt"
}

# ==============================================================================
# MAIN
# ==============================================================================

main() {
    echo ""
    echo "=============================================="
    echo "   AZALSCORE - Déploiement Automatique"
    echo "         Render.com (100% gratuit)"
    echo "=============================================="
    echo ""

    check_prerequisites
    setup_render_auth
    generate_all_secrets
    create_database
    create_api_service
    create_frontend_service
    connect_database_to_api
    trigger_deploy
    wait_and_verify
    print_summary
}

# Exécution
main "$@"
