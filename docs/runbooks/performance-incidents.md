# Runbook: Incidents Performance

## Alerte: HighAPILatency

**Sévérité:** SEV2
**Seuil:** P95 > 2 secondes pendant 5 minutes

### Symptômes
- Alerte Prometheus `HighAPILatency`
- Timeout côté client
- Dashboard Grafana montre latence élevée

### Diagnostic

```bash
# 1. Identifier les endpoints lents
grep "HTTP" /var/log/nginx/access.log | awk '{print $7, $NF}' | sort | uniq -c | sort -rn | head -20

# 2. Vérifier la charge CPU/Memory
top -bn1 | head -20
free -h

# 3. Vérifier les connexions DB
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# 4. Vérifier Redis
redis-cli info stats | grep -E "instantaneous_ops|connected_clients"
```

### Résolution

#### Cas 1: Charge CPU élevée
```bash
# Identifier les processus consommateurs
ps aux --sort=-%cpu | head -10

# Si c'est l'application, scaler horizontalement
# ou redémarrer le worker problématique
sudo systemctl restart azalscore@worker1
```

#### Cas 2: Requêtes DB lentes
```bash
# Voir requêtes actives
sudo -u postgres psql -c "
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' ORDER BY duration DESC LIMIT 5;"

# Terminer une requête bloquante
sudo -u postgres psql -c "SELECT pg_terminate_backend(<PID>);"
```

#### Cas 3: Cache Redis inefficace
```bash
# Vérifier le hit ratio
redis-cli info stats | grep keyspace

# Si miss ratio élevé, vérifier les TTL
redis-cli keys "*" | head -20 | xargs -I {} redis-cli ttl {}

# Flush cache si données corrompues
redis-cli FLUSHDB
```

---

## Alerte: HighMemoryUsage

**Sévérité:** SEV2
**Seuil:** > 85% RAM utilisée

### Diagnostic

```bash
# Vue d'ensemble mémoire
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Cached|Buffers"

# Top consommateurs
ps aux --sort=-%mem | head -10

# Vérifier les leaks potentiels
watch -n 5 "ps aux --sort=-%mem | head -5"
```

### Résolution

```bash
# 1. Libérer le cache système (sans impact)
sync; echo 3 > /proc/sys/vm/drop_caches

# 2. Redémarrer les workers si memory leak
sudo systemctl restart azalscore

# 3. Si persistant, augmenter la RAM (scale vertical)
# Ou ajouter des instances (scale horizontal)
```

---

## Alerte: HighErrorRate

**Sévérité:** SEV2
**Seuil:** > 5% des requêtes en erreur

### Diagnostic

```bash
# Analyser les erreurs par type
grep -E "500|502|503" /var/log/nginx/access.log | awk '{print $7}' | sort | uniq -c | sort -rn

# Erreurs applicatives
grep "ERROR\|Exception" /var/log/azalscore/app.log | tail -100
```

### Résolution par code d'erreur

#### 500 Internal Server Error
```bash
# Vérifier les exceptions
grep "Traceback\|Exception" /var/log/azalscore/app.log | tail -50

# Identifier le module en erreur
grep "ERROR" /var/log/azalscore/app.log | awk -F'[][]' '{print $2}' | sort | uniq -c
```

#### 502 Bad Gateway
```bash
# Vérifier que l'application répond
curl -I http://localhost:8000/health

# Redémarrer si nécessaire
sudo systemctl restart azalscore
```

#### 503 Service Unavailable
```bash
# Vérifier le rate limiting
redis-cli keys "azals:ratelimit:platform:*" | xargs -I {} redis-cli get {}

# Si rate limit atteint, attendre ou augmenter les limites
```

---

## Alerte: DiskSpaceWarning

**Sévérité:** SEV3 (SEV1 si > 95%)
**Seuil:** > 80% espace disque utilisé

### Diagnostic

```bash
# Vue d'ensemble
df -h

# Identifier les gros fichiers
du -sh /* 2>/dev/null | sort -hr | head -10
du -sh /var/log/* | sort -hr | head -10
```

### Résolution

```bash
# 1. Rotation des logs
sudo logrotate -f /etc/logrotate.conf

# 2. Nettoyer les anciens logs
sudo find /var/log -name "*.gz" -mtime +30 -delete
sudo journalctl --vacuum-time=7d

# 3. Nettoyer les backups anciens
find /var/backups/azalscore -name "*.sql.gz" -mtime +30 -delete

# 4. Vacuum PostgreSQL
sudo -u postgres vacuumdb --all --analyze

# 5. Nettoyer Docker si utilisé
docker system prune -af
```

---

## Procédure de scaling d'urgence

### Scale horizontal (ajouter des instances)

```bash
# 1. Préparer une nouvelle instance
# (via Terraform/Ansible ou manuellement)

# 2. Déployer l'application
git clone ... && ./deploy.sh

# 3. Ajouter au load balancer
# Dans nginx.conf:
upstream azalscore {
    server 10.0.0.1:8000;
    server 10.0.0.2:8000;  # Nouvelle instance
}

# 4. Recharger nginx
sudo nginx -t && sudo systemctl reload nginx
```

### Scale vertical (augmenter les ressources)

1. Prévenir les utilisateurs (maintenance)
2. Arrêter les services
3. Modifier la VM (CPU/RAM)
4. Redémarrer et vérifier

---

## Checklist post-incident performance

- [ ] Identifier la root cause
- [ ] Vérifier que les métriques sont revenues à la normale
- [ ] Documenter les actions prises
- [ ] Planifier les améliorations (index, cache, scaling)
- [ ] Mettre à jour les seuils d'alerte si nécessaire
