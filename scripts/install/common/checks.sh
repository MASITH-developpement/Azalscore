#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Vérifications système
#===============================================================================
# Ce module effectue toutes les vérifications préliminaires avant installation
#===============================================================================

#===============================================================================
# VÉRIFICATIONS SYSTÈME
#===============================================================================

run_system_checks() {
    log INFO "Exécution des vérifications système..."

    check_shell_version
    check_required_commands
    check_python_version
    check_memory
    check_cpu
    check_git_repo

    log OK "Toutes les vérifications système passées"
}

check_shell_version() {
    log INFO "Vérification de la version du shell..."

    local bash_major
    bash_major="${BASH_VERSION%%.*}"

    if [[ "${bash_major}" -lt 4 ]]; then
        log ERROR "Bash 4.0+ requis (version actuelle: ${BASH_VERSION})"
        if [[ "${OS_TYPE}" == "darwin" ]]; then
            log INFO "Sur macOS, installez une version récente avec: brew install bash"
        fi
        exit 1
    fi

    log OK "Version Bash: ${BASH_VERSION}"
}

check_required_commands() {
    log INFO "Vérification des commandes requises..."

    local required_commands=(
        "curl"
        "git"
        "grep"
        "awk"
        "sed"
    )

    local optional_commands=(
        "jq"
        "openssl"
    )

    local missing=()

    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            missing+=("${cmd}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log ERROR "Commandes requises manquantes: ${missing[*]}"
        exit 1
    fi

    for cmd in "${optional_commands[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            log WARN "Commande optionnelle manquante: ${cmd}"
        fi
    done

    log OK "Toutes les commandes requises sont disponibles"
}

check_python_version() {
    log INFO "Vérification de la version Python..."

    local python_cmd=""
    local python_version=""

    # Chercher Python dans l'ordre de préférence
    for cmd in python3.12 python3.11 python3 python; do
        if command -v "${cmd}" &> /dev/null; then
            python_cmd="${cmd}"
            break
        fi
    done

    if [[ -z "${python_cmd}" ]]; then
        log WARN "Python non trouvé - sera installé automatiquement"
        return 0
    fi

    python_version=$("${python_cmd}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)

    if [[ -z "${python_version}" ]]; then
        log WARN "Impossible de déterminer la version Python"
        return 0
    fi

    # Vérifier la version minimale
    local major minor
    IFS='.' read -r major minor <<< "${python_version}"

    local min_major min_minor
    IFS='.' read -r min_major min_minor <<< "${MIN_PYTHON_VERSION}"

    if [[ "${major}" -lt "${min_major}" ]] || \
       [[ "${major}" -eq "${min_major}" && "${minor}" -lt "${min_minor}" ]]; then
        log WARN "Python ${python_version} trouvé, mais ${MIN_PYTHON_VERSION}+ recommandé"
    else
        log OK "Python ${python_version} trouvé (${python_cmd})"
    fi

    # Exporter pour utilisation ultérieure
    export PYTHON_CMD="${python_cmd}"
}

check_memory() {
    log INFO "Vérification de la mémoire disponible..."

    local total_mem_mb

    if [[ "${OS_TYPE}" == "darwin" ]]; then
        total_mem_mb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 ))
    else
        total_mem_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
    fi

    if [[ "${total_mem_mb}" -lt 1024 ]]; then
        log WARN "Mémoire faible: ${total_mem_mb}MB (2GB+ recommandé)"
    else
        log OK "Mémoire totale: ${total_mem_mb}MB"
    fi
}

check_cpu() {
    log INFO "Vérification du CPU..."

    local cpu_cores

    if [[ "${OS_TYPE}" == "darwin" ]]; then
        cpu_cores=$(sysctl -n hw.ncpu)
    else
        cpu_cores=$(nproc 2>/dev/null || grep -c processor /proc/cpuinfo 2>/dev/null || echo "1")
    fi

    if [[ "${cpu_cores}" -lt 2 ]]; then
        log WARN "Nombre de cœurs CPU faible: ${cpu_cores} (2+ recommandé)"
    else
        log OK "Cœurs CPU: ${cpu_cores}"
    fi

    # Exporter pour configuration des workers
    export CPU_CORES="${cpu_cores}"
}

check_git_repo() {
    log INFO "Vérification du dépôt Git..."

    if [[ ! -d "${PROJECT_ROOT}/.git" ]]; then
        log WARN "Ce n'est pas un dépôt Git"
        return 0
    fi

    # Vérifier s'il y a des modifications non commitées
    if git -C "${PROJECT_ROOT}" status --porcelain | grep -q .; then
        log WARN "Modifications Git non commitées détectées"
    fi

    # Vérifier la branche
    local current_branch
    current_branch=$(git -C "${PROJECT_ROOT}" branch --show-current 2>/dev/null || echo "unknown")
    log OK "Branche Git: ${current_branch}"
}

#===============================================================================
# VÉRIFICATIONS DE SÉCURITÉ
#===============================================================================

