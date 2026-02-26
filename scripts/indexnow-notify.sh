#!/bin/bash
# =============================================================================
# AZALSCORE - IndexNow Notification Script
# Notifie les moteurs de recherche des pages mises à jour
# Usage: ./indexnow-notify.sh [url1] [url2] ...
#        ./indexnow-notify.sh --all  (notifie toutes les pages du sitemap)
# =============================================================================

set -e

DOMAIN="azalscore.com"
KEY="azalscore-indexnow-2026-key"
KEY_LOCATION="https://${DOMAIN}/${KEY}.txt"
API_ENDPOINT="https://api.indexnow.org/IndexNow"

# Couleurs pour output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[IndexNow]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Liste des URLs principales à notifier
MAIN_URLS=(
    "https://azalscore.com/"
    "https://azalscore.com/features"
    "https://azalscore.com/features/crm"
    "https://azalscore.com/features/facturation"
    "https://azalscore.com/features/comptabilite"
    "https://azalscore.com/features/inventaire"
    "https://azalscore.com/features/rh"
    "https://azalscore.com/features/tresorerie"
    "https://azalscore.com/features/pos"
    "https://azalscore.com/features/interventions"
    "https://azalscore.com/pricing"
    "https://azalscore.com/essai-gratuit"
    "https://azalscore.com/demo"
    "https://azalscore.com/blog"
    "https://azalscore.com/comparatif/odoo"
    "https://azalscore.com/comparatif/sage"
    "https://azalscore.com/comparatif/ebp"
    "https://azalscore.com/secteurs/commerce"
    "https://azalscore.com/secteurs/services"
    "https://azalscore.com/secteurs/industrie"
)

submit_urls() {
    local urls=("$@")
    local url_list=""

    for url in "${urls[@]}"; do
        url_list+="\"$url\","
    done
    # Remove trailing comma
    url_list="${url_list%,}"

    log "Soumission de ${#urls[@]} URLs à IndexNow..."

    response=$(curl -s -w "\n%{http_code}" -X POST "$API_ENDPOINT" \
        -H "Content-Type: application/json; charset=utf-8" \
        -d "{
            \"host\": \"$DOMAIN\",
            \"key\": \"$KEY\",
            \"keyLocation\": \"$KEY_LOCATION\",
            \"urlList\": [$url_list]
        }")

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ] || [ "$http_code" = "202" ]; then
        success "URLs soumises avec succès (HTTP $http_code)"
    else
        echo "Erreur: HTTP $http_code"
        echo "$response" | head -n-1
        exit 1
    fi
}

# Main
if [ "$1" = "--all" ]; then
    log "Notification de toutes les pages principales..."
    submit_urls "${MAIN_URLS[@]}"
elif [ $# -gt 0 ]; then
    log "Notification des URLs spécifiées..."
    submit_urls "$@"
else
    echo "Usage: $0 [url1] [url2] ..."
    echo "       $0 --all"
    echo ""
    echo "Exemples:"
    echo "  $0 https://azalscore.com/blog/nouvel-article"
    echo "  $0 --all"
    exit 1
fi

success "Notification IndexNow terminée"
