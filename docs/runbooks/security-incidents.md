# Runbook: Incidents Sécurité

## IMPORTANT: Protocole de réponse sécurité

**Tout incident sécurité doit être:**
1. Traité en confidentialité
2. Documenté dans un canal sécurisé
3. Escaladé au RSSI si données compromises
4. Notifié aux autorités si breach RGPD (< 72h)

---

## Alerte: SuspiciousTenantAccess

**Sévérité:** SEV1 (CRITIQUE)
**Trigger:** Tentative d'accès cross-tenant détectée

### Actions immédiates (< 15 min)

```bash
# 1. Identifier la source
grep "Tenant ID mismatch" /var/log/azalscore/app.log | tail -50

# 2. Extraire les IPs suspectes
grep "403.*mismatch" /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c

# 3. Bloquer immédiatement les IPs
for ip in <IPS_SUSPECTES>; do
    sudo iptables -A INPUT -s $ip -j DROP
done
```

### Investigation

```bash
# Vérifier les requêtes de l'IP suspecte
grep "<IP_SUSPECTE>" /var/log/nginx/access.log | head -100

# Vérifier si des données ont été accédées
sudo -u postgres psql -d azalscore -c "
SELECT * FROM core_audit_journal
WHERE created_at > now() - interval '1 hour'
ORDER BY created_at DESC LIMIT 100;"
```

### Containment

```bash
# Révoquer tous les tokens de l'utilisateur suspect
redis-cli keys "azals:token:*" | xargs redis-cli del

# Forcer re-login de tous les utilisateurs du tenant affecté
# (Si nécessaire)
```

---

## Alerte: SQLInjectionAttempt

**Sévérité:** SEV2
**Trigger:** Pattern SQL injection détecté dans les logs

### Diagnostic

```bash
# Identifier les requêtes suspectes
grep -iE "union|select.*from|drop|delete|insert|update.*set" /var/log/nginx/access.log | tail -50

# Vérifier les erreurs SQL
grep -i "sqlalchemy\|psycopg2" /var/log/azalscore/app.log | grep -i error | tail -50
```

### Résolution

```bash
# 1. Bloquer l'IP source
sudo iptables -A INPUT -s <IP_ATTAQUANT> -j DROP

# 2. Vérifier l'intégrité des données
sudo -u postgres psql -d azalscore -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
ORDER BY n_tup_del DESC LIMIT 20;"

# 3. Si données modifiées, restaurer depuis backup
# Voir runbook backup-restore.md
```

### Analyse post-incident

1. Identifier le endpoint vulnérable
2. Vérifier que toutes les requêtes utilisent des paramètres liés
3. Ajouter validation d'entrée si manquante
4. Déployer le fix

---

## Alerte: DataExfiltrationSuspected

**Sévérité:** SEV1 (CRITIQUE)
**Trigger:** Volume anormal de données accédées

### Actions immédiates

```bash
# 1. Identifier l'utilisateur/IP
grep -E "GET.*(export|download|bulk)" /var/log/nginx/access.log | \
    awk '{print $1, $4, $7}' | tail -100

# 2. Couper l'accès immédiatement
# Révoquer le token de l'utilisateur suspect
# ou bloquer l'IP

# 3. Capturer l'état actuel
pg_dump azalscore > /tmp/forensics_$(date +%Y%m%d_%H%M%S).sql
cp /var/log/azalscore/app.log /tmp/forensics_app.log
cp /var/log/nginx/access.log /tmp/forensics_nginx.log
```

### Investigation

```bash
# Analyser les patterns d'accès
sudo -u postgres psql -d azalscore -c "
SELECT user_id, action, count(*), min(created_at), max(created_at)
FROM core_audit_journal
WHERE created_at > now() - interval '24 hours'
GROUP BY user_id, action
ORDER BY count DESC LIMIT 50;"

# Identifier les données potentiellement exfiltrées
# Basé sur les endpoints accédés
```

### Notification RGPD

Si données personnelles potentiellement compromises:

1. **Documentation immédiate:**
   - Nature de la violation
   - Catégories de données concernées
   - Nombre de personnes affectées
   - Conséquences probables
   - Mesures prises

2. **Notification CNIL (< 72h):**
   - Via https://notifications.cnil.fr/
   - Référence: Article 33 RGPD

3. **Notification utilisateurs (si risque élevé):**
   - Email personnalisé
   - Description claire et simple
   - Recommandations (changement mdp, etc.)

---

## Alerte: BruteForceAttack

**Sévérité:** SEV2
**Trigger:** > 100 échecs auth/minute depuis même source

### Diagnostic

```bash
# Identifier les sources
grep "401\|Incorrect" /var/log/azalscore/app.log | \
    awk -F'IP:' '{print $2}' | cut -d' ' -f1 | sort | uniq -c | sort -rn | head -20
```

### Réponse automatique

Le rate limiter devrait bloquer automatiquement. Vérifier:

```bash
# Vérifier les blocages actifs
redis-cli keys "azals:ratelimit:login:*" | while read key; do
    echo "$key: $(redis-cli get $key)"
done
```

### Réponse manuelle si nécessaire

```bash
# Bloquer au niveau firewall
sudo iptables -A INPUT -s <IP_ATTAQUANT> -j DROP

# Ajouter à la blocklist permanente
echo "<IP_ATTAQUANT>" >> /etc/nginx/conf.d/blocklist.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

## Alerte: PrivilegeEscalationAttempt

**Sévérité:** SEV1 (CRITIQUE)
**Trigger:** Utilisateur tente d'accéder à des ressources hors de son rôle

### Diagnostic

```bash
# Identifier les tentatives
grep "403.*role\|permission\|unauthorized" /var/log/azalscore/app.log | tail -50

# Vérifier les rôles de l'utilisateur
sudo -u postgres psql -d azalscore -c "
SELECT id, email, role, tenant_id FROM users WHERE email = '<EMAIL_SUSPECT>';"
```

### Résolution

```bash
# Désactiver le compte suspect
sudo -u postgres psql -d azalscore -c "
UPDATE users SET is_active = 0 WHERE email = '<EMAIL_SUSPECT>';"

# Révoquer ses tokens
redis-cli keys "azals:token:<USER_ID>*" | xargs redis-cli del

# Audit des actions passées
sudo -u postgres psql -d azalscore -c "
SELECT * FROM core_audit_journal
WHERE user_id = '<USER_ID>'
ORDER BY created_at DESC LIMIT 100;"
```

---

## Checklist incident sécurité

### Pendant l'incident
- [ ] Contenir la menace (bloquer accès)
- [ ] Préserver les preuves (logs, dumps)
- [ ] Documenter chaque action avec timestamp
- [ ] Notifier le RSSI
- [ ] Évaluer l'impact (données, utilisateurs)

### Après l'incident
- [ ] Root cause analysis
- [ ] Notification CNIL si breach (< 72h)
- [ ] Notification utilisateurs si nécessaire
- [ ] Corriger la vulnérabilité
- [ ] Post-mortem documenté
- [ ] Mise à jour des règles de détection
- [ ] Formation équipe si erreur humaine

### Contacts d'urgence sécurité

| Rôle | Contact | Quand contacter |
|------|---------|-----------------|
| RSSI | rssi@azalscore.com | Tout SEV1 sécurité |
| DPO | dpo@azalscore.com | Breach données personnelles |
| Legal | legal@azalscore.com | Avant notification externe |
| CERT-FR | cert-fr.cossi@ssi.gouv.fr | Attaque majeure |
