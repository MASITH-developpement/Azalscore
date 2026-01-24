# Runbook: Incidents Authentification

## Alerte: HighAuthFailureRate

**Sévérité:** SEV2
**Seuil:** > 50 échecs/minute ou > 10% des tentatives

### Symptômes
- Alerte Prometheus `HighAuthFailureRate`
- Spike des erreurs 401/403
- Plaintes utilisateurs "impossible de se connecter"

### Diagnostic

```bash
# 1. Vérifier les logs d'authentification
grep -i "auth" /var/log/azalscore/app.log | tail -100

# 2. Analyser les patterns d'échec
grep "401\|403" /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# 3. Vérifier le rate limiter
redis-cli keys "azals:ratelimit:login:*" | head -20
```

### Résolution

#### Cas 1: Attaque brute force (même IP)
```bash
# Bloquer l'IP au niveau firewall
sudo iptables -A INPUT -s <IP_MALVEILLANTE> -j DROP

# Ou via nginx
echo "deny <IP_MALVEILLANTE>;" >> /etc/nginx/conf.d/blocklist.conf
sudo nginx -t && sudo systemctl reload nginx
```

#### Cas 2: Credential stuffing (IPs multiples)
```bash
# Activer le mode défensif (rate limit strict)
# Modifier dans .env:
AUTH_RATE_LIMIT_PER_MINUTE=3

# Redémarrer l'application
sudo systemctl restart azalscore
```

#### Cas 3: Problème JWT (tokens invalides)
```bash
# Vérifier la configuration JWT
grep -i "secret\|jwt" /etc/azalscore/.env

# Vérifier que le secret n'a pas changé
# Si changé, tous les tokens existants sont invalides

# Forcer la déconnexion de tous les utilisateurs
redis-cli FLUSHDB  # Attention: vide le cache Redis
```

### Escalade

Si attaque coordonnée détectée:
1. Contacter l'équipe sécurité immédiatement
2. Activer le mode maintenance si nécessaire
3. Analyser les logs pour identifier la source
4. Signaler à l'hébergeur si DDoS

---

## Alerte: AccountLockouts

**Sévérité:** SEV3
**Seuil:** > 10 comptes verrouillés/heure

### Diagnostic

```bash
# Vérifier les comptes récemment verrouillés dans Redis
redis-cli keys "azals:ratelimit:login:*:failures" | while read key; do
    count=$(redis-cli get "$key")
    if [ "$count" -ge 5 ]; then
        echo "$key: $count failures"
    fi
done
```

### Résolution

```bash
# Déverrouiller un compte spécifique
redis-cli del "azals:ratelimit:login:user@example.com:failures"

# Déverrouiller tous les comptes (attention!)
redis-cli keys "azals:ratelimit:login:*:failures" | xargs redis-cli del
```

---

## Alerte: JWTSecretCompromised

**Sévérité:** SEV1 (CRITIQUE)
**Trigger:** Détection de token forgé ou secret exposé

### Actions immédiates

1. **Rotation du secret JWT**
```bash
# Générer nouveau secret
NEW_SECRET=$(openssl rand -hex 32)

# Mettre à jour .env
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" /etc/azalscore/.env

# Redémarrer l'application
sudo systemctl restart azalscore
```

2. **Invalider tous les tokens existants**
```bash
# Vider la blacklist et forcer re-login
redis-cli FLUSHDB
```

3. **Notifier les utilisateurs**
- Envoyer email de notification
- Forcer changement de mot de passe si nécessaire

4. **Audit**
- Analyser les logs pour identifier les accès non autorisés
- Vérifier les actions effectuées avec tokens compromis
- Documenter pour compliance (RGPD breach notification si données exposées)

---

## Alerte: 2FAServiceDown

**Sévérité:** SEV2
**Symptômes:** Utilisateurs ne peuvent pas valider 2FA

### Diagnostic

```bash
# Vérifier le service TOTP
grep "2fa\|totp" /var/log/azalscore/app.log | tail -50

# Vérifier la synchronisation horaire (critique pour TOTP)
timedatectl status
ntpq -p
```

### Résolution

#### Cas 1: Désynchronisation horaire
```bash
# Forcer la synchronisation NTP
sudo systemctl restart systemd-timesyncd
# ou
sudo ntpdate -s time.google.com
```

#### Cas 2: Base de données TOTP corrompue
```bash
# Vérifier les secrets TOTP dans la DB
sudo -u postgres psql -d azalscore -c "
SELECT id, email, totp_enabled, totp_secret IS NOT NULL as has_secret
FROM users WHERE totp_enabled = 1 LIMIT 10;"
```

### Workaround temporaire

Permettre login sans 2FA pour les cas critiques:
```bash
# Désactiver temporairement 2FA pour un utilisateur
sudo -u postgres psql -d azalscore -c "
UPDATE users SET totp_enabled = 0 WHERE email = 'user@example.com';"

# IMPORTANT: Réactiver après résolution
```

---

## Checklist post-incident auth

- [ ] Identifier la root cause
- [ ] Vérifier qu'aucun compte n'est toujours compromis
- [ ] Rotation des secrets si nécessaire
- [ ] Notification utilisateurs si breach
- [ ] Mise à jour des règles de détection
- [ ] Post-mortem si SEV1/SEV2
