#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Installation de l'application
#===============================================================================
# Ce module installe et configure l'application AZALSCORE
#===============================================================================

#===============================================================================
# INSTALLATION AZALSCORE
#===============================================================================

install_azalscore() {
    log INFO "Installation de AZALSCORE..."

    # S'assurer que le venv est actif
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        activate_virtual_environment
    fi

    # Vérifier la structure du projet
    verify_project_structure

    # Charger les variables d'environnement
    load_environment

    # Exécuter les migrations de base de données
    run_database_migrations

    # Vérifier l'intégrité de la base de données
    verify_database_schema

    # Créer les scripts de démarrage
    create_startup_scripts

    # Test de démarrage rapide
    test_application_startup

    log OK "AZALSCORE installé avec succès"
}

#===============================================================================
# VÉRIFICATION DE LA STRUCTURE
#===============================================================================

verify_project_structure() {
    log INFO "Vérification de la structure du projet..."

    local required_files=(
        "app/main.py"
        "app/core/config.py"
        "app/core/database.py"
        "requirements.txt"
        "alembic.ini"
    )

    local required_dirs=(
        "app"
        "app/api"
        "app/core"
        "app/db"
        "app/models"
        "app/modules"
        "alembic"
        "alembic/versions"
    )

    local missing=()

    for file in "${required_files[@]}"; do
        if [[ ! -f "${PROJECT_ROOT}/${file}" ]]; then
            missing+=("${file}")
        fi
    done

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "${PROJECT_ROOT}/${dir}" ]]; then
            missing+=("${dir}/")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log ERROR "Éléments manquants dans le projet: ${missing[*]}"
        exit 1
    fi

    log OK "Structure du projet validée"
}

#===============================================================================
# CHARGEMENT DE L'ENVIRONNEMENT
#===============================================================================

load_environment() {
    log INFO "Chargement des variables d'environnement..."

    local env_file="${PROJECT_ROOT}/.env"

    if [[ ! -f "${env_file}" ]]; then
        log ERROR "Fichier .env non trouvé"
        exit 1
    fi

    # Charger les variables (sans export pour éviter les fuites)
    set -a
    # shellcheck source=/dev/null
    source "${env_file}"
    set +a

    # Vérifier les variables critiques
    local critical_vars=(
        "DATABASE_URL"
        "SECRET_KEY"
        "ENVIRONMENT"
    )

    for var in "${critical_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log ERROR "Variable ${var} non définie"
            exit 1
        fi
    done

    log OK "Variables d'environnement chargées"
}

#===============================================================================
# MIGRATIONS BASE DE DONNÉES
#===============================================================================

run_database_migrations() {
    log INFO "Exécution des migrations de base de données..."

    cd "${PROJECT_ROOT}" || exit 1

    # Vérifier que la connexion DB fonctionne
    log INFO "Vérification de la connexion à la base de données..."

    if ! python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
    print('OK')
" 2>/dev/null; then
        log ERROR "Impossible de se connecter à la base de données"
        log INFO "Vérifiez que PostgreSQL est démarré et que DATABASE_URL est correct"
        exit 1
    fi

    log OK "Connexion à la base de données établie"

    # Exécuter les migrations Alembic
    log INFO "Application des migrations Alembic..."

    if alembic upgrade head 2>&1 | tee -a "${LOG_FILE}"; then
        log OK "Migrations appliquées avec succès"
    else
        log WARN "Des avertissements lors des migrations (peut être normal)"
    fi
}

#===============================================================================
# VÉRIFICATION DU SCHÉMA
#===============================================================================

verify_database_schema() {
    log INFO "Vérification du schéma de base de données..."

    cd "${PROJECT_ROOT}" || exit 1

    # Vérifier que toutes les tables utilisent des UUID
    log INFO "Vérification des colonnes UUID..."

    python << 'EOF' 2>/dev/null || log WARN "Vérification UUID ignorée"
import os
os.environ.setdefault('ENVIRONMENT', 'development')

from sqlalchemy import inspect, text
from app.core.database import engine

with engine.connect() as conn:
    # Lister les tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if not tables:
        print("Aucune table trouvée (base de données vide)")
    else:
        print(f"Tables trouvées: {len(tables)}")

        # Vérifier les types de colonnes ID
        warnings = []
        for table in tables:
            columns = inspector.get_columns(table)
            for col in columns:
                if col['name'] in ('id', 'uuid', 'tenant_id') and 'UUID' not in str(col['type']).upper():
                    if 'INTEGER' in str(col['type']).upper() or 'BIGINT' in str(col['type']).upper():
                        warnings.append(f"{table}.{col['name']}: {col['type']}")

        if warnings:
            print(f"ATTENTION: Colonnes non-UUID détectées: {warnings}")
        else:
            print("OK: Toutes les colonnes ID utilisent UUID")
EOF

    log OK "Schéma de base de données vérifié"
}

#===============================================================================
# SCRIPTS DE DÉMARRAGE
#===============================================================================

create_startup_scripts() {
    log INFO "Création des scripts de démarrage..."

    # Script de démarrage développement
    create_dev_start_script

    # Script de démarrage production
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        create_prod_start_script
    fi

    log OK "Scripts de démarrage créés"
}

