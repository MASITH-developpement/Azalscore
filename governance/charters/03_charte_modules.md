# CHARTE MODULES AZALSCORE
## Gouvernance des Composants Métier

**Version:** 1.0.0
**Statut:** DOCUMENT NORMATIF
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE
**Référence:** AZALS-GOV-03-v1.0.0

---

## 1. OBJECTIF

Cette charte définit ce qu'est un module AZALSCORE, ses règles de conception, son cycle de vie, et ses obligations de gouvernance.

---

## 2. PÉRIMÈTRE

### 2.1 Définition d'un Module
Un module AZALSCORE est une **unité fonctionnelle indépendante** qui :
- Répond à un besoin métier spécifique
- Peut être installé ou désinstallé sans impact sur le système
- Dépend du Core mais jamais d'autres modules
- Possède sa propre charte de gouvernance

### 2.2 Liste des Modules Actuels

```
app/modules/
├── ai_assistant/     # IA et prédictions
├── audit/            # Audit et benchmark
├── bi/               # Business Intelligence
├── broadcast/        # Diffusion multi-canal
├── commercial/       # Ventes, devis, commandes
├── compliance/       # Conformité réglementaire
├── country_packs/    # Localisations (France, etc.)
├── ecommerce/        # Boutique en ligne
├── field_service/    # Interventions terrain
├── finance/          # Comptabilité, écritures
├── helpdesk/         # Support client
├── hr/               # Ressources humaines
├── iam/              # Gestion identités/accès
├── inventory/        # Stock et articles
├── maintenance/      # Maintenance équipements
├── mobile/           # Backend mobile
├── pos/              # Point de vente
├── procurement/      # Achats fournisseurs
├── production/       # Fabrication
├── projects/         # Gestion de projets
├── qc/               # Contrôle qualité
├── quality/          # Qualité processus
├── stripe_integration/ # Paiements Stripe
├── subscriptions/    # Abonnements SaaS
├── tenants/          # Gestion multi-tenant
├── triggers/         # Alertes automatisées
├── web/              # Contenu web
└── website/          # Site web public
```

---

## 3. PRINCIPES FONDAMENTAUX

### 3.1 Indépendance

```
RÈGLE: Un module est une île.

- Chaque module fonctionne de manière autonome
- La suppression d'un module ne casse pas le système
- Les modules ne s'appellent pas directement entre eux
```

### 3.2 Dépendance au Core Uniquement

```
RÈGLE: Un module ne dépend QUE du Core.

Autorisé:
✅ from app.core.database import get_db
✅ from app.core.dependencies import get_current_user
✅ from app.core.models import TenantMixin

Interdit:
❌ from app.modules.finance import InvoiceService
❌ from app.modules.hr.models import Employee
```

### 3.3 Communication Inter-Modules

```
RÈGLE: Les modules communiquent via événements ou API, jamais directement.

# ✅ Correct - Événement
event_bus.publish("invoice.created", invoice_data)

# ✅ Correct - Appel API interne
response = await http_client.post("/api/finance/invoices", data)

# ❌ Interdit - Import direct
from app.modules.finance.service import create_invoice
```

---

## 4. STRUCTURE OBLIGATOIRE

### 4.1 Fichiers Requis

```
app/modules/{module_name}/
├── __init__.py       # Exports publics [OBLIGATOIRE]
├── models.py         # Modèles SQLAlchemy [OBLIGATOIRE]
├── schemas.py        # Schémas Pydantic [OBLIGATOIRE]
├── service.py        # Logique métier [OBLIGATOIRE]
├── router.py         # Endpoints API [OBLIGATOIRE]
└── GOVERNANCE.md     # Charte module [OBLIGATOIRE]
```

### 4.2 Fichiers Optionnels

```
├── constants.py      # Constantes du module
├── exceptions.py     # Exceptions spécifiques
├── events.py         # Événements publiés/consommés
├── tasks.py          # Tâches asynchrones
├── utils.py          # Utilitaires internes
└── tests/            # Tests du module
```

### 4.3 Exemple de Structure

```python
# __init__.py
from .router import router
from .service import InvoiceService
from .models import Invoice, InvoiceLine

__all__ = ["router", "InvoiceService", "Invoice", "InvoiceLine"]
```

---

## 5. CHARTE MODULE OBLIGATOIRE (GOVERNANCE.md)

Chaque module DOIT avoir un fichier `GOVERNANCE.md` suivant le template 09.

### 5.1 Contenu Minimum

```markdown
# GOVERNANCE - Module {NomModule}

## Identité
- Nom: {nom}
- Version: {version}
- Responsable: {équipe/personne}

## Objectif
{description en 2-3 phrases}

## Périmètre
### Inclus
- {fonctionnalité 1}
- {fonctionnalité 2}

### Exclus
- {ce que le module ne fait PAS}

## Données
- {liste des entités gérées}

## APIs Exposées
- {liste des endpoints}

## Dépendances
### Autorisées
- Core uniquement

### Interdites
- Tout autre module

## Sécurité
- {règles spécifiques}

## IA
- Autorisée: OUI/NON
- Rôle: {description}
- Limites: {restrictions}

## Désinstallation
- Impact: {description}
- Données: {ce qui advient des données}
```

