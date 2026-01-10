#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Résumé final
#===============================================================================
# Ce module affiche un résumé de l'installation
#===============================================================================

#===============================================================================
# RÉSUMÉ FINAL
#===============================================================================

print_summary() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}   AZALSCORE - Résumé de l'installation${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    print_system_info
    print_installation_info
    print_security_info
    print_next_steps
    print_useful_commands
}

#===============================================================================
# INFORMATIONS SYSTÈME
#===============================================================================

print_system_info() {
    echo -e "${BOLD}Système:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  OS:              ${OS_TYPE} (${DISTRO})"
    echo "  Architecture:    ${ARCH}"
    echo "  Hostname:        $(hostname)"
    echo "  Date:            $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

#===============================================================================
# INFORMATIONS D'INSTALLATION
#===============================================================================

print_installation_info() {
    echo -e "${BOLD}Installation:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Mode:            ${INSTALL_MODE}"
    echo "  Répertoire:      ${PROJECT_ROOT}"
    echo "  Python:          ${PYTHON_CMD:-python3} (${PYTHON_VERSION:-unknown})"
    echo "  Venv:            ${PROJECT_ROOT}/venv"
    echo ""

    # Base de données
    echo -e "${BOLD}Base de données:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Type:            PostgreSQL"
    echo "  Base:            azals"
    echo "  Utilisateur:     azals_user"

    if [[ "${POSTGRES_LOCAL}" == "true" ]]; then
        echo "  Hôte:            localhost:5432"
    else
        echo "  Hôte:            (externe)"
    fi
    echo ""

    # API
    echo -e "${BOLD}API:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ "${INSTALL_MODE}" == "dev" ]]; then
        echo "  URL:             http://localhost:8000"
        echo "  Documentation:   http://localhost:8000/docs"
        echo "  Workers:         1 (hot-reload activé)"
    else
        echo "  URL:             http://127.0.0.1:8000"
        echo "  Documentation:   Désactivée (production)"
        echo "  Workers:         ${CPU_CORES:-4}"
    fi
    echo ""
}

#===============================================================================
# INFORMATIONS DE SÉCURITÉ
#===============================================================================

print_security_info() {
    echo -e "${BOLD}Sécurité:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Vérifications de sécurité
    local security_checks=()

    # .env existe et sécurisé
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        local env_perms
        env_perms=$(stat -c %a "${PROJECT_ROOT}/.env" 2>/dev/null || stat -f %Lp "${PROJECT_ROOT}/.env" 2>/dev/null)
        if [[ "${env_perms}" == "600" ]]; then
            security_checks+=("${GREEN}✓${NC} Fichier .env sécurisé (permissions 600)")
        else
            security_checks+=("${YELLOW}!${NC} Fichier .env permissions: ${env_perms} (600 recommandé)")
        fi
    fi

    # Secrets générés
    if [[ -n "${GENERATED_SECRETS["SECRET_KEY"]:-}" ]]; then
        security_checks+=("${GREEN}✓${NC} Secrets générés dynamiquement")
    fi

    # DEBUG en prod
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        if grep -q "^DEBUG=false" "${PROJECT_ROOT}/.env" 2>/dev/null; then
            security_checks+=("${GREEN}✓${NC} DEBUG désactivé")
        else
            security_checks+=("${RED}✗${NC} DEBUG devrait être désactivé!")
        fi
    fi

    # UUID strict
    if grep -q "^DB_STRICT_UUID=true" "${PROJECT_ROOT}/.env" 2>/dev/null; then
        security_checks+=("${GREEN}✓${NC} UUID strict activé")
    fi

    # CORS
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        if grep "^CORS_ORIGINS=" "${PROJECT_ROOT}/.env" 2>/dev/null | grep -qi "localhost"; then
            security_checks+=("${RED}✗${NC} localhost dans CORS (non sécurisé)")
        else
            security_checks+=("${GREEN}✓${NC} CORS configuré (pas de localhost)")
        fi
    fi

    # Pare-feu
    if [[ "${OS_TYPE}" == "linux" ]]; then
        if command -v ufw &> /dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
            security_checks+=("${GREEN}✓${NC} Pare-feu UFW actif")
        elif command -v firewall-cmd &> /dev/null && sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
            security_checks+=("${GREEN}✓${NC} Pare-feu firewalld actif")
        else
            security_checks+=("${YELLOW}!${NC} Pare-feu à vérifier")
        fi
    fi

    # Afficher les vérifications
    for check in "${security_checks[@]}"; do
        echo -e "  ${check}"
    done
    echo ""

    # Avertissements de sécurité
    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        echo -e "${YELLOW}Rappels de sécurité production:${NC}"
        echo "  • Configurez un reverse proxy (Nginx/Caddy) avec HTTPS"
        echo "  • Activez les certificats SSL (Let's Encrypt)"
        echo "  • Configurez des sauvegardes automatiques"
        echo "  • Surveillez les logs de sécurité"
        echo ""
    fi
}

#===============================================================================
# PROCHAINES ÉTAPES
#===============================================================================

print_next_steps() {
    echo -e "${BOLD}Prochaines étapes:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    case "${INSTALL_MODE}" in
        dev)
            echo ""
            echo "  1. Démarrer l'application:"
            echo -e "     ${CYAN}./start_dev.sh${NC}"
            echo ""
            echo "  2. Accéder à l'interface:"
            echo "     API:  http://localhost:8000"
            echo "     Docs: http://localhost:8000/docs"
            echo ""
            echo "  3. Créer le premier utilisateur admin:"
            echo "     Utilisez le BOOTSTRAP_SECRET du fichier .env"
            echo ""
            ;;

        prod)
            echo ""
            echo "  1. Configurer le reverse proxy (Nginx recommandé):"
            echo -e "     ${CYAN}sudo apt install nginx${NC}"
            echo -e "     ${CYAN}sudo nano /etc/nginx/sites-available/azalscore${NC}"
            echo ""
            echo "  2. Obtenir un certificat SSL:"
            echo -e "     ${CYAN}sudo certbot --nginx -d votre-domaine.com${NC}"
            echo ""
            echo "  3. Démarrer le service:"
            echo -e "     ${CYAN}sudo systemctl start azalscore${NC}"
            echo ""
            echo "  4. Vérifier le statut:"
            echo -e "     ${CYAN}sudo systemctl status azalscore${NC}"
            echo ""
            echo "  5. Configurer les sauvegardes automatiques"
            echo ""
            ;;

        cloud)
            echo ""
            echo "  1. Consultez les fichiers de configuration générés:"
            echo "     .env                    - Variables d'environnement"
            echo "     .env.cloud-instructions - Instructions détaillées"
            echo ""
            echo "  2. Déployez sur votre plateforme cloud:"
            echo "     Railway: railway up"
            echo "     Render:  Connectez votre dépôt GitHub"
            echo "     Fly.io:  fly deploy"
            echo ""
            echo "  3. Configurez les variables d'environnement"
            echo "     sur le dashboard de votre plateforme"
            echo ""
            ;;
    esac
}

