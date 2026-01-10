#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Génération des secrets
#===============================================================================
# Ce module génère tous les secrets cryptographiques de manière sécurisée
# Aucun secret n'est jamais codé en dur
#===============================================================================

#===============================================================================
# VARIABLES
#===============================================================================

declare -A GENERATED_SECRETS

#===============================================================================
# FONCTIONS DE GÉNÉRATION
#===============================================================================

generate_random_string() {
    # Génère une chaîne aléatoire hexadécimale
    # $1: longueur en bytes (défaut: 32)
    local length="${1:-32}"

    if command -v openssl &> /dev/null; then
        openssl rand -hex "${length}"
    elif [[ -r /dev/urandom ]]; then
        head -c "${length}" /dev/urandom | xxd -p | tr -d '\n'
    else
        # Fallback Python
        python3 -c "import secrets; print(secrets.token_hex(${length}))"
    fi
}

generate_base64_string() {
    # Génère une chaîne aléatoire en base64 (URL-safe)
    # $1: longueur en bytes (défaut: 32)
    local length="${1:-32}"

    if command -v openssl &> /dev/null; then
        openssl rand -base64 "${length}" | tr -d '\n=' | tr '+/' '-_'
    elif [[ -r /dev/urandom ]]; then
        head -c "${length}" /dev/urandom | base64 | tr -d '\n=' | tr '+/' '-_'
    else
        python3 -c "import secrets; import base64; print(base64.urlsafe_b64encode(secrets.token_bytes(${length})).decode().rstrip('='))"
    fi
}

generate_fernet_key() {
    # Génère une clé Fernet valide pour le chiffrement AES-256
    # Fernet requiert une clé base64 de 32 bytes exactement

    if command -v python3 &> /dev/null; then
        python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || \
        python3 -c "import base64; import secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
    else
        # Génération manuelle compatible Fernet
        local raw_bytes
        raw_bytes=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)
        # Fernet attend exactement 32 bytes en base64 urlsafe
        echo "${raw_bytes}" | tr '+/' '-_' | cut -c1-44
    fi
}

generate_db_password() {
    # Génère un mot de passe PostgreSQL sécurisé
    # Évite les caractères problématiques dans les URLs
    local length="${1:-24}"

    # Caractères alphanumériques + quelques spéciaux sûrs pour les URLs
    local chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    local password=""

    if command -v openssl &> /dev/null; then
        # Utiliser OpenSSL pour l'entropie
        password=$(openssl rand -base64 "${length}" | tr -dc "${chars}" | head -c "${length}")
    elif [[ -r /dev/urandom ]]; then
        password=$(tr -dc "${chars}" < /dev/urandom | head -c "${length}")
    else
        password=$(python3 -c "import secrets; import string; chars='${chars}'; print(''.join(secrets.choice(chars) for _ in range(${length})))")
    fi

    echo "${password}"
}

generate_uuid() {
    # Génère un UUID v4
    if command -v uuidgen &> /dev/null; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    elif [[ -r /proc/sys/kernel/random/uuid ]]; then
        cat /proc/sys/kernel/random/uuid
    else
        python3 -c "import uuid; print(uuid.uuid4())"
    fi
}

#===============================================================================
# GÉNÉRATION DE TOUS LES SECRETS
#===============================================================================