check_existing_secrets() {
    log INFO "Vérification des secrets existants..."

    local env_file="${PROJECT_ROOT}/.env"

    if [[ -f "${env_file}" ]]; then
        log WARN "Fichier .env existant trouvé"

        # Vérifier les secrets faibles
        if grep -qE "(CHANGEME|secret|password|123456)" "${env_file}" 2>/dev/null; then
            log ERROR "Secrets faibles détectés dans .env!"
            if [[ "${INSTALL_MODE}" == "prod" ]]; then
                log ERROR "Installation production impossible avec des secrets faibles"
                exit 1
            fi
        fi

        # Vérifier DEBUG en prod
        if [[ "${INSTALL_MODE}" == "prod" ]]; then
            if grep -qE "^DEBUG=true" "${env_file}" 2>/dev/null; then
                log ERROR "DEBUG=true interdit en production"
                exit 1
            fi
        fi

        return 0
    fi

    log OK "Pas de fichier .env existant (sera généré)"
}

check_file_permissions() {
    log INFO "Vérification des permissions de fichiers..."

    # Vérifier que le répertoire projet est accessible
    if [[ ! -r "${PROJECT_ROOT}" ]] || [[ ! -w "${PROJECT_ROOT}" ]]; then
        log ERROR "Permissions insuffisantes sur ${PROJECT_ROOT}"
        exit 1
    fi

    # Vérifier les fichiers sensibles
    local sensitive_files=(
        ".env"
        ".env.local"
        "secrets.json"
        "credentials.json"
    )

    for file in "${sensitive_files[@]}"; do
        local file_path="${PROJECT_ROOT}/${file}"
        if [[ -f "${file_path}" ]]; then
            local perms
            perms=$(stat -c %a "${file_path}" 2>/dev/null || stat -f %Lp "${file_path}" 2>/dev/null)

            if [[ "${perms}" != "600" ]] && [[ "${perms}" != "400" ]]; then
                log WARN "Permissions trop permissives sur ${file}: ${perms} (600 recommandé)"

                if [[ "${INSTALL_MODE}" == "prod" ]]; then
                    chmod 600 "${file_path}"
                    log OK "Permissions corrigées pour ${file}"
                fi
            fi
        fi
    done

    log OK "Vérification des permissions terminée"
}

#===============================================================================
# VÉRIFICATIONS RÉSEAU
#===============================================================================

check_dns_resolution() {
    log INFO "Vérification de la résolution DNS..."

    local test_domains=(
        "github.com"
        "pypi.org"
    )

    for domain in "${test_domains[@]}"; do
        if ! host "${domain}" &> /dev/null && ! nslookup "${domain}" &> /dev/null; then
            log WARN "Résolution DNS échouée pour ${domain}"
        fi
    done

    log OK "Résolution DNS fonctionnelle"
}

check_firewall_status() {
    log INFO "Vérification de l'état du pare-feu..."

    if [[ "${OS_TYPE}" == "linux" ]]; then
        if command -v ufw &> /dev/null; then
            if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
                log INFO "UFW est actif"
            else
                log WARN "UFW n'est pas actif"
            fi
        elif command -v firewall-cmd &> /dev/null; then
            if sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
                log INFO "firewalld est actif"
            else
                log WARN "firewalld n'est pas actif"
            fi
        else
            log WARN "Aucun pare-feu détecté"
        fi
    elif [[ "${OS_TYPE}" == "darwin" ]]; then
        if /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -q "enabled"; then
            log INFO "Pare-feu macOS actif"
        else
            log WARN "Pare-feu macOS inactif"
        fi
    fi
}

#===============================================================================
# VÉRIFICATIONS POSTGRESQL
#===============================================================================

check_postgres_installed() {
    log INFO "Vérification de PostgreSQL..."

    if command -v psql &> /dev/null; then
        local pg_version
        pg_version=$(psql --version 2>/dev/null | awk '{print $3}' | cut -d. -f1)
        log OK "PostgreSQL client installé (version ${pg_version})"

        # Vérifier si le serveur tourne
        if pg_isready -q 2>/dev/null; then
            log OK "Serveur PostgreSQL accessible"
            POSTGRES_LOCAL=false
        else
            log INFO "Serveur PostgreSQL non accessible (sera configuré)"
        fi
    else
        log INFO "PostgreSQL non installé (sera installé)"
    fi
}

#===============================================================================
# RÉSUMÉ DES VÉRIFICATIONS
#===============================================================================

print_check_summary() {
    echo ""
    echo -e "${BOLD}Résumé des vérifications:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  OS:          ${GREEN}${OS_TYPE} (${DISTRO})${NC}"
    echo -e "  Architecture: ${GREEN}${ARCH}${NC}"
    echo -e "  Mode:        ${GREEN}${INSTALL_MODE}${NC}"
    echo -e "  Python:      ${GREEN}${PYTHON_CMD:-'à installer'}${NC}"
    echo -e "  PostgreSQL:  ${GREEN}$(command -v psql &>/dev/null && echo 'installé' || echo 'à installer')${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}
