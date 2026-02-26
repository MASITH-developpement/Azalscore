# Checklist de Déploiement Sécurité AZALSCORE

Liste de vérification exhaustive avant tout déploiement en production.

## 1. Configuration Environnement

### Variables d'environnement obligatoires

```bash
# Vérifier que ces variables sont définies et sécurisées
[ ] SECRET_KEY          # Minimum 32 caractères, unique par environnement
[ ] DATABASE_URL        # URL de connexion PostgreSQL avec SSL
[ ] REDIS_URL           # URL Redis avec authentification
[ ] ENCRYPTION_KEY      # Clé de chiffrement principale
[ ] JWT_SECRET          # Secret JWT distinct de SECRET_KEY
```

### Fichiers de configuration

```bash
[ ] .env.production existe et n'est PAS dans le dépôt git
[ ] Les secrets ne sont PAS en clair dans le code
[ ] Les fichiers de config ont les permissions 600
```

---

## 2. Base de Données

### PostgreSQL

```sql
[ ] SSL/TLS activé (sslmode=require ou verify-full)
[ ] Utilisateur applicatif avec privilèges minimaux (pas superuser)
[ ] Mot de passe fort (minimum 20 caractères)
[ ] Connexions limitées par IP (pg_hba.conf)
[ ] Audit des requêtes activé (pgaudit)
```

### Migrations

```bash
[ ] Toutes les migrations appliquées
[ ] Pas de migration en attente
[ ] Backup avant migration
```

---

## 3. Authentification & Sessions

### Configuration Sessions

```python
[ ] access_token_expire_minutes <= 15
[ ] refresh_token_expire_days <= 7
[ ] enable_token_rotation = True
[ ] enable_hijack_detection = True
[ ] max_concurrent_sessions <= 5
[ ] session_store_type = "redis" (pas "memory")
```

### Configuration MFA

```python
[ ] enable_totp = True
[ ] enable_adaptive_mfa = True
[ ] backup_codes_count >= 10
[ ] device_trust_duration_days <= 30
```

### Mots de passe

```python
[ ] min_length >= 12
[ ] require_uppercase = True
[ ] require_lowercase = True
[ ] require_digits = True
[ ] require_special = True
[ ] password_history_count >= 12
[ ] hash_algorithm = "argon2"
```

---

## 4. Chiffrement

### Clés

```bash
[ ] Clés de production distinctes de staging/dev
[ ] Rotation des clés configurée (90 jours max)
[ ] Backup sécurisé des clés
[ ] Accès aux clés restreint et audité
```

### Algorithmes

```python
[ ] AES-256-GCM pour le chiffrement des données
[ ] RSA-2048 minimum pour les clés asymétriques
[ ] Argon2 pour le hachage des mots de passe
```

### Données sensibles

```bash
[ ] Cartes bancaires tokenisées (pas stockées en clair)
[ ] IBAN chiffrés
[ ] Données personnelles chiffrées au repos
```

---

## 5. Réseau & TLS

### Certificats

```bash
[ ] Certificat valide (pas expiré)
[ ] Chaîne de certificats complète
[ ] Clé privée protégée (permissions 600)
[ ] Renouvellement automatique configuré
```

### Configuration TLS

```nginx
[ ] TLS 1.2 minimum (TLS 1.3 préféré)
[ ] Cipher suites sécurisées uniquement
[ ] HSTS activé (max-age >= 1 an)
[ ] OCSP Stapling activé
```

### Headers HTTP

```bash
[ ] X-Content-Type-Options: nosniff
[ ] X-Frame-Options: DENY
[ ] X-XSS-Protection: 1; mode=block
[ ] Content-Security-Policy configuré
[ ] Strict-Transport-Security présent
[ ] Referrer-Policy: strict-origin-when-cross-origin
```

---

## 6. API & Rate Limiting

### CORS