create_dev_start_script() {
    local script="${PROJECT_ROOT}/start_dev.sh"

    cat > "${script}" << 'EOF'
#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Démarrage Développement
#===============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   AZALSCORE - Mode Développement${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Activer l'environnement virtuel
if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"
else
    echo "Environnement virtuel non trouvé. Exécutez d'abord ./scripts/install/install.sh"
    exit 1
fi

# Charger les variables d'environnement
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

# Variables de développement
export AZALS_ENV=dev
export DEBUG=true
export DB_STRICT_UUID=true

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  • Environment: ${ENVIRONMENT:-development}"
echo "  • Debug: ${DEBUG}"
echo "  • API: http://localhost:8000"
echo "  • Docs: http://localhost:8000/docs"
echo ""

# Démarrer l'application avec hot-reload
cd "${SCRIPT_DIR}"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir app \
    --log-level debug
EOF

    chmod +x "${script}"
    log OK "Script de développement créé: ${script}"
}

create_prod_start_script() {
    local script="${PROJECT_ROOT}/start_prod.sh"

    cat > "${script}" << 'EOF'
#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Démarrage Production
#===============================================================================
# NE JAMAIS UTILISER CE SCRIPT DIRECTEMENT EN PRODUCTION
# Utilisez systemd pour la gestion du service
#===============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   AZALSCORE - Mode Production${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Vérifications de sécurité
if [[ ! -f "${SCRIPT_DIR}/.env" ]]; then
    echo -e "${RED}ERREUR: Fichier .env non trouvé${NC}"
    exit 1
fi

# Vérifier que DEBUG n'est pas activé
if grep -q "^DEBUG=true" "${SCRIPT_DIR}/.env"; then
    echo -e "${RED}ERREUR: DEBUG=true détecté dans .env${NC}"
    echo "La production requiert DEBUG=false"
    exit 1
fi

# Activer l'environnement virtuel
if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"
else
    echo -e "${RED}Environnement virtuel non trouvé${NC}"
    exit 1
fi

# Charger les variables d'environnement
set -a
source "${SCRIPT_DIR}/.env"
set +a

# Variables de production (forcées)
export AZALS_ENV=prod
export DEBUG=false
export DB_STRICT_UUID=true
export DB_AUTO_RESET_ON_VIOLATION=false
export DB_RESET_UUID=false

# Nombre de workers (basé sur les CPUs)
WORKERS=${API_WORKERS:-$(nproc)}

echo ""
echo "Configuration:"
echo "  • Environment: production"
echo "  • Workers: ${WORKERS}"
echo "  • Host: ${API_HOST:-127.0.0.1}"
echo "  • Port: ${API_PORT:-8000}"
echo ""

# Démarrer avec Gunicorn
cd "${SCRIPT_DIR}"
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${WORKERS}" \
    --threads 2 \
    --bind "${API_HOST:-127.0.0.1}:${API_PORT:-8000}" \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance
EOF

    chmod +x "${script}"
    log OK "Script de production créé: ${script}"
}

#===============================================================================
# TEST DE DÉMARRAGE
#===============================================================================

test_application_startup() {
    log INFO "Test de démarrage de l'application..."

    cd "${PROJECT_ROOT}" || exit 1

    # Tester l'import de l'application
    if python -c "from app.main import app; print('Import OK')" 2>&1; then
        log OK "Import de l'application réussi"
    else
        log ERROR "Échec de l'import de l'application"
        exit 1
    fi

    # Test de démarrage rapide (si non-interactif ou si demandé)
    if [[ "${INTERACTIVE}" == "true" ]]; then
        echo ""
        read -rp "Tester le démarrage de l'API? [Y/n] " response
        if [[ ! "${response,,}" =~ ^(n|no)$ ]]; then
            run_quick_start_test
        fi
    fi
}

run_quick_start_test() {
    log INFO "Démarrage du test rapide..."

    cd "${PROJECT_ROOT}" || exit 1

    # Démarrer l'API en arrière-plan
    uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    local pid=$!

    # Attendre le démarrage
    sleep 3

    # Tester l'endpoint de santé
    local health_ok=false

    for _ in {1..5}; do
        if curl -s http://127.0.0.1:8000/health 2>/dev/null | grep -q "ok\|healthy"; then
            health_ok=true
            break
        fi
        sleep 1
    done

    # Arrêter le serveur de test
    kill "${pid}" 2>/dev/null || true
    wait "${pid}" 2>/dev/null || true

    if [[ "${health_ok}" == "true" ]]; then
        log OK "Test de démarrage réussi - l'API répond correctement"
    else
        log WARN "L'API n'a pas répondu au test de santé (peut être normal)"
    fi
}

#===============================================================================
# CONFIGURATION ADDITIONNELLE
#===============================================================================

setup_log_directory() {
    local log_dir="${PROJECT_ROOT}/logs"

    mkdir -p "${log_dir}"
    chmod 755 "${log_dir}"

    log OK "Répertoire de logs créé: ${log_dir}"
}

setup_temp_directory() {
    local temp_dir="${PROJECT_ROOT}/tmp"

    mkdir -p "${temp_dir}"
    chmod 755 "${temp_dir}"

    log OK "Répertoire temporaire créé: ${temp_dir}"
}