---

## 6. CYCLE DE VIE D'UN MODULE

### 6.1 États

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  DRAFT   │ ──▶ │  ACTIVE  │ ──▶ │DEPRECATED│
└──────────┘     └──────────┘     └──────────┘
                                        │
                                        ▼
                                  ┌──────────┐
                                  │ REMOVED  │
                                  └──────────┘
```

### 6.2 Transitions

| De | Vers | Condition |
|----|------|-----------|
| DRAFT | ACTIVE | Tests passants + Review + GOVERNANCE.md |
| ACTIVE | DEPRECATED | Notice 6 mois + Alternative documentée |
| DEPRECATED | REMOVED | Migration terminée + Données archivées |

### 6.3 Installation

```bash
# Un module est installé en l'ajoutant à app/main.py
from app.modules.{module}.router import router as module_router
app.include_router(module_router)
```

### 6.4 Désinstallation

```bash
# 1. Retirer du main.py
# 2. Migrer les données si nécessaire
# 3. Supprimer les tables (optionnel)
# 4. Retirer le dossier du module
```

---

## 7. RÈGLES DE DÉVELOPPEMENT

### 7.1 Isolation des Données

```python
# ✅ Correct - Toujours filtrer par tenant_id
def get_invoices(self, tenant_id: str) -> List[Invoice]:
    return self.db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id
    ).all()

# ❌ Interdit - Accès cross-tenant
def get_all_invoices(self) -> List[Invoice]:
    return self.db.query(Invoice).all()
```

### 7.2 Pas de Logique Core

```python
# ❌ Interdit - Gérer l'auth dans un module
def authenticate_user(email, password):
    # Cette logique appartient au Core !
    pass

# ✅ Correct - Utiliser le Core
from app.core.dependencies import get_current_user
```

### 7.3 Événements Standards

```python
# Événements qu'un module peut publier
MODULE_EVENTS = {
    "created": "{module}.{entity}.created",
    "updated": "{module}.{entity}.updated",
    "deleted": "{module}.{entity}.deleted",
}

# Exemple
event_bus.publish("finance.invoice.created", {
    "tenant_id": tenant_id,
    "invoice_id": invoice.id,
    "amount": invoice.total
})
```

---

## 8. VERSIONING

### 8.1 Version Sémantique

```
MODULE-X.Y.Z

X = Breaking change (incompatible)
Y = Nouvelle fonctionnalité (compatible)
Z = Bug fix (compatible)
```

### 8.2 Compatibilité

| Type de changement | Action requise |
|-------------------|----------------|
| Nouveau endpoint | Mineure (Y) |
| Modification signature | Majeure (X) |
| Correction bug | Patch (Z) |
| Suppression endpoint | Majeure (X) + dépréciation |

---

## 9. INTERDICTIONS

### 9.1 Interdictions Absolues

- ❌ Importer depuis un autre module
- ❌ Modifier le Core
- ❌ Accéder aux données d'autres modules directement
- ❌ Créer des dépendances circulaires
- ❌ Publier sans GOVERNANCE.md

### 9.2 Patterns Interdits

```python
# ❌ Interdit - Dépendance inter-module
from app.modules.hr.models import Employee

# ❌ Interdit - Requête cross-module
employees = db.query(Employee).filter(...)

# ❌ Interdit - Table partagée non Core
class SharedTable(Base):  # Doit être dans Core
    pass
```

---

## 10. TESTS

### 10.1 Couverture Minimale

| Composant | Minimum |
|-----------|---------|
| Service | 85% |
| Router | 80% |
| Models | 70% |

### 10.2 Tests Obligatoires

```python
# Chaque module doit tester :
def test_crud_operations():
    """Create, Read, Update, Delete"""

def test_tenant_isolation():
    """Isolation entre tenants"""

def test_permissions():
    """Vérification des droits"""

def test_validation():
    """Validation des entrées"""
```

---

## 11. DOCUMENTATION

### 11.1 OpenAPI

Tous les endpoints documentés avec :
- Summary
- Description
- Request/Response schemas
- Codes d'erreur

### 11.2 GOVERNANCE.md

Fichier obligatoire à jour avec :
- Objectif du module
- Périmètre exact
- APIs exposées
- Règles spécifiques

---

## 12. CONSÉQUENCES DU NON-RESPECT

| Violation | Conséquence |
|-----------|-------------|
| Module sans GOVERNANCE.md | Refus de merge |
| Import inter-module | Revert immédiat |
| Tests insuffisants | Blocage déploiement |
| Accès cross-tenant | Incident sécurité |

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-03-v1.0.0*
