#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Installation Python et environnement virtuel
#===============================================================================
# Ce module installe Python et configure l'environnement virtuel
#===============================================================================

#===============================================================================
# VARIABLES
#===============================================================================

readonly VENV_DIR="${PROJECT_ROOT}/venv"
readonly REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
readonly REQUIREMENTS_DEV_FILE="${PROJECT_ROOT}/requirements-dev.txt"

#===============================================================================
# INSTALLATION PYTHON
#===============================================================================

setup_python() {
    log INFO "Configuration de Python..."

    install_python_if_needed
    create_virtual_environment
    install_python_dependencies
}

install_python_if_needed() {
    log INFO "Vérification de Python..."

    # Chercher Python dans l'ordre de préférence
    local python_candidates=(
        "python3.12"
        "python3.11"
        "python3"
    )

    local python_cmd=""
    local python_version=""

    for cmd in "${python_candidates[@]}"; do
        if command -v "${cmd}" &> /dev/null; then
            local version
            version=$("${cmd}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)

            # Vérifier que la version est >= 3.11
            local major minor
            IFS='.' read -r major minor <<< "${version}"

            if [[ "${major}" -ge 3 ]] && [[ "${minor}" -ge 11 ]]; then
                python_cmd="${cmd}"
                python_version="${version}"
                break
            fi
        fi
    done

    if [[ -z "${python_cmd}" ]]; then
        log INFO "Installation de Python 3.12..."

        case "${DISTRO}" in
            debian|ubuntu|linuxmint|pop)
                install_python_debian
                ;;
            fedora|centos|rhel|rocky|almalinux)
                install_python_fedora
                ;;
            arch|manjaro)
                install_python_arch
                ;;
            macos)
                install_python_macos
                ;;
            *)
                log ERROR "Installation automatique de Python non supportée pour ${DISTRO}"
                log INFO "Veuillez installer Python 3.11+ manuellement"
                exit 1
                ;;
        esac

        # Vérifier l'installation
        for cmd in python3.12 python3.11 python3; do
            if command -v "${cmd}" &> /dev/null; then
                python_cmd="${cmd}"
                python_version=$("${cmd}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
                break
            fi
        done
    fi

    if [[ -z "${python_cmd}" ]]; then
        log ERROR "Python 3.11+ requis mais non trouvé"
        exit 1
    fi

    # Exporter pour utilisation ultérieure
    export PYTHON_CMD="${python_cmd}"
    export PYTHON_VERSION="${python_version}"

    log OK "Python ${python_version} disponible (${python_cmd})"
}

