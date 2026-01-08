# MODULE VENTES T0 - MATRICE RBAC

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CONCEPTION UNIQUEMENT.**
>
> Les permissions decrites ci-dessous sont EXISTANTES dans le codebase.
> Ce document definit leur APPLICATION dans le cadre de VENTES T0.
> AUCUNE modification RBAC n'est autorisee.

---

## 1. RESUME RBAC VENTES T0

### 1.1 Permissions Reutilisees

VENTES T0 reutilise les permissions existantes du module `commercial`:

| Permission Code | Description | Usage T0 |
|-----------------|-------------|----------|
| commercial.documents.create | Creer des documents commerciaux | Creer devis/factures |
| commercial.documents.read | Voir les documents commerciaux | Consulter devis/factures |
| commercial.documents.update | Modifier les documents | Modifier brouillons |
| commercial.documents.validate | Valider les documents | Valider devis/factures |
| commercial.customers.read | Voir les clients | Selectionner un client |

### 1.2 Permissions Sales Additionnelles

| Permission Code | Description | Usage T0 |
|-----------------|-------------|----------|
| sales.quote.create | Creer des devis | Creer un devis |
| sales.quote.read | Voir les devis | Consulter la liste |
| sales.quote.update | Modifier les devis | Modifier un brouillon |
| sales.quote.validate | Valider les devis | Passer en VALIDATED |
| sales.invoice.create | Creer des factures | Creer une facture |
| sales.invoice.read | Voir les factures | Consulter la liste |
| sales.invoice.validate | Valider les factures | Passer en VALIDATED |

---

## 2. MATRICE ROLE -> ACTION

### 2.1 Roles Standards

| Role | Niveau | Description |
|------|--------|-------------|
| super_admin | 0 | Acces total (invisible beta) |
| admin | 1 | Administrateur organisation |
| manager | 2 | Responsable d'equipe |
| user | 3 | Utilisateur standard |
| readonly | 4 | Consultation uniquement |

### 2.2 Matrice Devis (QUOTE)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir liste devis | FULL | FULL | FULL | OWN | FULL |
| Voir detail devis | FULL | FULL | FULL | OWN | FULL |
| Creer devis | FULL | FULL | FULL | DENY | DENY |
| Modifier devis | FULL | FULL | DENY | DENY | DENY |
| Valider devis | FULL | FULL | DENY | DENY | DENY |
| Supprimer devis | FULL | LIMITED | DENY | DENY | DENY |
| Export CSV | FULL | DENY | DENY | DENY | DENY |

### 2.3 Matrice Factures (INVOICE)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir liste factures | FULL | FULL | FULL | OWN | FULL |
| Voir detail facture | FULL | FULL | FULL | OWN | FULL |
| Creer facture | FULL | FULL | FULL | DENY | DENY |
| Modifier facture | FULL | FULL | DENY | DENY | DENY |
| Valider facture | FULL | FULL | DENY | DENY | DENY |
| Supprimer facture | FULL | LIMITED | DENY | DENY | DENY |
| Convertir devis | FULL | FULL | FULL | DENY | DENY |
| Export CSV | FULL | DENY | DENY | DENY | DENY |

---

## 3. RESTRICTIONS D'ACCES

### 3.1 Types de Restriction

| Code | Description | Application |
|------|-------------|-------------|
| FULL | Acces complet | Toutes les donnees du tenant |
| LIMITED | Acces limite | Avec contrainte supplementaire |
| OWN | Propres donnees | Documents crees par l'utilisateur |
| TEAM | Equipe | Documents de l'equipe (future) |
| DENY | Refuse | Aucun acces |

### 3.2 Regles de Restriction T0

```python
# Pseudo-code des regles
def can_access_document(user, document):
    # 1. Verification tenant (OBLIGATOIRE)
    if user.tenant_id != document.tenant_id:
        return False  # DENY

    # 2. Super admin / admin -> FULL
    if user.role in ['super_admin', 'admin']:
        return True

    # 3. Manager -> FULL lecture, LIMITED modification
    if user.role == 'manager':
        return True  # Lecture OK

    # 4. User -> OWN (ses documents uniquement)
    if user.role == 'user':
        return document.created_by == user.id

    # 5. Readonly -> lecture seule, pas de modification
    if user.role == 'readonly':
        return action == 'read'

    return False  # deny-by-default
```

