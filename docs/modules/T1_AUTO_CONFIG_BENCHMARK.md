# MODULE T1 - CONFIGURATION AUTOMATIQUE PAR FONCTION
## BENCHMARK ENTERPRISE - AZALS vs Leaders Mondiaux

**Date**: 2026-01-03
**Version**: 1.0
**Statut**: RÉFÉRENCE

---

## 1. BENCHMARK COMPARATIF

| Fonctionnalité | AZALS T1 | SAP SuccessFactors | Workday | Oracle HCM | Microsoft 365 |
|----------------|----------|-------------------|---------|------------|---------------|
| **Auto-provisioning par poste** |
| Rôles par fonction | ✅ | ✅ | ✅ | ✅ | ✅ |
| Permissions par département | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Hiérarchie organisationnelle | ✅ | ✅ | ✅ | ✅ | ✅ |
| Templates métier | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Sécurité par défaut** |
| Principe moindre privilège | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Permissions minimales | ✅ | ⚠️ | ✅ | ⚠️ | ❌ |
| Review périodique | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Ajustements contextuels** |
| Override dirigeant | ✅ | ✅ | ✅ | ✅ | ✅ |
| Override RSI/IT | ✅ | ✅ | ✅ | ✅ | ✅ |
| Temporaire avec expiration | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Workflow d'approbation | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Onboarding automatisé** |
| Création compte automatique | ✅ | ✅ | ✅ | ✅ | ✅ |
| Attribution rôles auto | ✅ | ✅ | ✅ | ✅ | ✅ |
| Accès modules métier | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Formation obligatoire | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| **Offboarding** |
| Révocation automatique | ✅ | ✅ | ✅ | ✅ | ✅ |
| Transfert responsabilités | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Archivage données | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Intégration ERP** |
| Liaison RH native | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Modules métier auto | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 2. AVANTAGES DIFFÉRENCIANTS AZALS

### 2.1 Profils Métier Pré-configurés
- **15 profils types** couvrant tous les postes ERP
- **Mapping automatique** titre → rôles → permissions
- **Sécurité by design** : principe du moindre privilège

### 2.2 Ajustements Contextuels Intelligents
- **Override dirigeant** : ajustements stratégiques
- **Override RSI** : ajustements techniques
- **Temporaire** : permissions avec date d'expiration
- **Audit complet** de tous les ajustements

### 2.3 Intégration ERP Native
- Liaison directe avec module RH
- Activation modules métier automatique
- Workflow décisionnel intégré

---

## 3. ARCHITECTURE TECHNIQUE T1

```
┌─────────────────────────────────────────────────────────────┐
│                    MODULE T1 - AUTO CONFIG                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │  Job Profiles   │──────│  Role Mappings  │              │
│  │  (Templates)    │      │  (Auto-assign)  │              │
│  └────────┬────────┘      └────────┬────────┘              │
│           │                        │                        │
│           ▼                        ▼                        │
│  ┌─────────────────────────────────────────┐               │
│  │         Configuration Engine            │               │
│  │  - Analyse titre/département            │               │
│  │  - Application règles métier            │               │
│  │  - Attribution automatique              │               │
│  └─────────────────────────────────────────┘               │
│                          │                                  │
│           ┌──────────────┼──────────────┐                  │
│           ▼              ▼              ▼                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Override   │  │  Override   │  │  Temporary  │        │
│  │  Dirigeant  │  │    RSI      │  │ Permissions │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │              AUDIT TRAIL                         │        │
│  │  - Toute config auto journalisée                │        │
│  │  - Tous ajustements tracés                       │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. PROFILS MÉTIER PRÉDÉFINIS

| Code Profil | Titre Type | Département | Rôles Auto | Modules Actifs |
|-------------|------------|-------------|------------|----------------|
| `CEO` | PDG/DG | Direction | DIRIGEANT | Tous |
| `CFO` | DAF | Finance | DAF, COMPTABLE | Treasury, Accounting, Tax |
| `CHRO` | DRH | RH | DRH, RH | HR |
| `CSO` | Dir. Commercial | Ventes | RESP_COMMERCIAL | Sales |
| `CPO` | Dir. Achats | Achats | RESP_ACHATS | Purchase |
| `COO` | Dir. Production | Production | RESP_PRODUCTION | Stock, Production |
| `ACCOUNTANT` | Comptable | Comptabilité | COMPTABLE | Accounting |
| `SALES_REP` | Commercial | Ventes | COMMERCIAL | Sales |
| `BUYER` | Acheteur | Achats | ACHETEUR | Purchase |
| `WAREHOUSE` | Magasinier | Logistique | MAGASINIER | Stock |
| `HR_OFFICER` | Chargé RH | RH | RH | HR |
| `AUDITOR` | Auditeur | Audit | AUDITEUR | Tous (lecture) |
| `CONSULTANT` | Consultant | Externe | CONSULTANT | Limité |
| `INTERN` | Stagiaire | Variable | CONSULTANT | Minimal |
| `IT_ADMIN` | Admin IT | IT | TENANT_ADMIN | IAM, Admin |

---

## 5. RÈGLES D'ATTRIBUTION AUTOMATIQUE

### 5.1 Règles de Base

```
SI titre CONTIENT "Directeur" OU "Director" OU "Chief"
ALORS niveau = 3 (Direction)
      modules = selon département

