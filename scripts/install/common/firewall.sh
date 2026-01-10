#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Module: Configuration du pare-feu
#===============================================================================
# Ce module configure le pare-feu pour sécuriser le serveur
#===============================================================================

#===============================================================================
# CONFIGURATION PARE-FEU
#===============================================================================

setup_firewall() {
    log INFO "Configuration du pare-feu..."

    if [[ "${OS_TYPE}" != "linux" ]]; then
        log INFO "Configuration du pare-feu ignorée sur ${OS_TYPE}"
        print_macos_firewall_instructions
        return
    fi

    # Détecter le pare-feu disponible
    if command -v ufw &> /dev/null; then
        setup_ufw
    elif command -v firewall-cmd &> /dev/null; then
        setup_firewalld
    elif command -v iptables &> /dev/null; then
        setup_iptables
    else
        log WARN "Aucun pare-feu détecté"
        log INFO "Il est fortement recommandé d'installer et configurer un pare-feu"
    fi
}

#===============================================================================
# UFW (Ubuntu/Debian)
#===============================================================================

setup_ufw() {
    log INFO "Configuration de UFW..."

    # Installer UFW si nécessaire
    if ! command -v ufw &> /dev/null; then
        sudo apt-get install -y -qq ufw
    fi

    # Réinitialiser UFW (avec confirmation en mode interactif)
    if [[ "${INTERACTIVE}" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}Configuration du pare-feu UFW${NC}"
        echo "Les règles suivantes seront appliquées:"
        echo "  • SSH (22): autorisé"
        echo "  • HTTP (80): autorisé"
        echo "  • HTTPS (443): autorisé"
        echo "  • PostgreSQL (5432): localhost uniquement"
        echo "  • API interne (8000): localhost uniquement"
        echo ""
        read -rp "Appliquer cette configuration? [Y/n] " response
        if [[ "${response,,}" =~ ^(n|no)$ ]]; then
            log INFO "Configuration du pare-feu ignorée"
            return
        fi
    fi

    # Politique par défaut
    sudo ufw default deny incoming
    sudo ufw default allow outgoing

    # Règles SSH (CRITIQUE - ne jamais oublier!)
    sudo ufw allow ssh comment 'SSH access'

    # HTTP/HTTPS pour le reverse proxy
    sudo ufw allow 80/tcp comment 'HTTP'
    sudo ufw allow 443/tcp comment 'HTTPS'

    # PostgreSQL - localhost uniquement
    # Note: Par défaut, PostgreSQL n'écoute que sur localhost
    # Cette règle bloque explicitement les connexions externes
    sudo ufw deny 5432/tcp comment 'Block external PostgreSQL'

    # API AZALSCORE - localhost uniquement (derrière reverse proxy)
    # Le port 8000 ne doit pas être accessible directement depuis l'extérieur
    sudo ufw deny 8000/tcp comment 'Block external API access'

    # Redis - localhost uniquement (si utilisé)
    sudo ufw deny 6379/tcp comment 'Block external Redis'

    # Limiter les tentatives SSH (protection brute force)
    sudo ufw limit ssh/tcp comment 'SSH rate limit'

    # Activer UFW
    echo "y" | sudo ufw enable

    # Afficher le statut
    log OK "UFW configuré"
    echo ""
    sudo ufw status verbose
    echo ""
}

#===============================================================================
# FIREWALLD (Fedora/RHEL/CentOS)
#===============================================================================

setup_firewalld() {
    log INFO "Configuration de firewalld..."

    # S'assurer que firewalld est démarré
    sudo systemctl enable firewalld
    sudo systemctl start firewalld

    # Zone par défaut
    sudo firewall-cmd --set-default-zone=public

    # SSH
    sudo firewall-cmd --permanent --zone=public --add-service=ssh

    # HTTP/HTTPS
    sudo firewall-cmd --permanent --zone=public --add-service=http
    sudo firewall-cmd --permanent --zone=public --add-service=https

    # Bloquer PostgreSQL depuis l'extérieur
    sudo firewall-cmd --permanent --zone=public --remove-service=postgresql 2>/dev/null || true

    # Bloquer le port API depuis l'extérieur
    sudo firewall-cmd --permanent --zone=public --remove-port=8000/tcp 2>/dev/null || true

    # Appliquer les changements
    sudo firewall-cmd --reload

    log OK "firewalld configuré"
    echo ""
    sudo firewall-cmd --list-all
    echo ""
}

#===============================================================================
# IPTABLES (Fallback)
#===============================================================================

setup_iptables() {
    log INFO "Configuration d'iptables..."

    # Sauvegarder les règles actuelles
    sudo iptables-save > /tmp/iptables.backup.$(date +%Y%m%d_%H%M%S)

    # Politique par défaut
    sudo iptables -P INPUT DROP
    sudo iptables -P FORWARD DROP
    sudo iptables -P OUTPUT ACCEPT

    # Autoriser le loopback
    sudo iptables -A INPUT -i lo -j ACCEPT
    sudo iptables -A OUTPUT -o lo -j ACCEPT

    # Autoriser les connexions établies
    sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

    # SSH
    sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

    # HTTP/HTTPS
    sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

    # PostgreSQL - localhost uniquement
    sudo iptables -A INPUT -p tcp --dport 5432 -s 127.0.0.1 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 5432 -j DROP

    # API - localhost uniquement
    sudo iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 8000 -j DROP

    # Protection contre le scan de ports
    sudo iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
    sudo iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

    # Limiter les nouvelles connexions SSH
    sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
    sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 -j DROP

    # Sauvegarder les règles
    if command -v netfilter-persistent &> /dev/null; then
        sudo netfilter-persistent save
    elif [[ -f /etc/redhat-release ]]; then
        sudo service iptables save
    fi

    log OK "iptables configuré"
}

#===============================================================================
# INSTRUCTIONS MACOS
#===============================================================================

print_macos_firewall_instructions() {
    echo ""
    echo -e "${BOLD}Configuration du pare-feu macOS:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Ouvrez Préférences Système > Sécurité et confidentialité > Coupe-feu"
    echo "2. Cliquez sur le cadenas pour déverrouiller"
    echo "3. Cliquez sur 'Activer le coupe-feu'"
    echo "4. Cliquez sur 'Options du coupe-feu'"
    echo "5. Cochez 'Bloquer toutes les connexions entrantes' (pour la production)"
    echo ""
    echo "Ou via le terminal:"
    echo "  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on"
    echo ""
}

#===============================================================================
# FAIL2BAN
#===============================================================================

setup_fail2ban() {
    log INFO "Configuration de Fail2ban..."

    # Installer Fail2ban
    case "${DISTRO}" in
        debian|ubuntu|linuxmint|pop)
            sudo apt-get install -y -qq fail2ban
            ;;
        fedora|centos|rhel|rocky|almalinux)
            sudo dnf install -y -q fail2ban
            ;;
        arch|manjaro)
            sudo pacman -Sy --noconfirm fail2ban
            ;;
        *)
            log WARN "Installation automatique de Fail2ban non supportée"
            return
            ;;
    esac

    # Configuration personnalisée
    local jail_local="/etc/fail2ban/jail.local"

    sudo tee "${jail_local}" > /dev/null << 'EOF'
