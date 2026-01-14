#!/bin/bash
# ============================================================
# AZALSCORE - Script d'audit branding
# Vérifie la conformité du logo et de la charte graphique
# ============================================================

FRONTEND_DIR="./frontend/src"
PUBLIC_DIR="./frontend/public"
DOCS_DIR="./docs"

echo "=============================================="
echo "AZALSCORE - Audit de conformité branding"
echo "=============================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

check_pass() {
    echo "[PASS] $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

check_fail() {
    echo "[FAIL] $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_warn() {
    echo "[WARN] $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

# ============================================================
# 1. VÉRIFICATION DES ASSETS
# ============================================================
echo "1. Vérification des assets logo..."
echo "---"

# Logo component
if [ -f "$FRONTEND_DIR/components/Logo/AzalscoreLogo.tsx" ]; then
    check_pass "Composant Logo présent"
else
    check_fail "Composant Logo manquant"
fi

# Favicons
for favicon in "favicon.png" "favicon-16x16.png" "favicon-48x48.png"; do
    if [ -f "$PUBLIC_DIR/$favicon" ]; then
        check_pass "Favicon $favicon présent"
    else
        check_fail "Favicon $favicon manquant"
    fi
done

# PWA assets
for pwa in "pwa-192x192.png" "pwa-512x512.png" "apple-touch-icon.png"; do
    if [ -f "$PUBLIC_DIR/$pwa" ]; then
        check_pass "Asset PWA $pwa présent"
    else
        check_fail "Asset PWA $pwa manquant"
    fi
done

echo ""

# ============================================================
# 2. INTÉGRATION DANS LES COMPOSANTS
# ============================================================
echo "2. Vérification de l'intégration..."
echo "---"

# AuthLayout (login)
if grep -q "AzalscoreLogo" "$FRONTEND_DIR/ui-engine/layout/index.tsx" 2>/dev/null; then
    check_pass "Logo intégré dans AuthLayout"
else
    check_fail "Logo absent dans AuthLayout"
fi

# MainLayout (header)
if grep -q "azals-header__logo" "$FRONTEND_DIR/ui-engine/layout/index.tsx" 2>/dev/null; then
    check_pass "Logo intégré dans le header"
else
    check_fail "Logo absent dans le header"
fi

# App loading screen
if grep -q "AzalscoreLogo" "$FRONTEND_DIR/App.tsx" 2>/dev/null; then
    check_pass "Logo intégré dans l'écran de chargement"
else
    check_fail "Logo absent dans l'écran de chargement"
fi

# NotFound page (404)
if grep -q "AzalscoreLogo" "$FRONTEND_DIR/pages/NotFound.tsx" 2>/dev/null; then
    check_pass "Logo intégré dans la page 404"
else
    check_fail "Logo absent dans la page 404"
fi

# About page
if [ -f "$FRONTEND_DIR/pages/About.tsx" ]; then
    if grep -q "AzalscoreLogo" "$FRONTEND_DIR/pages/About.tsx" 2>/dev/null; then
        check_pass "Logo intégré dans la page À propos"
    else
        check_fail "Logo absent dans la page À propos"
    fi
else
    check_fail "Page À propos manquante"
fi

echo ""

# ============================================================
# 3. VÉRIFICATION DES EMPLACEMENTS INTERDITS
# ============================================================
echo "3. Vérification des zones interdites..."
echo "---"

# Vérifier que le logo n'est pas dans les dashboards (corps)
DASHBOARD_FILES=$(find "$FRONTEND_DIR/modules" -name "*.tsx" -type f 2>/dev/null || true)
DASHBOARD_VIOLATIONS=0

for file in $DASHBOARD_FILES; do
    # Ignorer les fichiers de layout
    if [[ ! "$file" =~ "layout" ]] && [[ ! "$file" =~ "Layout" ]]; then
        if grep -q "AzalscoreLogo" "$file" 2>/dev/null; then
            # Vérifier si c'est dans un header/footer acceptable
            if ! grep -B5 "AzalscoreLogo" "$file" | grep -qE "(header|footer|Header|Footer)" 2>/dev/null; then
                check_warn "Logo potentiellement mal placé: $file"
                DASHBOARD_VIOLATIONS=$((DASHBOARD_VIOLATIONS + 1))
            fi
        fi
    fi
done

if [ $DASHBOARD_VIOLATIONS -eq 0 ]; then
    check_pass "Aucun logo dans les zones de données"
fi

echo ""

# ============================================================
# 4. DOCUMENTATION
# ============================================================
echo "4. Vérification de la documentation..."
echo "---"

if [ -f "$DOCS_DIR/BRAND_GUIDELINES.md" ]; then
    check_pass "Charte d'usage du logo présente"
else
    check_fail "Charte d'usage du logo manquante"
fi

if [ -f "README.md" ]; then
    check_pass "README principal présent"
else
    check_warn "README principal manquant"
fi

echo ""

# ============================================================
# 5. ACCESSIBILITÉ
# ============================================================
echo "5. Vérification accessibilité..."
echo "---"

# Vérifier les attributs alt/aria dans le composant Logo
if grep -q 'aria-label' "$FRONTEND_DIR/components/Logo/AzalscoreLogo.tsx" 2>/dev/null; then
    check_pass "Attribut aria-label présent dans le composant"
else
    check_warn "Attribut aria-label manquant"
fi

if grep -q 'role="img"' "$FRONTEND_DIR/components/Logo/AzalscoreLogo.tsx" 2>/dev/null; then
    check_pass "Role img présent dans le composant"
else
    check_warn "Role img manquant"
fi

echo ""

# ============================================================
# RÉSUMÉ
# ============================================================
echo "=============================================="
echo "RÉSUMÉ DE L'AUDIT"
echo "=============================================="
echo ""
echo "  Succès  : $PASS_COUNT"
echo "  Échecs  : $FAIL_COUNT"
echo "  Avert.  : $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "STATUS: CONFORME"
    echo "Le branding AZALSCORE est correctement intégré."
    exit 0
else
    echo "STATUS: NON CONFORME"
    echo "Des corrections sont nécessaires."
    exit 1
fi
