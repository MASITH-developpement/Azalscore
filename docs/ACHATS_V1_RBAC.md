# MODULE ACHATS V1 - MATRICE RBAC

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CONCEPTION UNIQUEMENT.**
>
> Les permissions decrites ci-dessous sont EXISTANTES dans le codebase.
> Ce document definit leur APPLICATION dans le cadre de ACHATS V1.
> AUCUNE modification RBAC n'est autorisee.

---

## 1. RESUME RBAC ACHATS V1

### 1.1 Permissions Reutilisees

ACHATS V1 reutilise les permissions existantes du module `procurement`:

| Permission Code | Description | Usage V1 |
|-----------------|-------------|----------|
| procurement.suppliers.create | Creer des fournisseurs | Creer fournisseurs |
| procurement.suppliers.read | Voir les fournisseurs | Consulter fournisseurs |
| procurement.suppliers.update | Modifier les fournisseurs | Modifier fournisseurs |
| procurement.orders.create | Creer des commandes | Creer commandes |
| procurement.orders.read | Voir les commandes | Consulter commandes |
| procurement.orders.update | Modifier les commandes | Modifier brouillons |
| procurement.orders.validate | Valider les commandes | Valider commandes |
| procurement.invoices.create | Creer des factures | Creer factures |
| procurement.invoices.read | Voir les factures | Consulter factures |
| procurement.invoices.update | Modifier les factures | Modifier brouillons |
| procurement.invoices.validate | Valider les factures | Valider factures |

### 1.2 Permissions Purchases Additionnelles

| Permission Code | Description | Usage V1 |
|-----------------|-------------|----------|
| purchases.view | Voir module achats | Acceder au module |
| purchases.create | Creer documents | Creer commandes/factures |
| purchases.edit | Modifier documents | Modifier brouillons |
| purchases.delete | Supprimer documents | Supprimer brouillons |
| purchases.validate | Valider documents | Passer en VALIDATED |
| purchases.export | Exporter CSV | Export listes |

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

### 2.2 Matrice Fournisseurs (SUPPLIER)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir liste fournisseurs | FULL | FULL | FULL | FULL | FULL |
| Voir detail fournisseur | FULL | FULL | FULL | FULL | FULL |
| Creer fournisseur | FULL | FULL | FULL | DENY | DENY |
| Modifier fournisseur | FULL | FULL | FULL | DENY | DENY |
| Bloquer fournisseur | FULL | FULL | DENY | DENY | DENY |
| Supprimer fournisseur | FULL | DENY | DENY | DENY | DENY |

### 2.3 Matrice Commandes (PURCHASE_ORDER)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir liste commandes | FULL | FULL | FULL | OWN | FULL |
| Voir detail commande | FULL | FULL | FULL | OWN | FULL |
| Creer commande | FULL | FULL | FULL | DENY | DENY |
| Modifier commande | FULL | FULL | FULL | DENY | DENY |
| Valider commande | FULL | FULL | FULL | DENY | DENY |
| Supprimer commande | FULL | LIMITED | DENY | DENY | DENY |
| Export CSV | FULL | FULL | DENY | DENY | DENY |

### 2.4 Matrice Factures (PURCHASE_INVOICE)

| Action | super_admin | admin | manager | user | readonly |
|--------|-------------|-------|---------|------|----------|
| Voir liste factures | FULL | FULL | FULL | OWN | FULL |
| Voir detail facture | FULL | FULL | FULL | OWN | FULL |
| Creer facture | FULL | FULL | FULL | DENY | DENY |
| Modifier facture | FULL | FULL | FULL | DENY | DENY |
| Valider facture | FULL | FULL | DENY | DENY | DENY |
| Supprimer facture | FULL | LIMITED | DENY | DENY | DENY |
| Creer depuis commande | FULL | FULL | FULL | DENY | DENY |
| Export CSV | FULL | FULL | DENY | DENY | DENY |

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

### 3.2 Regles de Restriction V1

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
| Valider commande | Passer DRAFT -> VALIDATED | admin, manager |
| Valider facture | Passer DRAFT -> VALIDATED | admin uniquement |
| Supprimer document | Supprimer un brouillon | admin uniquement |

### 4.2 Contraintes de Modification

```
Document status = DRAFT:
  - Modification autorisee selon role
  - Suppression autorisee pour admin

Document status = VALIDATED:
  - Aucune modification autorisee
  - Aucune suppression autorisee
  - Seule action possible: creation facture (depuis commande)
```

### 4.3 Audit Trail

| Action | Tracabilite | Champs Captures |
|--------|-------------|-----------------|
| Creation | created_by, created_at | user_id, timestamp |
| Modification | updated_at | timestamp |
| Validation | validated_by, validated_at | user_id, timestamp |
| Suppression | audit_log | user_id, timestamp, raison |

---

## 5. ROLES LEGACY -> ACHATS V1

### 5.1 Mapping Roles Existants

