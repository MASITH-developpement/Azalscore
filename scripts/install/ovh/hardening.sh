#!/usr/bin/env bash
#===============================================================================
# AZALSCORE - Hardening de sécurité pour serveur OVH
#===============================================================================
# Ce script applique les meilleures pratiques de sécurité sur un serveur
# Debian/Ubuntu fraîchement installé.
#
# Exécution: sudo ./hardening.sh
#
# Actions:
#   - Configuration SSH sécurisée
#   - Configuration du pare-feu UFW
#   - Installation et configuration de Fail2ban
#   - Désactivation des services inutiles
#   - Sécurisation du kernel
#   - Configuration des limites système
#===============================================================================

set -euo pipefail

#===============================================================================
# CONFIGURATION
#===============================================================================

# Port SSH personnalisé (optionnel - laisser vide pour garder 22)
SSH_PORT="${SSH_PORT:-22}"

# Adresses IP autorisées pour SSH (optionnel)
SSH_ALLOWED_IPS="${SSH_ALLOWED_IPS:-}"

# Activer le 2FA SSH
ENABLE_2FA="${ENABLE_2FA:-false}"

#===============================================================================
# FONCTIONS
#===============================================================================

log() {
    local level="$1"
    shift
    case "$level" in
        INFO)  echo -e "\033[0;34m[INFO]\033[0m $*" ;;
        OK)    echo -e "\033[0;32m[OK]\033[0m $*" ;;
        WARN)  echo -e "\033[1;33m[WARN]\033[0m $*" ;;
        ERROR) echo -e "\033[0;31m[ERROR]\033[0m $*" ;;
    esac
}

#===============================================================================
# FONCTION PRINCIPALE
#===============================================================================

run_hardening() {
    log INFO "Démarrage du hardening..."

    harden_ssh
    setup_firewall
    setup_fail2ban
    harden_kernel
    disable_unused_services
    set_file_permissions
    configure_audit
    final_checks

    log OK "Hardening terminé"
}

#===============================================================================
# SSH HARDENING
#===============================================================================

harden_ssh() {
    log INFO "Sécurisation de SSH..."

    # Backup de la configuration originale
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d)

    # Configuration SSH sécurisée
    cat > /etc/ssh/sshd_config.d/99-hardening.conf << EOF
# AZALSCORE SSH Hardening
# Généré le $(date '+%Y-%m-%d %H:%M:%S')

# Port SSH
Port ${SSH_PORT}

# Désactiver l'authentification root
PermitRootLogin prohibit-password

# Désactiver l'authentification par mot de passe (clé SSH requise)
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Authentification par clé uniquement
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Désactiver les fonctionnalités non utilisées
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no

# Limites de connexion
MaxAuthTries 3
MaxSessions 5
LoginGraceTime 60

# Vérification stricte des répertoires
StrictModes yes

# Désactiver les protocoles obsolètes
Protocol 2

# Algorithmes sécurisés uniquement
KexAlgorithms curve25519-sha256@libssh.org,curve25519-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Timeout
ClientAliveInterval 300
ClientAliveCountMax 2

# Bannière
Banner /etc/ssh/banner

# Logs
LogLevel VERBOSE
EOF

    # Créer la bannière SSH
    cat > /etc/ssh/banner << 'EOF'
*******************************************************************
*                      AUTHORIZED ACCESS ONLY                      *
*                                                                   *
*  This system is for authorized users only. All activity may be   *
*  monitored and reported. Unauthorized access is prohibited.      *
*                                                                   *
*******************************************************************
EOF

    # Générer les clés hôte Ed25519 si absentes
    if [[ ! -f /etc/ssh/ssh_host_ed25519_key ]]; then
        ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""
    fi

    # Tester la configuration
    if sshd -t; then
        systemctl restart sshd
        log OK "SSH sécurisé (port ${SSH_PORT})"
    else
        log ERROR "Erreur de configuration SSH - restauration du backup"
        cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
        rm /etc/ssh/sshd_config.d/99-hardening.conf
        exit 1
    fi
}