---

## 4. REGLES METIER RBAC

### 4.1 Validation Documents

| Regle | Description | Roles Autorises |
|-------|-------------|-----------------|
| Valider devis | Passer DRAFT -> VALIDATED | admin, manager (configurable) |
| Valider facture | Passer DRAFT -> VALIDATED | admin, manager (configurable) |
| Supprimer document | Supprimer un brouillon | admin uniquement |

### 4.2 Contraintes de Modification

```
Document status = DRAFT:
  - Modification autorisee selon role
  - Suppression autorisee pour admin

Document status = VALIDATED:
  - Aucune modification autorisee
  - Aucune suppression autorisee
  - Seule action possible: conversion (devis -> facture)
```

### 4.3 Audit Trail

| Action | Tracabilite | Champs Captures |
|--------|-------------|-----------------|
| Creation | created_by, created_at | user_id, timestamp |
| Modification | (updated_at) | timestamp |
| Validation | validated_by, validated_at | user_id, timestamp |
| Suppression | audit_log | user_id, timestamp, raison |

---

## 5. ROLES LEGACY -> VENTES T0

### 5.1 Mapping Roles Existants

| Role Legacy | Role Standard | Droits VENTES T0 |
|-------------|---------------|------------------|
| DIRIGEANT | admin | CRUD complet |
| ADMIN | admin | CRUD complet |
| DAF | manager | Lecture + Validation |
| RESPONSABLE_COMMERCIAL | manager | CRUD limité |
| COMPTABLE | user | Lecture seule |
| COMMERCIAL | user | Creation devis |
| EMPLOYE | readonly | Lecture seule |
| CONSULTANT | readonly | Lecture seule |
| AUDITEUR | readonly | Lecture seule |

### 5.2 Permissions par Role Legacy

```python
# DIRIGEANT / ADMIN
VENTES_T0_DIRIGEANT = [
    "commercial.documents.create",
    "commercial.documents.read",
    "commercial.documents.update",
    "commercial.documents.validate",
    "sales.quote.*",
    "sales.invoice.*",
]

# DAF / RESPONSABLE_COMMERCIAL
VENTES_T0_MANAGER = [
    "commercial.documents.read",
    "commercial.documents.validate",
    "sales.quote.read",
    "sales.quote.create",
    "sales.invoice.read",
    "sales.invoice.validate",
]

# COMPTABLE
VENTES_T0_COMPTABLE = [
    "commercial.documents.read",
    "sales.invoice.read",
]

# COMMERCIAL
VENTES_T0_COMMERCIAL = [
    "sales.quote.create",
    "sales.quote.read",
    "sales.quote.update",
    "commercial.customers.read",
]

# READONLY (EMPLOYE, CONSULTANT, AUDITEUR)
VENTES_T0_READONLY = [
    "commercial.documents.read",
    "sales.quote.read",
    "sales.invoice.read",
]
```

---

## 6. SECURITE TRANSVERSALE

### 6.1 Regles Obligatoires

| Regle | Description | Enforcement |
|-------|-------------|-------------|
| Isolation tenant | Pas d'acces cross-tenant | Filter SQL + Middleware |
| deny-by-default | Tout acces non explicite refuse | RBAC Matrix |
| Audit obligatoire | Toute action critique loggee | Decorator |

### 6.2 Verification Multi-Niveau

```python
def verify_access(request, action, document_id=None):
    """
    Verification 3 niveaux pour VENTES T0.
    """
    # Niveau 1: Authentification
    user = request.state.user
    if not user:
        raise HTTPException(401, "Non authentifie")

    # Niveau 2: Permission RBAC
    if not has_permission(user.role, Module.BILLING, action):
        raise HTTPException(403, "Permission refusee")

    # Niveau 3: Tenant isolation
    if document_id:
        document = get_document(document_id)
        if document.tenant_id != user.tenant_id:
            # Log tentative acces inter-tenant
            log_security_event(
                event="CROSS_TENANT_ACCESS_ATTEMPT",
                user_id=user.id,
                target_tenant=document.tenant_id
            )
            raise HTTPException(404, "Document non trouve")

    return True
```

