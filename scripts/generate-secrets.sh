#!/bin/bash
# ============================================================
# AZALS - Générateur de Secrets Sécurisés
# ============================================================
# Ce script génère tous les secrets nécessaires pour .env.production
# Les secrets sont affichés sur stdout - copiez-les dans votre gestionnaire de secrets
# ============================================================

set -e

echo "============================================================"
echo "AZALS - Génération de Secrets Sécurisés"
echo "============================================================"
echo ""
echo "ATTENTION: Les anciens secrets sont COMPROMIS et doivent être révoqués!"
echo "Actions requises AVANT d'utiliser ces nouveaux secrets:"
echo "  1. Révoquer la clé OpenAI: https://platform.openai.com/api-keys"
echo "  2. Révoquer la clé Anthropic: https://console.anthropic.com/"
echo "  3. Révoquer les clés Stripe: https://dashboard.stripe.com/apikeys"
echo "  4. Changer le mot de passe PostgreSQL"
echo "  5. Invalider toutes les sessions JWT actives"
echo ""
echo "============================================================"
echo ""

# Fonction pour générer un secret base64
generate_base64() {
    openssl rand -base64 "$1" | tr -d '\n'
}

# Fonction pour générer une clé Fernet
generate_fernet_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || \
    openssl rand -base64 32 | tr -d '\n'
}

# Fonction pour générer un mot de passe alphanumérique
generate_password() {
    openssl rand -base64 "$1" | tr -dc 'a-zA-Z0-9' | head -c "$1"
}

echo "# Copiez ces valeurs dans votre gestionnaire de secrets ou .env.production"
echo "# Généré le: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

echo "# PostgreSQL"
POSTGRES_PWD=$(generate_base64 32)
echo "POSTGRES_PASSWORD=$POSTGRES_PWD"
echo "DATABASE_URL=postgresql+psycopg2://azals_user:$POSTGRES_PWD@postgres:5432/azals"
echo ""

echo "# Sécurité JWT/Sessions"
echo "SECRET_KEY=$(generate_base64 64)"
echo "BOOTSTRAP_SECRET=$(generate_base64 64)"
echo "ENCRYPTION_KEY=$(generate_fernet_key)"
echo ""

echo "# Grafana"
echo "GRAFANA_PASSWORD=$(generate_password 20)"
echo "GF_SECURITY_ADMIN_PASSWORD=$(generate_password 20)"
echo ""

echo "# Tenant Admin (MASITH)"
echo "MASITH_ADMIN_PASSWORD=$(generate_password 16)!"
echo ""

echo "============================================================"
echo "RAPPEL: Vous devez également configurer manuellement:"
echo "  - OPENAI_API_KEY (nouvelle clé depuis OpenAI)"
echo "  - ANTHROPIC_API_KEY (nouvelle clé depuis Anthropic)"
echo "  - STRIPE_SECRET_KEY (nouvelle clé depuis Stripe)"
echo "  - STRIPE_PUBLISHABLE_KEY (nouvelle clé depuis Stripe)"
echo "  - STRIPE_WEBHOOK_SECRET (nouveau secret depuis Stripe)"
echo "  - SMTP_USER et SMTP_PASSWORD (depuis Brevo)"
echo "============================================================"
