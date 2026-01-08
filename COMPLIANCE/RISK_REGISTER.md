# AZALSCORE - Registre des Risques
## COMPLIANCE/RISK_REGISTER.md

**Version**: 1.0
**Date**: 2026-01-08
**Prochaine revue**: 2026-04-08

---

## 1. MATRICE D'ÉVALUATION

### 1.1 Probabilité

| Niveau | Description | Score |
|--------|-------------|-------|
| Rare | < 10% / an | 1 |
| Peu probable | 10-30% / an | 2 |
| Possible | 30-50% / an | 3 |
| Probable | 50-70% / an | 4 |
| Quasi certain | > 70% / an | 5 |

### 1.2 Impact

| Niveau | Description | Score |
|--------|-------------|-------|
| Négligeable | Impact minimal | 1 |
| Mineur | Perturbation limitée | 2 |
| Modéré | Perturbation significative | 3 |
| Majeur | Perturbation critique | 4 |
| Catastrophique | Survie de l'entreprise | 5 |

### 1.3 Criticité

```
Criticité = Probabilité × Impact
- 1-4   : Faible (vert)
- 5-9   : Modéré (jaune)
- 10-14 : Élevé (orange)
- 15-25 : Critique (rouge)
```

---

## 2. RISQUES TECHNIQUES

### R-TECH-001: Fuite de Données Inter-Tenant

| Attribut | Valeur |
|----------|--------|
| **ID** | R-TECH-001 |
| **Catégorie** | Sécurité |
| **Description** | Accès non autorisé aux données d'un autre tenant |
| **Probabilité** | 2 (Peu probable) |
| **Impact** | 5 (Catastrophique) |
| **Criticité** | **10 (Élevé)** |
| **Mesures existantes** | Triple validation tenant, RBAC, tests isolation |
| **Mesures planifiées** | Audit sécurité externe |
| **Responsable** | CTO |
| **Statut** | Atténué |

### R-TECH-002: Compromission de Clés Cryptographiques

| Attribut | Valeur |
|----------|--------|
| **ID** | R-TECH-002 |
| **Catégorie** | Sécurité |
| **Description** | Vol ou exposition des clés SECRET_KEY, ENCRYPTION_KEY |
| **Probabilité** | 2 (Peu probable) |
| **Impact** | 5 (Catastrophique) |
| **Criticité** | **10 (Élevé)** |
| **Mesures existantes** | Clés hors code, validation env, rotation documentée |
| **Mesures planifiées** | HSM / AWS KMS |
| **Responsable** | CTO |
| **Statut** | Partiellement atténué |

### R-TECH-003: Injection SQL

| Attribut | Valeur |
|----------|--------|
| **ID** | R-TECH-003 |
| **Catégorie** | Sécurité |
| **Description** | Injection de code SQL malveillant |
| **Probabilité** | 2 (Peu probable) |
| **Impact** | 4 (Majeur) |
| **Criticité** | **8 (Modéré)** |
| **Mesures existantes** | ORM SQLAlchemy, requêtes paramétrées |
| **Mesures planifiées** | Tests SQLMap réguliers |
| **Responsable** | Dev Lead |
| **Statut** | Atténué |

### R-TECH-004: Attaque DDoS

| Attribut | Valeur |
|----------|--------|
| **ID** | R-TECH-004 |
| **Catégorie** | Disponibilité |
| **Description** | Saturation de l'infrastructure par attaque distribuée |
| **Probabilité** | 3 (Possible) |
| **Impact** | 3 (Modéré) |
| **Criticité** | **9 (Modéré)** |
| **Mesures existantes** | Rate limiting, IP blocklist, Cloudflare |
| **Mesures planifiées** | Auto-scaling, WAF avancé |
| **Responsable** | Ops |
| **Statut** | Partiellement atténué |

### R-TECH-005: Perte de Données

| Attribut | Valeur |
|----------|--------|
| **ID** | R-TECH-005 |
| **Catégorie** | Continuité |
| **Description** | Perte irrécupérable de données clients |
| **Probabilité** | 1 (Rare) |
| **Impact** | 5 (Catastrophique) |
| **Criticité** | **5 (Modéré)** |
| **Mesures existantes** | Backups quotidiens, réplication DB |
| **Mesures planifiées** | DR site, tests restauration mensuels |
| **Responsable** | Ops |
| **Statut** | Partiellement atténué |

