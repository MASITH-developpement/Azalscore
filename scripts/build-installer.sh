#!/bin/bash
# ==============================================================================
# AZALSCORE - Script de Creation du Package d'Installation
# ==============================================================================
# Cree un package autonome telecharegable pour installation sans GitHub.
#
# USAGE:
#   ./scripts/build-installer.sh
#
# OUTPUT:
#   dist/azalscore-installer.tar.gz
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
DIST_DIR="${ROOT_DIR}/dist"
PACKAGE_NAME="azalscore-installer"
VERSION=$(date '+%Y%m%d')

echo "======================================"
echo "AZALSCORE - Build Installer Package"
echo "======================================"
echo ""

# Nettoyage
rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}/${PACKAGE_NAME}"

echo "1/5 - Copie des fichiers sources..."

# Fichiers backend
cp -r "${ROOT_DIR}/app" "${DIST_DIR}/${PACKAGE_NAME}/"
cp -r "${ROOT_DIR}/alembic" "${DIST_DIR}/${PACKAGE_NAME}/"
cp "${ROOT_DIR}/alembic.ini" "${DIST_DIR}/${PACKAGE_NAME}/"
cp "${ROOT_DIR}/requirements.txt" "${DIST_DIR}/${PACKAGE_NAME}/"
cp "${ROOT_DIR}/Dockerfile" "${DIST_DIR}/${PACKAGE_NAME}/"
cp "${ROOT_DIR}/Dockerfile.prod" "${DIST_DIR}/${PACKAGE_NAME}/"

# Fichiers frontend
cp -r "${ROOT_DIR}/frontend" "${DIST_DIR}/${PACKAGE_NAME}/"

# Configuration Docker
cp "${ROOT_DIR}/docker-compose.yml" "${DIST_DIR}/${PACKAGE_NAME}/"
cp "${ROOT_DIR}/docker-compose.prod.yml" "${DIST_DIR}/${PACKAGE_NAME}/"

# Installer
cp -r "${ROOT_DIR}/installer/"* "${DIST_DIR}/${PACKAGE_NAME}/"

# Tests
cp -r "${ROOT_DIR}/tests" "${DIST_DIR}/${PACKAGE_NAME}/"

# Scripts
mkdir -p "${DIST_DIR}/${PACKAGE_NAME}/scripts"
cp "${ROOT_DIR}/scripts/bootstrap_production.py" "${DIST_DIR}/${PACKAGE_NAME}/scripts/"
cp -r "${ROOT_DIR}/scripts/automation" "${DIST_DIR}/${PACKAGE_NAME}/scripts/" 2>/dev/null || true
cp -r "${ROOT_DIR}/scripts/install" "${DIST_DIR}/${PACKAGE_NAME}/scripts/" 2>/dev/null || true

# Infrastructure
cp -r "${ROOT_DIR}/infra" "${DIST_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true

# Exemples de configuration
cp "${ROOT_DIR}/.env.example" "${DIST_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true
cp "${ROOT_DIR}/.env.production.example" "${DIST_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true

echo "2/5 - Nettoyage des fichiers inutiles..."

# Suppression des fichiers inutiles
find "${DIST_DIR}/${PACKAGE_NAME}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${DIST_DIR}/${PACKAGE_NAME}" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find "${DIST_DIR}/${PACKAGE_NAME}" -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true
find "${DIST_DIR}/${PACKAGE_NAME}" -type f -name "*.pyc" -delete 2>/dev/null || true
find "${DIST_DIR}/${PACKAGE_NAME}" -type f -name ".DS_Store" -delete 2>/dev/null || true
find "${DIST_DIR}/${PACKAGE_NAME}" -type f -name "*.log" -delete 2>/dev/null || true

echo "3/5 - Creation du fichier VERSION..."

# Version
cat > "${DIST_DIR}/${PACKAGE_NAME}/VERSION" << EOF
AZALSCORE Installer Package
============================
Version: ${VERSION}
Build Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

Checksums generated at build time.
EOF

echo "4/5 - Creation de l'archive..."

# Creation de l'archive
cd "${DIST_DIR}"
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

# Checksum
cd "${DIST_DIR}"
sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.sha256"

echo "5/5 - Verification..."

# Verification
ARCHIVE_SIZE=$(du -h "${DIST_DIR}/${PACKAGE_NAME}.tar.gz" | cut -f1)
CHECKSUM=$(cat "${DIST_DIR}/${PACKAGE_NAME}.tar.gz.sha256" | cut -d' ' -f1)

echo ""
echo "======================================"
echo "Package cree avec succes!"
echo "======================================"
echo ""
echo "Fichier: ${DIST_DIR}/${PACKAGE_NAME}.tar.gz"
echo "Taille:  ${ARCHIVE_SIZE}"
echo "SHA256:  ${CHECKSUM}"
echo ""
echo "Pour installer:"
echo "  tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "  cd ${PACKAGE_NAME}"
echo "  ./install.sh"
echo ""