install_python_debian() {
    log INFO "Installation de Python sur Debian/Ubuntu..."

    # Ajouter le PPA deadsnakes pour les dernières versions Python
    if ! grep -q "deadsnakes" /etc/apt/sources.list.d/*.list 2>/dev/null; then
        sudo apt-get install -y -qq software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
        sudo apt-get update -qq
    fi

    # Installer Python 3.12
    sudo apt-get install -y -qq python3.12 python3.12-venv python3.12-dev python3-pip

    # Mettre à jour les alternatives
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 2>/dev/null || true

    log OK "Python 3.12 installé"
}

install_python_fedora() {
    log INFO "Installation de Python sur Fedora/RHEL..."

    sudo dnf install -y -q python3.12 python3.12-devel python3-pip

    log OK "Python 3.12 installé"
}

install_python_arch() {
    log INFO "Installation de Python sur Arch Linux..."

    sudo pacman -Sy --noconfirm python python-pip

    log OK "Python installé"
}

install_python_macos() {
    log INFO "Installation de Python sur macOS..."

    brew install python@3.12

    # Ajouter au PATH
    if [[ -d "/opt/homebrew/opt/python@3.12/bin" ]]; then
        export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"
    elif [[ -d "/usr/local/opt/python@3.12/bin" ]]; then
        export PATH="/usr/local/opt/python@3.12/bin:$PATH"
    fi

    log OK "Python 3.12 installé"
}

#===============================================================================
# ENVIRONNEMENT VIRTUEL
#===============================================================================

create_virtual_environment() {
    log INFO "Configuration de l'environnement virtuel..."

    # Supprimer l'ancien venv si demandé
    if [[ -d "${VENV_DIR}" ]]; then
        log INFO "Environnement virtuel existant trouvé"

        if [[ "${INTERACTIVE}" == "true" ]]; then
            read -rp "Recréer l'environnement virtuel? [y/N] " response
            if [[ "${response,,}" =~ ^(y|yes)$ ]]; then
                log INFO "Suppression de l'ancien environnement virtuel..."
                rm -rf "${VENV_DIR}"
            else
                log INFO "Conservation de l'environnement virtuel existant"
                activate_virtual_environment
                return
            fi
        fi
    fi

    # Créer le nouvel environnement virtuel
    log INFO "Création de l'environnement virtuel..."

    "${PYTHON_CMD}" -m venv "${VENV_DIR}"

    if [[ ! -d "${VENV_DIR}" ]]; then
        log ERROR "Échec de la création de l'environnement virtuel"
        exit 1
    fi

    activate_virtual_environment

    # Mettre à jour pip
    log INFO "Mise à jour de pip..."
    pip install --upgrade pip setuptools wheel --quiet

    log OK "Environnement virtuel créé: ${VENV_DIR}"
}

activate_virtual_environment() {
    log INFO "Activation de l'environnement virtuel..."

    # Déterminer le chemin d'activation
    local activate_script=""

    if [[ -f "${VENV_DIR}/bin/activate" ]]; then
        activate_script="${VENV_DIR}/bin/activate"
    elif [[ -f "${VENV_DIR}/Scripts/activate" ]]; then
        # Windows Git Bash
        activate_script="${VENV_DIR}/Scripts/activate"
    else
        log ERROR "Script d'activation non trouvé"
        exit 1
    fi

    # Activer
    # shellcheck source=/dev/null
    source "${activate_script}"

    # Vérifier l'activation
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        log ERROR "Échec de l'activation de l'environnement virtuel"
        exit 1
    fi

    log OK "Environnement virtuel activé"
}

#===============================================================================
# INSTALLATION DES DÉPENDANCES
#===============================================================================

install_python_dependencies() {
    log INFO "Installation des dépendances Python..."

    # S'assurer que l'environnement virtuel est actif
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        activate_virtual_environment
    fi

    # Installer les dépendances principales
    if [[ -f "${REQUIREMENTS_FILE}" ]]; then
        log INFO "Installation des dépendances depuis requirements.txt..."

        pip install -r "${REQUIREMENTS_FILE}" --quiet

        if [[ $? -ne 0 ]]; then
            log ERROR "Échec de l'installation des dépendances"
            exit 1
        fi

        log OK "Dépendances principales installées"
    else
        log ERROR "Fichier requirements.txt non trouvé"
        exit 1
    fi

    # Installer les dépendances de développement en mode dev
    if [[ "${INSTALL_MODE}" == "dev" ]] && [[ -f "${REQUIREMENTS_DEV_FILE}" ]]; then
        log INFO "Installation des dépendances de développement..."

        pip install -r "${REQUIREMENTS_DEV_FILE}" --quiet

        log OK "Dépendances de développement installées"
    fi

    # Installer les hooks pre-commit en mode dev
    if [[ "${INSTALL_MODE}" == "dev" ]] && command -v pre-commit &> /dev/null; then
        log INFO "Configuration des hooks pre-commit..."

        cd "${PROJECT_ROOT}" || exit 1
        pre-commit install --install-hooks 2>/dev/null || true

        log OK "Hooks pre-commit configurés"
    fi
}

#===============================================================================
# VÉRIFICATION
#===============================================================================

verify_python_installation() {
    log INFO "Vérification de l'installation Python..."

    # Activer le venv
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        activate_virtual_environment
    fi

    # Vérifier les imports critiques
    local critical_packages=(
        "fastapi"
        "uvicorn"
        "sqlalchemy"
        "pydantic"
        "psycopg2"
        "alembic"
    )

    local failed=()

    for package in "${critical_packages[@]}"; do
        if ! python -c "import ${package}" 2>/dev/null; then
            failed+=("${package}")
        fi
    done

    if [[ ${#failed[@]} -gt 0 ]]; then
        log ERROR "Packages manquants: ${failed[*]}"
        return 1
    fi

    log OK "Tous les packages critiques sont installés"

    # Afficher les versions
    echo ""
    echo -e "${BOLD}Packages installés:${NC}"
    pip list --format=columns 2>/dev/null | head -20
    echo "..."
    echo ""
}

#===============================================================================
# SCRIPTS D'ACTIVATION
#===============================================================================

create_activation_script() {
    # Crée un script pour activer facilement l'environnement
    local script_path="${PROJECT_ROOT}/activate.sh"

    cat > "${script_path}" << 'EOF'
#!/usr/bin/env bash
# Script d'activation de l'environnement AZALSCORE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"
    echo "✓ Environnement AZALSCORE activé"
    echo "  Python: $(python --version)"
    echo "  Venv: ${VIRTUAL_ENV}"
else
    echo "✗ Environnement virtuel non trouvé"
    echo "  Exécutez d'abord: ./scripts/install/install.sh"
fi
EOF

    chmod +x "${script_path}"
    log OK "Script d'activation créé: ${script_path}"
}
