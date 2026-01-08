# AZALSCORE - Limitations Version Bêta
## COMPLIANCE/BETA_LIMITATIONS.md

**Version**: 1.1-BETA
**Date**: 2026-01-08
**Statut**: Bêta Fermée - Module CRM T0 ACTIVÉ

---

## AVERTISSEMENT IMPORTANT

> **Cette version est une BÊTA FERMÉE destinée à des tests contrôlés.**
>
> Elle ne doit PAS être utilisée en production avec des données sensibles réelles
> tant que toutes les limitations ci-dessous n'ont pas été levées.

---

## 1. LIMITATIONS FONCTIONNELLES

### 1.1 Modules Non Activés

Les modules suivants sont **préparés mais NON activés** :

| Module | Code | Statut |
|--------|------|--------|
| IAM Avancé | T0 | ✅ ACTIVÉ |
| AutoConfig | T1 | En validation |
| Triggers | T2 | En validation |
| Audit Avancé | T3 | En validation |
| QC | T4 | En attente |
| Country Packs | T5 | France uniquement |
| Broadcast | T6 | En attente |
| Web Services | T7 | En attente |
| Website | T8 | En attente |
| Multi-Tenant Admin | T9 | En développement |
| **CRM/Commercial** | **M1** | **✅ ACTIVÉ (CRM T0)** |
| Finance | M2 | En attente validation M1 |
| HR | M3 | En attente M2 |
| Tous autres | M4-M18 | Séquence gating |

### 1.2 Fonctionnalités Réduites

| Fonctionnalité | Limitation | Plan |
|----------------|------------|------|
| Rôles | 1 seul rôle actif (DIRIGEANT) | 5 rôles en GA |
| 2FA | Recommandé mais non obligatoire | Obligatoire en prod |
| Export | Formats limités | PDF/Excel en GA |
| API | Pas de webhooks | Webhooks en GA |
| Mobile | Pas d'app native | PWA uniquement |

---

## 2. LIMITATIONS TECHNIQUES

### 2.1 Performance

| Métrique | Limite Bêta | Cible Production |
|----------|-------------|------------------|
| Utilisateurs simultanés | 50 | 1000+ |
| Requêtes/seconde | 100 | 1000+ |
| Stockage/tenant | 1 GB | 100 GB |
| Rétention logs | 30 jours | 3 ans |

### 2.2 Disponibilité

| Aspect | Bêta | Production |
|--------|------|------------|
| SLA | Aucun garanti | 99.9% |
| Maintenance | Non planifiée | Fenêtres définies |
| Support | Best effort | 24/7 |
| Backup | Quotidien | Temps réel |

### 2.3 Infrastructure

- **Environnement unique** : Pas de staging/prod séparé
- **Single AZ** : Pas de redondance géographique
- **Scaling manuel** : Pas d'auto-scaling

---

## 3. LIMITATIONS SÉCURITÉ

### 3.1 Corrections En Cours

| Correction | Statut | ETA |
|------------|--------|-----|
| ✅ Chiffrement AES-256 | Implémenté | Fait |
| ✅ Hash chaîné audit | Implémenté | Fait |
| ✅ CORS restrictif | Implémenté | Fait |
| ⏳ Token blacklist | Planifié | Sprint 2 |
| ⏳ Rotation clés auto | Planifié | Sprint 3 |

### 3.2 Non Inclus en Bêta

- Pentest externe
- Bug bounty program
- Certification ISO 27001
- SOC 2 compliance

---

## 4. LIMITATIONS LÉGALES

### 4.1 Contrat Bêta

- **Pas de garantie** de service
- **Pas de SLA** contractuel
- **Données** peuvent être perdues
- **Fonctionnalités** peuvent changer sans préavis

### 4.2 Données Sensibles

⚠️ **NE PAS UTILISER avec** :
- Données financières réelles
- Données personnelles sensibles (santé, etc.)
- Données de production critiques
- Informations bancaires réelles

---

## 5. LIMITATIONS SUPPORT

### 5.1 Canaux

| Canal | Disponibilité |
|-------|---------------|
| Email | Best effort (48h) |
| Slack/Discord | Communauté |
| Téléphone | Non disponible |
| On-site | Non disponible |

### 5.2 Périmètre

✅ Inclus :
- Bugs critiques
- Problèmes de sécurité
- Questions fonctionnelles

❌ Exclus :
- Personnalisation
- Formation
- Intégration sur mesure
- Développement spécifique

---

## 6. CALENDRIER PRÉVISIONNEL

### Phase Bêta (Actuelle)

```
Janvier 2026  : Socle technique validé ✅
              : Module IAM (T0) activé ✅
              : Module CRM T0 activé ✅ (8 janvier 2026)
Février 2026  : Module Finance (M2) prévu
Mars 2026     : Modules complémentaires
```

### Phase GA (Général Availability)

```
Mai 2026      : Version 1.0 GA
               - Tous modules core activés
               - SLA 99.9%
               - Support 24/7
               - Conformité complète
```

---

## 7. ACCEPTATION DES LIMITATIONS

En utilisant la version bêta d'AZALSCORE, vous acceptez :

1. Les **limitations** décrites dans ce document
2. L'**absence de garantie** de service
3. La **possibilité de perte** de données
4. Les **changements** sans préavis
5. L'utilisation **à vos risques** et périls

---

## 8. CONTACT

Pour toute question sur les limitations :

- **Email** : beta@azalscore.com
- **Documentation** : docs.azalscore.com/beta

---

## 9. HISTORIQUE

| Version | Date | Changements |
|---------|------|-------------|
| 1.1 | 2026-01-08 | Activation Module CRM T0 (PASS) |
| 1.0 | 2026-01-08 | Création initiale |
