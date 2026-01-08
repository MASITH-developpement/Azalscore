# AZALSCORE - Plan de Gestion des Incidents
## COMPLIANCE/INCIDENT_PLAN.md

**Version**: 1.0
**Date**: 2026-01-08
**Classification**: Document interne

---

## 1. OBJECTIF

Ce document définit les procédures de gestion des incidents de sécurité et de disponibilité pour AZALSCORE.

---

## 2. CLASSIFICATION DES INCIDENTS

### 2.1 Niveaux de Sévérité

| Niveau | Description | Temps de Réponse | Escalade |
|--------|-------------|------------------|----------|
| **P1 - Critique** | Fuite de données, compromission système | 15 minutes | CEO + CTO immédiat |
| **P2 - Majeur** | Service indisponible, faille sécurité | 1 heure | CTO + Ops Lead |
| **P3 - Modéré** | Dégradation performance, bug bloquant | 4 heures | Ops Lead |
| **P4 - Mineur** | Bug non bloquant, incident isolé | 24 heures | Support |

### 2.2 Exemples par Niveau

**P1 - Critique**
- Fuite de données client détectée
- Accès non autorisé au système
- Ransomware / malware
- Compromission de clés cryptographiques

**P2 - Majeur**
- Service totalement indisponible > 30min
- Vulnérabilité critique exploitable
- Perte de données (backup dispo)
- Attaque DDoS réussie

**P3 - Modéré**
- Ralentissement significatif (>2x normal)
- Bug bloquant pour certains utilisateurs
- Échec de backup quotidien
- Alerte sécurité non critique

**P4 - Mineur**
- Bug cosmétique
- Lenteur ponctuelle
- Erreur utilisateur
- Question de configuration

---

## 3. PROCESSUS DE RÉPONSE

### 3.1 Workflow Standard

```
┌──────────────────┐
│   DÉTECTION      │  ← Alerting, monitoring, signalement
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   TRIAGE         │  ← Classification P1/P2/P3/P4
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   CONTAINMENT    │  ← Isolation, limitation impact
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   ERADICATION    │  ← Correction root cause
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   RECOVERY       │  ← Restauration service
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   POST-MORTEM    │  ← Analyse, améliorations
└──────────────────┘
```

### 3.2 Checklist P1 (Critique)

```markdown
□ T+0min  : Accusé de réception
□ T+5min  : Notification CTO + CEO
□ T+10min : Équipe incident constituée
□ T+15min : Premier diagnostic
□ T+30min : Containment actif
□ T+1h    : Communication clients si nécessaire
□ T+4h    : Root cause identifiée
□ T+24h   : Post-mortem préliminaire
□ T+72h   : Post-mortem complet
```

---

## 4. PROCÉDURES SPÉCIFIQUES

### 4.1 Fuite de Données (P1)

**Containment immédiat** :
```bash
# 1. Révoquer les accès compromis
python manage.py revoke_all_tokens --tenant=TENANT_ID

# 2. Bloquer les IPs suspectes
python manage.py block_ip --ip=X.X.X.X

# 3. Activer le mode maintenance si nécessaire
python manage.py maintenance_mode --enable
```

**Actions obligatoires** :
1. Identifier l'étendue de la fuite
2. Préserver les preuves (logs, dumps)
3. Notifier CNIL sous 72h si données personnelles
4. Notifier les clients affectés
5. Engager audit forensique externe

### 4.2 Compromission de Clés (P1)

**Rotation d'urgence** :
```bash
# 1. Générer nouvelles clés
python -c "import secrets; print(secrets.token_urlsafe(64))"  # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY

# 2. Déployer avec nouvelles clés
# 3. Invalider tous les tokens existants
python manage.py invalidate_all_sessions

# 4. Re-chiffrer les données si ENCRYPTION_KEY compromise
python manage.py reencrypt_data --old-key=XXX --new-key=YYY
```

### 4.3 Indisponibilité Service (P2)

**Diagnostic rapide** :
```bash
# 1. Vérifier status
curl https://api.azalscore.com/health
curl https://api.azalscore.com/health/db

# 2. Vérifier logs
kubectl logs -f deployment/api --tail=100

# 3. Vérifier ressources
kubectl top pods
kubectl describe pod api-xxx
```