```python
[ ] allowed_origins limité aux domaines autorisés
[ ] Pas de wildcard (*) en production
[ ] Credentials correctement configurés
```

### Rate Limiting

```python
[ ] requests_per_minute <= 100 par utilisateur
[ ] auth_requests_per_minute <= 10
[ ] export_requests_per_hour <= 10
[ ] Rate limiting par IP activé
```

### Validation

```bash
[ ] Toutes les entrées utilisateur validées
[ ] Pas d'injection SQL possible
[ ] Pas de XSS possible
[ ] Protection CSRF activée
```

---

## 7. Audit & Monitoring

### Journalisation

```python
[ ] audit_authentication = True
[ ] audit_authorization = True
[ ] audit_data_access = True
[ ] audit_data_modification = True
[ ] retention_days >= 2555 (7 ans)
```

### SIEM

```bash
[ ] Intégration SIEM configurée et testée
[ ] Alertes temps réel activées
[ ] Dashboard de monitoring opérationnel
```

### Alertes

```bash
[ ] Alerte brute force configurée
[ ] Alerte accès suspect configurée
[ ] Alerte modification critique configurée
[ ] Notification équipe sécurité testée
```

---

## 8. Disaster Recovery

### Backups

```bash
[ ] Backup automatique configuré
[ ] Backup testé (restauration vérifiée)
[ ] Backup chiffré
[ ] Backup hors-site (autre région)
[ ] Rétention conforme (30 jours minimum)
```

### Réplication

```bash
[ ] Réplication cross-région active
[ ] Failover testé
[ ] RTO documenté et réaliste
[ ] RPO documenté et respecté
```

### Plan DR

```bash
[ ] Procédure de failover documentée
[ ] Équipe formée
[ ] Test DR effectué (< 30 jours)
[ ] Contacts d'urgence à jour
```

---

## 9. Conformité

### RGPD

```bash
[ ] Registre des traitements à jour
[ ] DPO désigné et contactable
[ ] Procédure droit d'accès fonctionnelle
[ ] Procédure droit à l'effacement fonctionnelle
[ ] Portabilité des données testée
[ ] Consentements correctement gérés
```

### NF525 (Comptabilité)

```bash
[ ] Chaîne de hash SHA-256 active
[ ] Horodatage sécurisé
[ ] Export FEC conforme
[ ] Clôture annuelle implémentée
[ ] Archivage légal configuré
```

### Audit

```bash
[ ] Dernier audit sécurité < 12 mois
[ ] Vulnérabilités critiques corrigées
[ ] Pentest effectué
[ ] Rapport d'audit disponible
```

---

## 10. Pré-déploiement

### Tests

```bash
[ ] Tests unitaires passent (100%)
[ ] Tests d'intégration passent
[ ] Tests de sécurité passent
[ ] Scan de vulnérabilités effectué
[ ] Pas de dépendance vulnérable
```

### Code Review

```bash
[ ] Code reviewé par 2 personnes minimum
[ ] Pas de secret dans le code
[ ] Pas de TODO de sécurité en suspens
[ ] Documentation à jour
```

### Déploiement

```bash
[ ] Rollback préparé et testé
[ ] Communication planifiée
[ ] Équipe on-call disponible
[ ] Monitoring prêt
```

---

## Validation Finale

| Étape | Validé par | Date |
|-------|------------|------|
| Configuration | __________ | __/__/____ |
| Base de données | __________ | __/__/____ |
| Authentification | __________ | __/__/____ |
| Chiffrement | __________ | __/__/____ |
| Réseau & TLS | __________ | __/__/____ |
| API | __________ | __/__/____ |
| Audit | __________ | __/__/____ |
| DR | __________ | __/__/____ |
| Conformité | __________ | __/__/____ |
| Tests | __________ | __/__/____ |

**Approbation finale:**

Responsable Sécurité: _________________ Date: __/__/____

Responsable Technique: _________________ Date: __/__/____