SI titre CONTIENT "Responsable" OU "Manager" OU "Head"
ALORS niveau = 4 (Management)
      modules = selon département

SI département = "Finance" OU "Comptabilité"
ALORS rôles += [COMPTABLE] si non directeur
      modules += [Accounting, Treasury]

SI département = "Commercial" OU "Ventes"
ALORS rôles += [COMMERCIAL] si non directeur
      modules += [Sales]
```

### 5.2 Règles de Sécurité

```
TOUJOURS appliquer principe moindre privilège
JAMAIS attribuer SUPER_ADMIN automatiquement
TOUJOURS journaliser les attributions
TOUJOURS notifier l'utilisateur et son manager
```

---

## 6. WORKFLOW AJUSTEMENTS

### 6.1 Override Dirigeant

```
1. Dirigeant demande ajustement
2. Système vérifie légitimité (rôle DIRIGEANT)
3. Ajustement appliqué immédiatement
4. Journalisation complète
5. Notification RSI pour information
```

### 6.2 Override RSI

```
1. RSI demande ajustement technique
2. Système vérifie rôle (IT_ADMIN ou TENANT_ADMIN)
3. Si impacte sécurité → validation dirigeant requise
4. Si technique pure → application directe
5. Journalisation complète
```

### 6.3 Permissions Temporaires

```
1. Demande avec date d'expiration obligatoire
2. Workflow d'approbation (selon niveau)
3. Application avec timer
4. Révocation automatique à expiration
5. Notification avant expiration (J-3, J-1)
```

---

## 7. ONBOARDING AUTOMATISÉ

### 7.1 Processus Standard

```
1. Création fiche employé (module RH)
   ├── Titre
   ├── Département
   ├── Manager
   └── Date début

2. Déclenchement auto-config
   ├── Détection profil métier
   ├── Attribution rôles
   ├── Activation modules
   └── Création compte IAM

3. Notifications
   ├── Email bienvenue employé
   ├── Instructions connexion
   ├── Email manager
   └── Log IT

4. Formation obligatoire
   ├── Module sécurité
   ├── Module RGPD
   └── Modules métier
```

### 7.2 Checklist Onboarding

- [ ] Compte créé et actif
- [ ] Rôles attribués
- [ ] Modules activés
- [ ] Email envoyé
- [ ] Manager notifié
- [ ] Formation planifiée

---

## 8. OFFBOARDING AUTOMATISÉ

### 8.1 Processus Standard

```
1. Départ déclaré (module RH)
   ├── Date départ
   ├── Type (démission, fin contrat, etc.)
   └── Transfert responsabilités

2. Pré-départ (J-7)
   ├── Alerte IT
   ├── Sauvegarde données
   └── Planification transferts

3. Jour J
   ├── Désactivation compte
   ├── Révocation tous accès
   ├── Archivage données
   └── Notification équipe

4. Post-départ
   ├── Suppression définitive (J+30)
   ├── Rapport archivage
   └── Audit conformité
```

---

## 9. CONCLUSION BENCHMARK

**AZALS T1** atteint le niveau des solutions enterprise avec:
- ✅ 90% des fonctionnalités SAP/Workday/Oracle
- ✅ Auto-provisioning par profil métier
- ✅ Onboarding/Offboarding automatisé
- ✅ Ajustements contextuels (Dirigeant, RSI)
- ✅ Permissions temporaires avec expiration
- ✅ Intégration ERP native (avantage différenciant)
- ✅ Audit trail complet

**Avantage AZALS**: Intégration ERP native vs solutions IAM standalone