# AZALSCORE - Configuration Fail2ban
# Généré automatiquement

[DEFAULT]
# Ban pendant 1 heure
bantime = 3600

# Fenêtre de détection: 10 minutes
findtime = 600

# Nombre maximum de tentatives
maxretry = 5

# Action par défaut
banaction = iptables-multiport
banaction_allports = iptables-allports

# Email de notification (optionnel)
# destemail = admin@example.com
# sender = fail2ban@example.com
# action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[sshd-ddos]
enabled = true
port = ssh
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 6

# Protection Nginx (si utilisé)
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2

# Protection API AZALSCORE
[azalscore-api]
enabled = true
port = http,https
filter = azalscore-api
logpath = /var/log/azalscore/access.log
maxretry = 10
findtime = 60
bantime = 600

# Scan de ports
[portscan]
enabled = true
filter = portscan
action = iptables-allports[name=portscan]
logpath = /var/log/syslog
maxretry = 2
EOF

    # Créer le filtre personnalisé pour AZALSCORE
    local azalscore_filter="/etc/fail2ban/filter.d/azalscore-api.conf"

    sudo tee "${azalscore_filter}" > /dev/null << 'EOF'
# Fail2ban filter for AZALSCORE API
[Definition]
failregex = ^<HOST> .* "(GET|POST|PUT|DELETE) /api/v1/auth/login.* HTTP/.*" (401|403)
            ^<HOST> .* "(GET|POST|PUT|DELETE) /api/v1/auth/.*" (401|403)
            ^<HOST> .* "(GET|POST|PUT|DELETE) /api/.*" 429