**Procédure de recovery** :
1. Identifier le composant défaillant
2. Rollback si déploiement récent
3. Scale up si saturation
4. Failover si DB défaillante
5. Communication status page

### 4.4 Attaque DDoS (P2)

**Actions immédiates** :
1. Activer mode protection renforcé Cloudflare
2. Augmenter les seuils rate limiting
3. Bloquer les ranges IP attaquants
4. Activer auto-scaling d'urgence
5. Contacter le fournisseur anti-DDoS

---

## 5. COMMUNICATION

### 5.1 Interne

| Niveau | Canal | Destinataires |
|--------|-------|---------------|
| P1 | Appel + SMS + Slack | CEO, CTO, toute l'équipe |
| P2 | Slack + Email | CTO, Ops, Dev Lead |
| P3 | Slack | Ops, Dev concernés |
| P4 | Ticket | Support |

### 5.2 Externe

| Niveau | Communication |
|--------|---------------|
| P1 | Email immédiat + Status page + Blog si fuite |
| P2 | Status page + Email si > 1h |
| P3 | Status page si impact visible |
| P4 | Aucune |

### 5.3 Templates

**Email P1 - Fuite de données** :
```
Objet: [URGENT] Incident de sécurité AZALSCORE - Action requise

Cher client,

Nous vous informons qu'un incident de sécurité a été détecté le [DATE] à [HEURE].

Ce qui s'est passé:
[Description factuelle]

Données potentiellement affectées:
[Liste]

Actions prises:
[Liste]

Actions recommandées pour vous:
- Changez votre mot de passe
- Activez la 2FA si ce n'est pas fait
- Surveillez vos comptes

Nous restons à votre disposition.

L'équipe AZALSCORE
```

---

## 6. CONTACTS D'URGENCE

### 6.1 Internes

| Rôle | Nom | Téléphone | Email |
|------|-----|-----------|-------|
| CTO | [À remplir] | +33 X XX XX XX XX | cto@azalscore.com |
| Ops Lead | [À remplir] | +33 X XX XX XX XX | ops@azalscore.com |
| Dev Lead | [À remplir] | +33 X XX XX XX XX | dev@azalscore.com |
| CEO | [À remplir] | +33 X XX XX XX XX | ceo@azalscore.com |

### 6.2 Externes

| Service | Contact |
|---------|---------|
| Hébergeur | Support 24/7 |
| CNIL | [En cas de fuite RGPD] |
| Assurance Cyber | [Numéro police] |
| Forensique | [Prestataire] |

---

## 7. POST-MORTEM

### 7.1 Template

```markdown
# Post-Mortem Incident [ID]

## Résumé
- Date/Heure:
- Durée:
- Impact:
- Sévérité: P1/P2/P3/P4

## Timeline
- HH:MM - Événement X
- HH:MM - Événement Y
- ...

## Root Cause
[Description technique]

## Impact
- Utilisateurs affectés: X
- Données affectées: Y
- Durée indisponibilité: Z

## Actions de Remédiation
1. [Action immédiate]
2. [Action court terme]
3. [Action long terme]

## Leçons Apprises
- [Leçon 1]
- [Leçon 2]

## Améliorations Planifiées
- [ ] Amélioration A (Owner, Date)
- [ ] Amélioration B (Owner, Date)
```

### 7.2 Délais

| Sévérité | Post-Mortem Requis | Délai |
|----------|-------------------|-------|
| P1 | Obligatoire | 72h |
| P2 | Obligatoire | 1 semaine |
| P3 | Recommandé | 2 semaines |
| P4 | Optionnel | - |

---

## 8. TESTS ET EXERCICES

### 8.1 Fréquence

| Type | Fréquence |
|------|-----------|
| Test backup/restore | Mensuel |
| Exercice incident P2 | Trimestriel |
| Exercice incident P1 | Semestriel |
| Revue du plan | Annuel |

### 8.2 Checklist de Test

```markdown
□ Backup restaurable en < 1h
□ Failover DB fonctionnel
□ Rotation clés sans downtime
□ Contacts d'urgence à jour
□ Procédures documentées à jour
□ Équipe formée aux procédures
```

---

## 9. HISTORIQUE

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 1.0 | 2026-01-08 | Système | Création initiale |