#===============================================================================
# COMMANDES UTILES
#===============================================================================

print_useful_commands() {
    echo -e "${BOLD}Commandes utiles:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    echo "  # Activer l'environnement virtuel"
    echo -e "  ${CYAN}source venv/bin/activate${NC}"
    echo ""

    echo "  # Exécuter les migrations"
    echo -e "  ${CYAN}alembic upgrade head${NC}"
    echo ""

    echo "  # Créer une nouvelle migration"
    echo -e "  ${CYAN}alembic revision --autogenerate -m \"description\"${NC}"
    echo ""

    echo "  # Lancer les tests"
    echo -e "  ${CYAN}pytest${NC}"
    echo ""

    if [[ "${INSTALL_MODE}" == "prod" ]]; then
        echo "  # Gestion du service"
        echo -e "  ${CYAN}sudo systemctl start|stop|restart|status azalscore${NC}"
        echo ""

        echo "  # Voir les logs"
        echo -e "  ${CYAN}sudo journalctl -u azalscore -f${NC}"
        echo -e "  ${CYAN}tail -f /var/log/azalscore/access.log${NC}"
        echo ""

        echo "  # Sauvegarde de la base de données"
        echo -e "  ${CYAN}pg_dump -U azals_user azals > backup.sql${NC}"
        echo ""
    fi

    # Informations de contact / support
    echo -e "${BOLD}Documentation et support:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  GitHub:    https://github.com/MASITH-developpement/Azalscore"
    echo "  Logs:      ${PROJECT_ROOT}/install.log"
    echo ""
}

#===============================================================================
# CONFIGURATION NGINX (EXEMPLE)
#===============================================================================

print_nginx_config() {
    cat << 'EOF'

# Configuration Nginx pour AZALSCORE
# Fichier: /etc/nginx/sites-available/azalscore

server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (si frontend servi par Nginx)
    location /static/ {
        alias /opt/azalscore/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}

EOF
}

#===============================================================================
# SAUVEGARDE DU RÉSUMÉ
#===============================================================================

save_installation_summary() {
    local summary_file="${PROJECT_ROOT}/INSTALL_SUMMARY.txt"

    {
        echo "AZALSCORE - Installation Summary"
        echo "================================="
        echo ""
        echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Mode: ${INSTALL_MODE}"
        echo "OS: ${OS_TYPE} (${DISTRO})"
        echo "Architecture: ${ARCH}"
        echo ""
        echo "Paths:"
        echo "  Project: ${PROJECT_ROOT}"
        echo "  Venv: ${PROJECT_ROOT}/venv"
        echo "  Logs: ${PROJECT_ROOT}/logs"
        echo ""
        echo "Database:"
        echo "  Name: azals"
        echo "  User: azals_user"
        echo "  Host: localhost:5432"
        echo ""
        echo "Configuration Files:"
        echo "  .env - Environment variables"
        echo "  start_dev.sh - Development startup"
        [[ "${INSTALL_MODE}" == "prod" ]] && echo "  start_prod.sh - Production startup"
        echo ""
    } > "${summary_file}"

    chmod 600 "${summary_file}"
    log INFO "Résumé sauvegardé: ${summary_file}"
}
