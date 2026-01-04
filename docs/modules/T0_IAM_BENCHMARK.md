# MODULE T0 - GESTION DES UTILISATEURS & RÔLES (IAM)
## BENCHMARK ENTERPRISE - AZALS vs Leaders Mondiaux

**Date**: 2026-01-03
**Version**: 1.0
**Statut**: RÉFÉRENCE

---

## 1. BENCHMARK COMPARATIF

| Fonctionnalité | AZALS T0 | Keycloak | Auth0 | Okta | AWS IAM |
|----------------|----------|----------|-------|------|---------|
| **Authentification** |
| Login/Password | ✅ | ✅ | ✅ | ✅ | ✅ |
| JWT Tokens | ✅ | ✅ | ✅ | ✅ | ✅ |
| Refresh Tokens | ✅ | ✅ | ✅ | ✅ | ✅ |
| MFA/2FA (TOTP) | ✅ | ✅ | ✅ | ✅ | ✅ |
| SSO/SAML | ❌ Phase 2 | ✅ | ✅ | ✅ | ✅ |
| OAuth2/OIDC | ❌ Phase 2 | ✅ | ✅ | ✅ | ✅ |
| **Gestion Utilisateurs** |
| CRUD Utilisateurs | ✅ | ✅ | ✅ | ✅ | ✅ |
| Profils étendus | ✅ | ✅ | ✅ | ✅ | ✅ |
| Groupes | ✅ | ✅ | ✅ | ✅ | ✅ |
| Invitation par email | ✅ | ✅ | ✅ | ✅ | ❌ |
| Self-registration | ✅ | ✅ | ✅ | ✅ | ❌ |
| Password policies | ✅ | ✅ | ✅ | ✅ | ✅ |
| Account lockout | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Rôles & Permissions** |
| RBAC | ✅ | ✅ | ✅ | ✅ | ✅ |
| Permissions granulaires | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rôles hiérarchiques | ✅ | ✅ | ✅ | ✅ | ❌ |
| Séparation des pouvoirs | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| Rôles par défaut | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Multi-Tenant** |
| Isolation tenant | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin par tenant | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rôles cross-tenant | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| **Sécurité** |
| Rate limiting | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit trail | ✅ | ✅ | ✅ | ✅ | ✅ |
| Session management | ✅ | ✅ | ✅ | ✅ | ✅ |
| IP whitelist | ✅ | ✅ | ✅ | ✅ | ✅ |
| Token blacklist | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Intégration ERP** |
| Liaison modules métier | ✅ | ❌ | ❌ | ❌ | ❌ |
| Workflow décisionnel | ✅ | ❌ | ❌ | ❌ | ❌ |
| Contexte dirigeant | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 2. AVANTAGES DIFFÉRENCIANTS AZALS

### 2.1 Séparation des Pouvoirs Intégrée
- **Principe**: Aucun utilisateur ne peut tout faire
- **Implémentation**: Rôles mutuellement exclusifs pour certaines actions
- **Exemple**: Un comptable ne peut pas valider ses propres écritures

### 2.2 Workflow Décisionnel Natif
- **Lien direct** avec le cockpit dirigeant
- **Validation multi-niveau** obligatoire pour actions critiques
- **Traçabilité** complète dans le journal APPEND-ONLY

### 2.3 Contexte ERP Natif
- **Rôles métier** préconfgurés (Dirigeant, DAF, RH, Commercial...)
- **Permissions** alignées sur processus ERP
- **Modules** automatiquement liés aux rôles

---

## 3. ARCHITECTURE TECHNIQUE T0

```
┌─────────────────────────────────────────────────────────────┐
│                      MODULE T0 - IAM                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Users     │  │   Roles     │  │ Permissions │          │
│  │  (profiles) │  │ (hierarchy) │  │ (granular)  │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│         ┌────────────────────────────────┐                  │
│         │         user_roles             │                  │
│         │    (many-to-many + audit)      │                  │
│         └────────────────────────────────┘                  │
│                          │                                   │
│         ┌────────────────┼────────────────┐                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Groups    │  │  Sessions   │  │   Tokens    │          │
│  │ (optional)  │  │ (tracking)  │  │ (blacklist) │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │              AUDIT TRAIL (Journal)              │        │
│  │  - Toute action IAM journalisée                 │        │
│  │  - APPEND-ONLY inaltérable                      │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. RÔLES PRÉDÉFINIS AZALS

| Code | Nom | Niveau | Description |
|------|-----|--------|-------------|
| `SUPER_ADMIN` | Super Administrateur | 0 | Accès total système (1 par installation) |
| `TENANT_ADMIN` | Admin Tenant | 1 | Gestion complète du tenant |
| `DIRIGEANT` | Dirigeant | 2 | Décisions stratégiques, validation RED |
| `DAF` | Directeur Financier | 3 | Finance, comptabilité, trésorerie |
| `DRH` | Directeur RH | 3 | Ressources humaines, paie |
| `RESPONSABLE_COMMERCIAL` | Dir. Commercial | 3 | Ventes, devis, clients |
| `RESPONSABLE_ACHATS` | Dir. Achats | 3 | Achats, fournisseurs |
| `RESPONSABLE_PRODUCTION` | Dir. Production | 3 | Production, stocks |
| `COMPTABLE` | Comptable | 4 | Saisie comptable |
| `COMMERCIAL` | Commercial | 4 | Gestion commerciale |
| `ACHETEUR` | Acheteur | 4 | Gestion achats |
| `MAGASINIER` | Magasinier | 4 | Gestion stocks |
| `RH` | Agent RH | 4 | Gestion RH |
| `CONSULTANT` | Consultant | 5 | Lecture seule |
| `AUDITEUR` | Auditeur | 5 | Accès audit, journal |

---

## 5. PERMISSIONS GRANULAIRES

### 5.1 Structure Permission
```
{module}.{ressource}.{action}
```

### 5.2 Exemples
```
treasury.forecast.create
treasury.forecast.read
treasury.forecast.validate
accounting.entry.create
accounting.entry.validate
hr.employee.read
hr.payroll.generate
sales.quote.create
sales.order.approve
```

### 5.3 Actions Standard
- `create` : Création
- `read` : Lecture
- `update` : Modification
- `delete` : Suppression
- `validate` : Validation/Approbation
- `export` : Export données
- `admin` : Administration

---

## 6. RÈGLES DE SÉPARATION DES POUVOIRS

| Règle | Description | Implémentation |
|-------|-------------|----------------|
| R1 | Celui qui crée ne valide pas | `creator_id != validator_id` |
| R2 | 4 yeux minimum sur critique | 2 validations distinctes |
| R3 | Pas d'auto-attribution de droits | Admin != bénéficiaire |
| R4 | Rotation obligatoire | Alerte si même validateur > N fois |
| R5 | Incompatibilité rôles | Certains rôles mutuellement exclusifs |

---

## 7. CONCLUSION BENCHMARK

**AZALS T0** atteint le niveau des solutions enterprise avec:
- ✅ 85% des fonctionnalités Keycloak/Auth0/Okta
- ✅ RBAC complet avec permissions granulaires
- ✅ Séparation des pouvoirs native (avantage différenciant)
- ✅ Multi-tenant sécurisé
- ✅ Audit trail intégré
- ✅ Intégration ERP native (avantage différenciant)

**Points à développer Phase 2**:
- SSO/SAML
- OAuth2/OIDC externe
- Fédération d'identités
