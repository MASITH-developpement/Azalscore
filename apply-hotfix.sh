#!/bin/bash
################################################################################
# AZALSCORE - HOTFIX P0 BUGS
# Script de correction automatique des bugs critiques
# Date: 2026-01-23
# Bugs: P0-002 (CRUD users), P0-001 (Dashboard admin)
################################################################################

set -e  # Exit on error

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
FRONTEND_DIR="/home/ubuntu/azalscore/frontend"
ADMIN_FILE="${FRONTEND_DIR}/src/modules/admin/index.tsx"
BACKUP_SUFFIX=".backup-$(date +%Y%m%d-%H%M%S)"

################################################################################
# FUNCTIONS
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_file_exists() {
    if [ ! -f "$1" ]; then
        log_error "Fichier non trouvé: $1"
        exit 1
    fi
}

################################################################################
# PRE-CHECKS
################################################################################

log_info "Vérification pré-requis..."

# Check working directory
if [ ! -d "${FRONTEND_DIR}" ]; then
    log_error "Répertoire frontend non trouvé: ${FRONTEND_DIR}"
    exit 1
fi

# Check admin file exists
check_file_exists "${ADMIN_FILE}"
log_success "Fichier admin trouvé"

################################################################################
# BACKUP
################################################################################

log_info "Création backup..."
cp "${ADMIN_FILE}" "${ADMIN_FILE}${BACKUP_SUFFIX}"
log_success "Backup créé: ${ADMIN_FILE}${BACKUP_SUFFIX}"

################################################################################
# P0-002: FIX CRUD USERS ENDPOINTS
################################################################################

log_info "Application fix P0-002 (CRUD users)..."

# Fix 1: Ligne 301 - useCreateUser
log_info "  - Fix création utilisateur (ligne 301)"
sed -i "301s|/v1/admin/users|/v1/iam/users|" "${ADMIN_FILE}"

# Fix 2: Ligne 311 - useUpdateUserStatus
log_info "  - Fix modification statut (ligne 311)"
sed -i "311s|/v1/admin/users|/v1/iam/users|" "${ADMIN_FILE}"

# Vérification
if grep -q "api.post('/v1/iam/users'" "${ADMIN_FILE}" && \
   grep -q "api.patch(\`/v1/iam/users/" "${ADMIN_FILE}"; then
    log_success "P0-002 corrigé avec succès"
else
    log_error "P0-002: Correction échouée - vérifier manuellement"
    exit 1
fi

################################################################################
# P0-001: FIX DASHBOARD ADMIN ENDPOINT
################################################################################

log_info "Application fix P0-001 (Dashboard admin)..."

# Trouver la ligne exacte du dashboard
DASHBOARD_LINE=$(grep -n "api.get.*'/v1/admin/dashboard'" "${ADMIN_FILE}" | cut -d: -f1)

if [ -z "$DASHBOARD_LINE" ]; then
    log_warning "Endpoint dashboard non trouvé à l'emplacement attendu"
    log_info "Recherche alternative..."
    DASHBOARD_LINE=$(grep -n "/v1/admin/dashboard" "${ADMIN_FILE}" | head -1 | cut -d: -f1)
fi

if [ -n "$DASHBOARD_LINE" ]; then
    log_info "  - Fix dashboard (ligne ${DASHBOARD_LINE})"
    sed -i "${DASHBOARD_LINE}s|/v1/admin/dashboard|/v1/cockpit/dashboard|" "${ADMIN_FILE}"

    # Vérification
    if grep -q "/v1/cockpit/dashboard" "${ADMIN_FILE}"; then
        log_success "P0-001 corrigé avec succès"
    else
        log_error "P0-001: Correction échouée"
        exit 1
    fi
else
    log_error "Impossible de trouver l'appel dashboard"
    log_warning "Correction manuelle requise pour P0-001"
fi

################################################################################
# VERIFICATION GLOBALE
################################################################################

log_info "Vérification globale des corrections..."

# Check plus d'appels /v1/admin/users ou /v1/admin/dashboard
ADMIN_USERS_COUNT=$(grep -c "/v1/admin/users" "${ADMIN_FILE}" || true)
ADMIN_DASHBOARD_COUNT=$(grep -c "/v1/admin/dashboard" "${ADMIN_FILE}" || true)

if [ "$ADMIN_USERS_COUNT" -gt 0 ]; then
    log_warning "Attention: ${ADMIN_USERS_COUNT} occurrence(s) restante(s) de '/v1/admin/users'"
    log_info "Lignes concernées:"
    grep -n "/v1/admin/users" "${ADMIN_FILE}" || true
fi

if [ "$ADMIN_DASHBOARD_COUNT" -gt 0 ]; then
    log_warning "Attention: ${ADMIN_DASHBOARD_COUNT} occurrence(s) restante(s) de '/v1/admin/dashboard'"
    log_info "Lignes concernées:"
    grep -n "/v1/admin/dashboard" "${ADMIN_FILE}" || true
fi

# Check nouveaux endpoints corrects
IAM_USERS_COUNT=$(grep -c "/v1/iam/users" "${ADMIN_FILE}" || true)
COCKPIT_DASHBOARD_COUNT=$(grep -c "/v1/cockpit/dashboard" "${ADMIN_FILE}" || true)

log_info "Résumé endpoints:"
log_info "  - /v1/iam/users: ${IAM_USERS_COUNT} occurrence(s)"
log_info "  - /v1/cockpit/dashboard: ${COCKPIT_DASHBOARD_COUNT} occurrence(s)"

################################################################################
# DIFF SUMMARY
################################################################################

log_info "Aperçu des changements:"
echo ""
diff -u "${ADMIN_FILE}${BACKUP_SUFFIX}" "${ADMIN_FILE}" || true
echo ""

################################################################################
# NEXT STEPS
################################################################################

log_success "✅ Corrections appliquées avec succès!"
echo ""
log_info "PROCHAINES ÉTAPES:"
echo ""
echo "1. Vérifier les changements:"
echo "   git diff ${ADMIN_FILE}"
echo ""
echo "2. Tester en local:"
echo "   cd ${FRONTEND_DIR}"
echo "   npm run dev"
echo "   # → Ouvrir http://localhost:5173/admin"
echo "   # → Tester création utilisateur"
echo "   # → Vérifier dashboard affiche vraies métriques"
echo ""
echo "3. Si tests OK, commit:"
echo "   git add ${ADMIN_FILE}"
echo "   git commit -m \"fix(admin): Corriger endpoints CRUD users et dashboard (P0-002, P0-001)\""
echo ""
echo "4. Si tests KO, restaurer backup:"
echo "   cp ${ADMIN_FILE}${BACKUP_SUFFIX} ${ADMIN_FILE}"
echo ""

log_info "Backup disponible: ${ADMIN_FILE}${BACKUP_SUFFIX}"
echo ""

################################################################################
# VALIDATION CHECKLIST
################################################################################

log_warning "⚠️  CHECKLIST VALIDATION MANUELLE:"
echo ""
echo "  [ ] Créer un utilisateur via /admin → Status 201 (pas 404)"
echo "  [ ] Modifier statut utilisateur → Status 200 (pas 404)"
echo "  [ ] Dashboard affiche métriques > 0 (pas tout à 0)"
echo "  [ ] Console: Aucune erreur 404 sur /v1/admin/*"
echo ""

log_info "Temps total: ~5 minutes de corrections + 20 minutes de tests"
echo ""
log_success "Script terminé."