### 6.3 Actions Critiques Loggees

| Action | Niveau Log | Donnees Capturees |
|--------|------------|-------------------|
| Validation document | INFO | user, document, timestamp |
| Suppression document | WARNING | user, document, raison |
| Tentative acces refuse | WARNING | user, action, ressource |
| Acces inter-tenant | CRITICAL | user, tenant_source, tenant_cible |

---

## 7. INTERFACE FRONTEND

### 7.1 CapabilityGuard

```tsx
// Composant protection frontend
<CapabilityGuard
  requiredPermission="commercial.documents.create"
  fallback={<AccessDenied />}
>
  <CreateQuoteButton />
</CapabilityGuard>
```

### 7.2 Visibilite Conditionnelle

| Element UI | Permission Requise | Comportement |
|------------|-------------------|--------------|
| Bouton "Nouveau Devis" | sales.quote.create | Cache si deny |
| Bouton "Valider" | commercial.documents.validate | Cache si deny |
| Bouton "Supprimer" | admin only | Cache si non admin |
| Bouton "Export CSV" | admin only | Cache si non admin |
| Champs en edition | commercial.documents.update | Readonly si deny |

### 7.3 Navigation Filtree

```tsx
// Menu VENTES T0 conditionnel
const VentesMenu = () => {
  const { hasPermission } = useRBAC();

  return (
    <Menu>
      {hasPermission('sales.quote.read') && (
        <MenuItem href="/invoicing/quotes">Devis</MenuItem>
      )}
      {hasPermission('sales.invoice.read') && (
        <MenuItem href="/invoicing/invoices">Factures</MenuItem>
      )}
    </Menu>
  );
};
```

---

## 8. TESTS RBAC REQUIS

### 8.1 Tests Unitaires

| Test | Description | Resultat Attendu |
|------|-------------|------------------|
| admin_can_create_quote | Admin cree un devis | 201 Created |
| admin_can_validate_quote | Admin valide un devis | 200 OK |
| user_cannot_create_quote | User tente creer devis | 403 Forbidden |
| readonly_cannot_modify | Readonly tente modifier | 403 Forbidden |
| cross_tenant_blocked | Acces autre tenant | 404 Not Found |

### 8.2 Tests E2E

| Test | Scenario | Resultat Attendu |
|------|----------|------------------|
| admin_full_workflow | Admin cree, modifie, valide | Success |
| manager_validate_only | Manager valide devis existant | Success |
| user_read_own_only | User voit uniquement ses docs | Liste filtree |
| readonly_no_buttons | Readonly ne voit pas boutons action | UI filtree |

---

## 9. CONFIGURATION

### 9.1 Parametres Tenant (Future)

```yaml
# Configuration RBAC personnalisable par tenant (T1+)
ventes_t0:
  validation:
    quote:
      roles: ["admin", "manager"]
    invoice:
      roles: ["admin"]  # Plus restrictif pour factures

  suppression:
    requires_reason: true
    allowed_roles: ["admin"]
```

### 9.2 Valeurs Par Defaut T0

```python
# Configuration VENTES T0 fixe (pas de personnalisation)
VENTES_T0_CONFIG = {
    "validation_roles": ["admin", "manager"],
    "deletion_roles": ["admin"],
    "export_roles": ["admin"],
    "default_tva_rate": 20.0,
}
```

---

## 10. RISQUES RBAC

### 10.1 Risques Identifies

| Risque | Probabilite | Impact | Mitigation |
|--------|-------------|--------|------------|
| Escalade privilege | Faible | CRITIQUE | Tests unitaires exhaustifs |
| Fuite inter-tenant | Faible | CRITIQUE | Triple verification tenant |
| Bypass validation | Moyen | ELEVE | Verification backend obligatoire |
| UI desynchronisee | Moyen | MOYEN | Refresh permissions auto |

### 10.2 Controles de Securite

| Controle | Frequence | Responsable |
|----------|-----------|-------------|
| Audit RBAC matrix | Mensuel | Security Lead |
| Revue acces admin | Mensuel | Tenant Admin |
| Tests penetration | Trimestriel | Security Team |
| Logs access denied | Quotidien (auto) | Monitoring |

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