generate_secrets() {
    log INFO "Génération des secrets cryptographiques..."

    # 1. SECRET_KEY (JWT et sessions)
    log INFO "  → Génération SECRET_KEY (256 bits)..."
    GENERATED_SECRETS["SECRET_KEY"]=$(generate_random_string 32)

    # 2. BOOTSTRAP_SECRET (Protection bootstrap admin)
    log INFO "  → Génération BOOTSTRAP_SECRET (256 bits)..."
    GENERATED_SECRETS["BOOTSTRAP_SECRET"]=$(generate_random_string 32)

    # 3. ENCRYPTION_KEY (Chiffrement AES-256 Fernet)
    log INFO "  → Génération ENCRYPTION_KEY (Fernet AES-256)..."
    GENERATED_SECRETS["ENCRYPTION_KEY"]=$(generate_fernet_key)

    # 4. POSTGRES_PASSWORD
    log INFO "  → Génération mot de passe PostgreSQL..."
    GENERATED_SECRETS["POSTGRES_PASSWORD"]=$(generate_db_password 24)

    # 5. API_KEY pour intégrations (optionnel)
    log INFO "  → Génération API_KEY..."
    GENERATED_SECRETS["API_KEY"]=$(generate_random_string 24)

    # 6. REDIS_PASSWORD (si Redis est utilisé)
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        log INFO "  → Génération mot de passe Redis..."
        GENERATED_SECRETS["REDIS_PASSWORD"]=$(generate_db_password 20)
    fi

    log OK "Tous les secrets générés avec succès"

    # Afficher un résumé (masqué)
    echo ""
    echo -e "${BOLD}Secrets générés:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for key in "${!GENERATED_SECRETS[@]}"; do
        local value="${GENERATED_SECRETS[$key]}"
        local masked="${value:0:4}...${value: -4}"
        echo "  ${key}: ${masked}"
    done
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

#===============================================================================
# VALIDATION DES SECRETS
#===============================================================================

validate_secret_strength() {
    # Valide qu'un secret est suffisamment fort
    # $1: nom du secret
    # $2: valeur du secret
    # $3: longueur minimale (défaut: 32)

    local name="$1"
    local value="$2"
    local min_length="${3:-32}"

    if [[ -z "${value}" ]]; then
        log ERROR "Secret ${name} est vide"
        return 1
    fi

    if [[ ${#value} -lt ${min_length} ]]; then
        log ERROR "Secret ${name} trop court: ${#value} < ${min_length}"
        return 1
    fi

    # Vérifier l'entropie basique (pas de patterns évidents)
    local weak_patterns=(
        "123456"
        "password"
        "secret"
        "changeme"
        "azalscore"
        "admin"
        "qwerty"
    )

    local lower_value
    lower_value=$(echo "${value}" | tr '[:upper:]' '[:lower:]')

    for pattern in "${weak_patterns[@]}"; do
        if [[ "${lower_value}" == *"${pattern}"* ]]; then
            log ERROR "Secret ${name} contient un pattern faible: ${pattern}"
            return 1
        fi
    done

    return 0
}

validate_all_secrets() {
    log INFO "Validation des secrets générés..."

    local all_valid=true

    # Valider SECRET_KEY (64 chars hex = 32 bytes)
    if ! validate_secret_strength "SECRET_KEY" "${GENERATED_SECRETS["SECRET_KEY"]}" 64; then
        all_valid=false
    fi

    # Valider BOOTSTRAP_SECRET
    if ! validate_secret_strength "BOOTSTRAP_SECRET" "${GENERATED_SECRETS["BOOTSTRAP_SECRET"]}" 64; then
        all_valid=false
    fi

    # Valider ENCRYPTION_KEY (Fernet key = 44 chars)
    if ! validate_secret_strength "ENCRYPTION_KEY" "${GENERATED_SECRETS["ENCRYPTION_KEY"]}" 32; then
        all_valid=false
    fi

    # Valider POSTGRES_PASSWORD
    if ! validate_secret_strength "POSTGRES_PASSWORD" "${GENERATED_SECRETS["POSTGRES_PASSWORD"]}" 16; then
        all_valid=false
    fi

    if [[ "${all_valid}" == "true" ]]; then
        log OK "Tous les secrets sont valides"
        return 0
    else
        log ERROR "Validation des secrets échouée"
        return 1
    fi
}

#===============================================================================
# SAUVEGARDE SÉCURISÉE DES SECRETS
#===============================================================================

save_secrets_backup() {
    # Crée une sauvegarde chiffrée des secrets (optionnel)
    # $1: chemin du fichier de backup

    local backup_file="$1"

    log INFO "Création d'une sauvegarde des secrets..."

    # Créer un fichier temporaire
    local temp_file
    temp_file=$(mktemp)

    # Écrire les secrets au format JSON
    {
        echo "{"
        local first=true
        for key in "${!GENERATED_SECRETS[@]}"; do
            if [[ "${first}" == "true" ]]; then
                first=false
            else
                echo ","
            fi
            printf '  "%s": "%s"' "${key}" "${GENERATED_SECRETS[$key]}"
        done
        echo ""
        echo "}"
    } > "${temp_file}"

    # Demander un mot de passe pour chiffrer
    if [[ "${INTERACTIVE}" == "true" ]]; then
        echo ""
        log INFO "Entrez un mot de passe pour chiffrer la sauvegarde des secrets"
        log INFO "(Gardez ce mot de passe en lieu sûr!)"

        openssl enc -aes-256-cbc -salt -pbkdf2 -in "${temp_file}" -out "${backup_file}" 2>/dev/null

        if [[ $? -eq 0 ]]; then
            chmod 600 "${backup_file}"
            log OK "Sauvegarde chiffrée créée: ${backup_file}"
        else
            log WARN "Échec de la création de la sauvegarde chiffrée"
        fi
    fi

    # Supprimer le fichier temporaire de manière sécurisée
    shred -u "${temp_file}" 2>/dev/null || rm -f "${temp_file}"
}

#===============================================================================
# EXPORT DES SECRETS
#===============================================================================

get_secret() {
    # Récupère un secret généré
    # $1: nom du secret
    local name="$1"
    echo "${GENERATED_SECRETS[$name]:-}"
}

export_secrets_to_env() {
    # Exporte les secrets comme variables d'environnement
    # (pour usage temporaire pendant l'installation)

    for key in "${!GENERATED_SECRETS[@]}"; do
        export "AZALS_${key}=${GENERATED_SECRETS[$key]}"
    done
}
