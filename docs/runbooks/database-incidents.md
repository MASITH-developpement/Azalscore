# Runbook: Incidents Base de Données

## Alerte: PostgreSQLDown

**Sévérité:** SEV1 (CRITIQUE)
**Temps de réponse:** 15 minutes

### Symptômes
- Alerte Prometheus `PostgreSQLDown`
- Erreurs 500 sur les endpoints API
- Logs: `OperationalError: could not connect to server`

### Diagnostic

```bash
# 1. Vérifier le statut PostgreSQL
sudo systemctl status postgresql

# 2. Vérifier les connexions
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Vérifier l'espace disque
df -h /var/lib/postgresql

# 4. Vérifier les logs
sudo tail -100 /var/log/postgresql/postgresql-*-main.log
```

### Résolution

#### Cas 1: Service arrêté
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

#### Cas 2: Connexions saturées
```bash
# Voir les connexions actives
sudo -u postgres psql -c "SELECT pid, usename, application_name, state, query_start
FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# Terminer les connexions idle anciennes
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND query_start < now() - interval '1 hour';"
```

#### Cas 3: Espace disque insuffisant
```bash
# Libérer de l'espace
sudo -u postgres psql -c "VACUUM FULL;"

# Supprimer les anciens WAL
sudo -u postgres pg_archivecleanup /var/lib/postgresql/*/main/pg_wal <oldest_needed>
```

### Escalade

Si non résolu en 30 minutes:
1. Contacter DBA on-call
2. Ouvrir ticket OVH si infrastructure
3. Préparer failover vers replica si disponible

---

## Alerte: PostgreSQLHighConnections

**Sévérité:** SEV2
**Seuil:** > 80% max_connections

### Diagnostic

```bash
sudo -u postgres psql -c "
SELECT
    count(*) as total,
    count(*) FILTER (WHERE state = 'active') as active,
    count(*) FILTER (WHERE state = 'idle') as idle,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max
FROM pg_stat_activity;"
```

### Résolution

```bash
# Terminer les connexions idle
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND pid <> pg_backend_pid()
AND query_start < now() - interval '5 minutes';"

# Si persistant, augmenter temporairement max_connections
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections = 200;"
sudo systemctl reload postgresql
```

---

## Alerte: PostgreSQLReplicationLag

**Sévérité:** SEV2
**Seuil:** > 100MB ou > 5 minutes

### Diagnostic

```bash
# Sur le primary
sudo -u postgres psql -c "
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes
FROM pg_stat_replication;"
```

### Résolution

1. Vérifier la charge réseau entre primary et replica
2. Vérifier l'espace disque sur replica
3. Si lag persiste, reconstruire le replica:

```bash
# Sur le replica
sudo systemctl stop postgresql
sudo rm -rf /var/lib/postgresql/*/main/*
sudo -u postgres pg_basebackup -h <primary_ip> -D /var/lib/postgresql/*/main -P -R
sudo systemctl start postgresql
```

---

## Alerte: PostgreSQLSlowQueries

**Sévérité:** SEV3
**Seuil:** Requêtes > 5 secondes

### Diagnostic

```bash
# Voir les requêtes lentes actives
sudo -u postgres psql -c "
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;"

# Analyser les stats de requêtes (si pg_stat_statements activé)
sudo -u postgres psql -c "
SELECT
    calls,
    round(total_exec_time::numeric, 2) as total_ms,
    round(mean_exec_time::numeric, 2) as mean_ms,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;"
```

### Résolution

1. Identifier la requête problématique
2. Analyser avec EXPLAIN ANALYZE
3. Ajouter les index manquants
4. Optimiser la requête ou le code applicatif

```bash
# Exemple: Créer un index manquant
sudo -u postgres psql -d azalscore -c "
CREATE INDEX CONCURRENTLY idx_items_tenant_created
ON items (tenant_id, created_at);"
```

---

## Post-mortem template

Après tout incident SEV1/SEV2:

1. **Timeline**: Documenter chaque action avec timestamp
2. **Impact**: Nombre d'utilisateurs affectés, durée
3. **Root Cause**: Analyse approfondie
4. **Actions correctives**: Court et long terme
5. **Leçons apprises**: Ce qu'on peut améliorer