ignoreregex =
EOF

    # Démarrer Fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban

    log OK "Fail2ban configuré"

    # Afficher le statut
    echo ""
    sudo fail2ban-client status
    echo ""
}

#===============================================================================
# VÉRIFICATION
#===============================================================================

verify_firewall_rules() {
    log INFO "Vérification des règles de pare-feu..."

    echo ""
    echo -e "${BOLD}État du pare-feu:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if command -v ufw &> /dev/null; then
        sudo ufw status numbered
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --list-all
    elif command -v iptables &> /dev/null; then
        sudo iptables -L -n --line-numbers | head -30
    fi

    echo ""

    # Vérifier que les ports critiques sont protégés
    log INFO "Vérification des ports critiques..."

    local exposed_ports=()

    # Tester si les ports sont accessibles depuis l'extérieur
    # (Note: ce test est limité - en production, utilisez un scanner externe)

    if ss -tuln 2>/dev/null | grep -q ":5432 "; then
        if ss -tuln 2>/dev/null | grep ":5432 " | grep -q "0.0.0.0"; then
            exposed_ports+=("5432 (PostgreSQL)")
        fi
    fi

    if ss -tuln 2>/dev/null | grep -q ":8000 "; then
        if ss -tuln 2>/dev/null | grep ":8000 " | grep -q "0.0.0.0"; then
            log WARN "Port 8000 (API) écoute sur toutes les interfaces"
            log INFO "Assurez-vous qu'il est protégé par le pare-feu"
        fi
    fi

    if [[ ${#exposed_ports[@]} -gt 0 ]]; then
        log WARN "Ports potentiellement exposés: ${exposed_ports[*]}"
    else
        log OK "Configuration des ports semble correcte"
    fi
}

#===============================================================================
# COMMANDES UTILES
#===============================================================================

print_firewall_commands() {
    echo ""
    echo -e "${BOLD}Commandes utiles pour le pare-feu:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if command -v ufw &> /dev/null; then
        echo "UFW:"
        echo "  Statut:           sudo ufw status verbose"
        echo "  Activer:          sudo ufw enable"
        echo "  Désactiver:       sudo ufw disable"
        echo "  Ajouter règle:    sudo ufw allow 443/tcp"
        echo "  Supprimer règle:  sudo ufw delete allow 443/tcp"
        echo "  Logs:             sudo tail -f /var/log/ufw.log"
    fi

    if command -v fail2ban-client &> /dev/null; then
        echo ""
        echo "Fail2ban:"
        echo "  Statut:           sudo fail2ban-client status"
        echo "  Statut jail:      sudo fail2ban-client status sshd"
        echo "  Débannir IP:      sudo fail2ban-client set sshd unbanip <IP>"
        echo "  Logs:             sudo tail -f /var/log/fail2ban.log"
    fi

    echo ""
}