| Role Legacy | Role Standard | Droits ACHATS V1 |
|-------------|---------------|------------------|
| DIRIGEANT | admin | CRUD complet |
| ADMIN | admin | CRUD complet |
| DAF | manager | Lecture + Validation factures |
| RESPONSABLE_ACHATS | manager | CRUD limité |
| COMPTABLE | user | Lecture seule |
| ACHETEUR | user | Creation commandes |
| EMPLOYE | readonly | Lecture seule |
| CONSULTANT | readonly | Lecture seule |
| AUDITEUR | readonly | Lecture seule |

### 5.2 Permissions par Role Legacy

```python
# DIRIGEANT / ADMIN
ACHATS_V1_DIRIGEANT = [
    "procurement.suppliers.*",
    "procurement.orders.*",
    "procurement.invoices.*",
    "purchases.*",
]

# DAF / RESPONSABLE_ACHATS
ACHATS_V1_MANAGER = [
    "procurement.suppliers.read",
    "procurement.suppliers.update",
    "procurement.orders.read",
    "procurement.orders.create",
    "procurement.orders.validate",
    "procurement.invoices.read",
    "procurement.invoices.create",
    "procurement.invoices.validate",
    "purchases.view",
    "purchases.create",
    "purchases.validate",
]

# COMPTABLE
ACHATS_V1_COMPTABLE = [
    "procurement.suppliers.read",
    "procurement.orders.read",
    "procurement.invoices.read",
    "purchases.view",
]

# ACHETEUR
ACHATS_V1_ACHETEUR = [
    "procurement.suppliers.read",
    "procurement.orders.read",
    "procurement.orders.create",
    "procurement.orders.update",
    "purchases.view",
    "purchases.create",
]

# READONLY (EMPLOYE, CONSULTANT, AUDITEUR)
ACHATS_V1_READONLY = [
    "procurement.suppliers.read",
    "procurement.orders.read",
    "procurement.invoices.read",
    "purchases.view",
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
    Verification 3 niveaux pour ACHATS V1.
    """
    # Niveau 1: Authentification
    user = request.state.user
    if not user:
        raise HTTPException(401, "Non authentifie")

    # Niveau 2: Permission RBAC
    if not has_permission(user.role, Module.PURCHASES, action):
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
  requiredPermission="purchases.create"
  fallback={<AccessDenied />}
>
  <CreateOrderButton />
</CapabilityGuard>
```

### 7.2 Visibilite Conditionnelle

| Element UI | Permission Requise | Comportement |
|------------|-------------------|--------------|
| Bouton "+ Commande fournisseur" | purchases.create | Cache si deny |
| Bouton "+ Facture fournisseur" | purchases.create | Cache si deny |
| Bouton "Valider" | purchases.validate | Cache si deny |
| Bouton "Supprimer" | admin only | Cache si non admin |
| Bouton "Export CSV" | admin, manager | Cache si deny |
| Champs en edition | purchases.edit | Readonly si deny |

### 7.3 Navigation Filtree

```tsx
// Menu ACHATS V1 conditionnel
const AchatsMenu = () => {
  const { hasPermission } = useRBAC();

  return (
    <Menu>
      {hasPermission('purchases.view') && (
        <>
          <MenuItem href="/purchases/suppliers">Fournisseurs</MenuItem>
          <MenuItem href="/purchases/orders">Commandes</MenuItem>
          <MenuItem href="/purchases/invoices">Factures fournisseurs</MenuItem>
        </>
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
| admin_can_create_order | Admin cree une commande | 201 Created |
| admin_can_validate_order | Admin valide une commande | 200 OK |
| admin_can_validate_invoice | Admin valide une facture | 200 OK |
| manager_can_create_order | Manager cree une commande | 201 Created |
| manager_cannot_delete | Manager tente supprimer | 403 Forbidden |
| user_cannot_create | User tente creer | 403 Forbidden |
| readonly_cannot_modify | Readonly tente modifier | 403 Forbidden |
| cross_tenant_blocked | Acces autre tenant | 404 Not Found |

### 8.2 Tests E2E

| Test | Scenario | Resultat Attendu |
|------|----------|------------------|
| admin_full_workflow | Admin cree, modifie, valide | Success |
| manager_validate_order | Manager valide commande | Success |
| manager_cannot_delete | Manager tente supprimer | UI: bouton cache |
| user_read_own_only | User voit uniquement ses docs | Liste filtree |
| readonly_no_buttons | Readonly ne voit pas boutons action | UI filtree |
| cross_tenant_access | Tenant A accede tenant B | 404 Not Found |

---

## 9. CONFIGURATION

### 9.1 Parametres Tenant (Future)

```yaml
# Configuration RBAC personnalisable par tenant (V2+)
achats_v1:
  validation:
    order:
      roles: ["admin", "manager"]
    invoice:
      roles: ["admin"]  # Plus restrictif pour factures

  suppression:
    requires_reason: true
    allowed_roles: ["admin"]
```

### 9.2 Valeurs Par Defaut V1

```python
# Configuration ACHATS V1 fixe (pas de personnalisation)
ACHATS_V1_CONFIG = {
    "order_validation_roles": ["admin", "manager"],
    "invoice_validation_roles": ["admin"],
    "deletion_roles": ["admin"],
    "export_roles": ["admin", "manager"],
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