#===============================================================================
# FIREWALL UFW
#===============================================================================

setup_firewall() {
    log INFO "Configuration du pare-feu UFW..."

    # Installer UFW si nécessaire
    apt-get install -y -qq ufw

    # Réinitialiser UFW
    ufw --force reset

    # Politique par défaut
    ufw default deny incoming
    ufw default allow outgoing

    # SSH
    ufw allow "${SSH_PORT}/tcp" comment 'SSH'

    # HTTP/HTTPS
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'

    # Limiter les connexions SSH (protection brute force)
    ufw limit "${SSH_PORT}/tcp" comment 'SSH rate limit'

    # Bloquer les ports sensibles
    ufw deny 5432/tcp comment 'Block external PostgreSQL'
    ufw deny 6379/tcp comment 'Block external Redis'
    ufw deny 8000/tcp comment 'Block direct API access'

    # Activer UFW
    echo "y" | ufw enable

    log OK "UFW configuré"
    ufw status verbose
}

#===============================================================================
# FAIL2BAN
#===============================================================================

setup_fail2ban() {
    log INFO "Configuration de Fail2ban..."

    apt-get install -y -qq fail2ban

    # Configuration principale
    cat > /etc/fail2ban/jail.local << 'EOF'
# AZALSCORE Fail2ban Configuration

[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
banaction = iptables-multiport
ignoreip = 127.0.0.1/8 ::1

# Email (optionnel)
# destemail = admin@example.com
# sender = fail2ban@example.com
# action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400

[sshd-ddos]
enabled = true
port = ssh
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 6

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 60

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

    # Filtre personnalisé pour AZALSCORE
    cat > /etc/fail2ban/filter.d/azalscore.conf << 'EOF'
[Definition]
failregex = ^<HOST> .* "(GET|POST|PUT|DELETE) /api/v1/auth/login.* HTTP/.*" (401|403)
            ^<HOST> .* "(GET|POST|PUT|DELETE) /api/.*" 429
ignoreregex =
EOF

    systemctl enable fail2ban
    systemctl restart fail2ban

    log OK "Fail2ban configuré"
}

#===============================================================================
# KERNEL HARDENING
#===============================================================================

harden_kernel() {
    log INFO "Sécurisation du kernel..."

    cat > /etc/sysctl.d/99-security.conf << 'EOF'
# AZALSCORE Kernel Security Hardening

# Désactiver le routage IP
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Protection contre les attaques SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# Ignorer les redirections ICMP
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Ignorer les requêtes source route
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Protection contre le spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignorer les broadcast ICMP
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Logs des paquets martiens
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Ignorer les bogus ICMP
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Protection ASLR
kernel.randomize_va_space = 2

# Restreindre l'accès à dmesg
kernel.dmesg_restrict = 1

# Restreindre l'accès aux pointeurs kernel
kernel.kptr_restrict = 2

# Désactiver le Magic SysRq
kernel.sysrq = 0

# Restreindre ptrace
kernel.yama.ptrace_scope = 1

# Augmenter l'entropie du générateur aléatoire
kernel.random.read_wakeup_threshold = 256
kernel.random.write_wakeup_threshold = 256

# Protection contre les core dumps
fs.suid_dumpable = 0

# Limiter les liens symboliques
fs.protected_symlinks = 1
fs.protected_hardlinks = 1

# Limiter l'accès aux fichiers FIFO
fs.protected_fifos = 2
fs.protected_regular = 2
EOF

    sysctl -p /etc/sysctl.d/99-security.conf

    log OK "Kernel sécurisé"
}

#===============================================================================
# SERVICES INUTILISÉS
#===============================================================================

disable_unused_services() {
    log INFO "Désactivation des services inutilisés..."

    local services=(
        "avahi-daemon"
        "cups"
        "cups-browsed"
        "bluetooth"
        "ModemManager"
    )

    for service in "${services[@]}"; do
        if systemctl is-enabled "${service}" 2>/dev/null; then
            systemctl stop "${service}" 2>/dev/null || true
            systemctl disable "${service}" 2>/dev/null || true
            log INFO "Service ${service} désactivé"
        fi
    done

    log OK "Services inutilisés désactivés"
}

#===============================================================================
# PERMISSIONS
#===============================================================================

set_file_permissions() {
    log INFO "Configuration des permissions..."

    # Permissions strictes sur les fichiers sensibles
    chmod 600 /etc/shadow
    chmod 600 /etc/gshadow
    chmod 644 /etc/passwd
    chmod 644 /etc/group

    # SSH
    chmod 700 /etc/ssh
    chmod 600 /etc/ssh/sshd_config
    chmod 600 /etc/ssh/ssh_host_*_key

    # Cron
    chmod 600 /etc/crontab
    chmod 700 /etc/cron.d
    chmod 700 /etc/cron.daily
    chmod 700 /etc/cron.hourly
    chmod 700 /etc/cron.weekly
    chmod 700 /etc/cron.monthly

    # Désactiver le compte invité
    if [[ -f /etc/lightdm/lightdm.conf ]]; then
        echo "allow-guest=false" >> /etc/lightdm/lightdm.conf
    fi

    log OK "Permissions configurées"
}

#===============================================================================
# AUDIT
#===============================================================================

configure_audit() {
    log INFO "Configuration de l'audit..."

    # Installer auditd
    apt-get install -y -qq auditd audispd-plugins

    # Configuration des règles d'audit
    cat > /etc/audit/rules.d/azalscore.rules << 'EOF'
# AZALSCORE Audit Rules

# Supprimer les règles existantes
-D

# Buffer size
-b 8192

# Échec de la configuration = panique
-f 1

# Surveiller les modifications de configuration
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Surveiller SSH
-w /etc/ssh/sshd_config -p wa -k sshd

# Surveiller les authentifications
-w /var/log/auth.log -p wa -k auth_log
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins

# Surveiller le démarrage des services
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules

# Surveiller les montages
-a always,exit -F arch=b64 -S mount -k mounts
-a always,exit -F arch=b32 -S mount -k mounts

# Surveiller les suppressions de fichiers
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete
-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete

# Surveiller les modifications de temps
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Verrouiller les règles
-e 2
EOF

    systemctl enable auditd
    systemctl restart auditd

    log OK "Audit configuré"
}

#===============================================================================
# VÉRIFICATIONS FINALES
#===============================================================================

final_checks() {
    log INFO "Vérifications finales..."

    # Vérifier UFW
    if ufw status | grep -q "Status: active"; then
        log OK "UFW actif"
    else
        log WARN "UFW n'est pas actif"
    fi

    # Vérifier Fail2ban
    if systemctl is-active --quiet fail2ban; then
        log OK "Fail2ban actif"
    else
        log WARN "Fail2ban n'est pas actif"
    fi

    # Vérifier SSH
    if sshd -t 2>/dev/null; then
        log OK "Configuration SSH valide"
    else
        log WARN "Problème de configuration SSH"
    fi

    # Vérifier auditd
    if systemctl is-active --quiet auditd; then
        log OK "Auditd actif"
    else
        log WARN "Auditd n'est pas actif"
    fi

    echo ""
    log OK "Hardening terminé!"
    echo ""
    echo "Actions recommandées:"
    echo "  1. Ajoutez votre clé SSH publique dans ~/.ssh/authorized_keys"
    echo "  2. Testez la connexion SSH avant de fermer cette session"
    echo "  3. Redémarrez le serveur pour appliquer tous les changements kernel"
    echo ""
}

#===============================================================================
# EXÉCUTION (si appelé directement)
#===============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $EUID -ne 0 ]]; then
        echo "Ce script doit être exécuté en tant que root"
        exit 1
    fi

    run_hardening
fi