---

## 3. RISQUES OPÉRATIONNELS

### R-OPS-001: Indisponibilité Service

| Attribut | Valeur |
|----------|--------|
| **ID** | R-OPS-001 |
| **Catégorie** | Disponibilité |
| **Description** | Service inaccessible > 4h |
| **Probabilité** | 3 (Possible) |
| **Impact** | 4 (Majeur) |
| **Criticité** | **12 (Élevé)** |
| **Mesures existantes** | Health checks, alerting, monitoring |
| **Mesures planifiées** | Multi-AZ, failover automatique |
| **Responsable** | Ops |
| **Statut** | Partiellement atténué |

### R-OPS-002: Erreur de Migration

| Attribut | Valeur |
|----------|--------|
| **ID** | R-OPS-002 |
| **Catégorie** | Technique |
| **Description** | Migration DB corrompant les données |
| **Probabilité** | 2 (Peu probable) |
| **Impact** | 4 (Majeur) |
| **Criticité** | **8 (Modéré)** |
| **Mesures existantes** | Migrations versionnées, backup pré-migration |
| **Mesures planifiées** | Environnement staging obligatoire |
| **Responsable** | Dev Lead |
| **Statut** | Atténué |

---

## 4. RISQUES LÉGAUX / CONFORMITÉ

### R-LEG-001: Non-Conformité RGPD

| Attribut | Valeur |
|----------|--------|
| **ID** | R-LEG-001 |
| **Catégorie** | Conformité |
| **Description** | Violation des exigences RGPD |
| **Probabilité** | 2 (Peu probable) |
| **Impact** | 5 (Catastrophique) |
| **Criticité** | **10 (Élevé)** |
| **Mesures existantes** | Chiffrement, consentement, droit effacement |
| **Mesures planifiées** | DPO, audit RGPD externe |
| **Responsable** | Juridique |
| **Statut** | Partiellement atténué |

### R-LEG-002: Faille Sécurité Exploitée

| Attribut | Valeur |
|----------|--------|
| **ID** | R-LEG-002 |
| **Catégorie** | Sécurité |
| **Description** | Exploitation publique d'une vulnérabilité |
| **Probabilité** | 2 (Peu probable) |
| **Impact** | 5 (Catastrophique) |
| **Criticité** | **10 (Élevé)** |
| **Mesures existantes** | Secure coding, tests sécurité, updates |
| **Mesures planifiées** | Bug bounty, pentest annuel |
| **Responsable** | CTO |
| **Statut** | Partiellement atténué |

---

## 5. MATRICE DE SYNTHÈSE

| ID | Risque | P | I | C | Statut |
|----|--------|---|---|---|--------|
| R-TECH-001 | Fuite inter-tenant | 2 | 5 | 10 | 🟠 |
| R-TECH-002 | Compromission clés | 2 | 5 | 10 | 🟠 |
| R-TECH-003 | Injection SQL | 2 | 4 | 8 | 🟡 |
| R-TECH-004 | DDoS | 3 | 3 | 9 | 🟡 |
| R-TECH-005 | Perte données | 1 | 5 | 5 | 🟡 |
| R-OPS-001 | Indisponibilité | 3 | 4 | 12 | 🟠 |
| R-OPS-002 | Erreur migration | 2 | 4 | 8 | 🟡 |
| R-LEG-001 | Non-conformité RGPD | 2 | 5 | 10 | 🟠 |
| R-LEG-002 | Faille exploitée | 2 | 5 | 10 | 🟠 |

---

## 6. PLAN D'ACTIONS PRIORITAIRES

### Priorité 1 (Immédiat)

1. ✅ Implémenter chiffrement AES-256
2. ✅ Tests isolation inter-tenant
3. ⏳ Audit sécurité externe

### Priorité 2 (Court terme)

1. ⏳ Migration vers HSM / KMS
2. ⏳ Bug bounty program
3. ⏳ DR site secondaire

### Priorité 3 (Moyen terme)

1. ⏳ Pentest annuel
2. ⏳ Certification ISO 27001
3. ⏳ SOC 2 Type II

---

## 7. REVUE ET APPROBATION

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| CTO | [À remplir] | - | __________ |
| RSSI | [À remplir] | - | __________ |
| DPO | [À remplir] | - | __________ |

---

## 8. HISTORIQUE

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 1.0 | 2026-01-08 | Système | Création initiale |
