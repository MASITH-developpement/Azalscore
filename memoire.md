# AZALSCORE - Memoire de Session

## Derniere mise a jour: 2026-02-14

---

## Problemes Resolus

### 1. Admin Panel - Acces Refuse (401/403) [2026-02-08]

**Probleme:** L'utilisateur `contact@masith.fr` avec role DIRIGEANT ne pouvait pas acceder a l'administration.

**Causes identifiees:**
- `CoreAuthMiddleware` ne definissait pas `request.state.user` (seulement `saas_context`)
- `RBACMiddleware` verifiait `request.state.user` pour l'authentification
- L'endpoint `/v1/tenants` exigeait `require_super_admin()`
- Le role SUPERADMIN n'etait pas dans `role_capabilities` pour `/capabilities`

**Solutions appliquees:**
1. Modifie `/app/core/core_auth_middleware.py` - Ajout du chargement de l'objet User dans `request.state.user`
2. Modifie `/app/modules/tenants/router.py` - `list_tenants()` permet aux non-superadmin de voir leur propre tenant
3. Modifie `/app/api/auth.py` - Ajout de SUPERADMIN dans `role_capabilities`
4. Mis a jour le role de `contact@masith.fr` en SUPERADMIN dans la base

### 2. Erreur 422 sur IAM Endpoints [2026-02-08]

**Probleme:** Les endpoints `/v1/iam/users/{user_id}` retournaient 422 car ils attendaient `int` au lieu de `UUID`.

**Solution:** Modifie `/app/modules/iam/router.py`:
- Change `user_id: int` en `user_id: UUID`
- Change `role_id: int` en `role_id: UUID`
- Change `group_id: int` en `group_id: UUID`
- Ajoute `from uuid import UUID` en import

### 3. Erreur 500 sur /v1/tenants [2026-02-08]

**Probleme:** `ResponseValidationError` - Le schema attendait `id: int` mais recevait UUID.

**Solution:** Modifie `/app/modules/tenants/schemas.py`:
- Change `id: int` en `id: UUID` dans `TenantResponse` et `TenantListResponse`
- Ajoute `from uuid import UUID` en import
- Ajoute validator pour convertir les enums status/plan en string

### 4. Approbation Code Promo - Echec [2026-02-08]

**Probleme:** L'approbation des codes promo echouait avec plusieurs erreurs:
- `actor_id` NOT NULL dans `tenant_events`
- Donnees orphelines du tenant "test" dans plusieurs tables

**Solutions:**
1. Modifie `/app/modules/tenants/service_trial.py` - Passe `actor_email` au TenantService
2. Execute `ALTER TABLE tenant_events ALTER COLUMN actor_id DROP NOT NULL;`
3. Script de nettoyage des donnees orphelines pour toutes les tables avec tenant_id

### 5. Pages Admin affichent "Aucune donnee disponible" [2026-02-09]

**Probleme:** Toutes les pages admin (Utilisateurs, Roles, Tenants, Numerotation, Audit, Sauvegardes, Permissions, Tableau de bord) affichaient "Aucune donnee disponible" malgre des donnees presentes en base.

**Cause:** Le frontend s'attendait a une reponse enveloppee `{ data: [...] }` mais l'API retournait directement les donnees `[...]`. Le code `.then(r => r.data)` retournait `undefined`.

**Solutions appliquees:**
1. Modifie `/frontend/src/modules/admin/index.tsx` - Correction des hooks:
   - `useUsers` - gere les deux formats de reponse
   - `useUser` - gere les deux formats de reponse
   - `useRoles` - gere les deux formats de reponse
   - `useTenants` - gere les deux formats de reponse
   - `useAuditLogs` - gere les deux formats de reponse
   - `useBackupConfigs` - gere les deux formats de reponse
   - `useAdminDashboard` - gere les deux formats de reponse
   - `useCreateUser`, `useUpdateUserStatus`, `useRunBackup` - mutations corrigees

2. Modifie `/frontend/src/modules/admin/components/SequencesView.tsx` - Correction des hooks:
   - `useSequences` - gere les deux formats de reponse
   - `useUpdateSequence`, `useResetSequence`, `usePreviewSequence` - corrigees

3. Modifie `/frontend/src/ui-engine/simple/PermissionsManager.tsx` - Correction des hooks:
   - Chargement des utilisateurs et permissions

4. Modifie `/frontend/src/core/capabilities/index.tsx` - Parsing robuste:
   - Gere format `{ capabilities: [...] }`
   - Gere format `{ data: { capabilities: [...] } }`
   - Gere format tableau direct
   - Ajoute logging pour debug

### 6. Nouvel endpoint Admin Dashboard [2026-02-09]

**Probleme:** Le frontend appelait `/v1/cockpit/dashboard` qui retourne des KPIs business, pas les stats admin.

**Solution:** Cree `/app/api/admin.py` avec endpoint `/v1/admin/dashboard` retournant:
- `total_users`, `active_users` (depuis `iam_users`)
- `total_tenants`, `active_tenants` (depuis `tenants`)
- `total_roles` (depuis `iam_roles`)
- `storage_used_gb`, `api_calls_today`, `errors_today`

### 7. Format reponse /v1/auth/capabilities [2026-02-09]

**Probleme:** L'API retournait `{ data: { capabilities: [...] } }` mais le frontend attendait `{ capabilities: [...] }`.

**Solution:** Modifie `/app/api/auth.py` ligne 1032-1036:
```python
# Avant
return {"data": {"capabilities": capabilities, "role": role_name}}

# Apres
return {"capabilities": capabilities, "role": role_name}
```

### 8. Container Docker avec fichier obsolete [2026-02-09]

**Probleme:** Le container avait une ancienne version de `auth.py` sans `SUPERADMIN` dans `role_capabilities`. L'utilisateur recevait seulement 1 capability (`cockpit.view`).

**Solution:** Copie manuelle du fichier mis a jour:
```bash
docker cp /home/ubuntu/azalscore/app/api/auth.py azals_api:/app/app/api/auth.py
docker restart azals_api
```

**Note importante:** Apres modification de fichiers Python, toujours verifier que le container a la bonne version:
```bash
docker exec azals_api grep "SUPERADMIN" /app/app/api/auth.py
```

### 9. Permissions IAM et roles admin [2026-02-09]

**Probleme:** Les endpoints IAM (`/v1/iam/roles`, `/v1/iam/users`) retournaient 403 meme pour SUPERADMIN car le decorateur `@require_permission` verifiait les permissions dans la table `iam_role_permissions` au lieu des capabilities.

**Solution:** Modifie `/app/modules/iam/decorators.py`:
- Ajoute bypass pour les roles admin (SUPERADMIN, SUPER_ADMIN, DIRIGEANT, ADMIN)
- Verifie `current_user.role` avant d'appeler `service.check_permission()`

### 10. require_super_admin accepte tous les roles admin [2026-02-09]

**Probleme:** `require_super_admin()` dans `/app/modules/tenants/router.py` n'acceptait que `SUPER_ADMIN` mais pas `SUPERADMIN`.

**Solution:** Modifie la fonction pour accepter `{'SUPERADMIN', 'SUPER_ADMIN', 'DIRIGEANT', 'ADMIN'}`.

### 11. Schema TenantListResponse id: UUID [2026-02-09]

**Probleme:** Erreur 500 sur `/v1/tenants` car `TenantListResponse.id` etait `int` mais recevait UUID.

**Solution:** Change `id: int` en `id: UUID` dans `/app/modules/tenants/schemas.py` (toutes les classes Response).

### 12. Format reponse roles avec items [2026-02-09]

**Probleme:** L'API roles retourne `{"items": [...], "total": 1}` mais le frontend attendait un tableau direct.

**Solution:** Modifie `useRoles` dans `/frontend/src/modules/admin/index.tsx` pour gerer les formats:
- Tableau direct `[...]`
- Objet avec data `{ data: [...] }`
- Objet avec items `{ items: [...] }`

### 13. Actions Tenant dans Admin [2026-02-09]

**Ajout:** Fonctionnalites de gestion des tenants dans `/frontend/src/modules/admin/index.tsx`:
- Bouton Modifier (modal avec nom, plan, statut)
- Bouton Suspendre (pour tenants actifs)
- Bouton Activer (pour tenants suspendus)
- Bouton Annuler definitivement (dans modal)

Nouveaux hooks: `useSuspendTenant`, `useActivateTenant`, `useCancelTenant`, `useUpdateTenant`

### 14. Gestion des Roles dans Admin [2026-02-09]

**Ajout:** Fonctionnalites de gestion des roles dans `/frontend/src/modules/admin/index.tsx`:
- Bouton "Nouveau role" avec modal de creation
- Bouton Modifier (icone crayon) pour chaque role
- Bouton Supprimer (icone poubelle) pour les roles non-systeme sans utilisateurs
- Validation: impossible de supprimer un role systeme ou avec des utilisateurs assignes

**Champs du formulaire role:**
- Code (majuscules, chiffres, _ uniquement) - creation uniquement
- Nom
- Description (textarea)
- Niveau (0-10, 0 = plus eleve)
- Role parent (creation uniquement)
- Statut Actif/Inactif (modification uniquement)
- Max utilisateurs (optionnel)
- Requiert approbation (checkbox)
- Permissions (selection par module avec cases a cocher)

**Composant separe `RoleFormModal`** pour eviter les problemes de focus lors de la saisie.

Nouveaux hooks: `useCreateRole`, `useUpdateRole`, `useDeleteRole`, `usePermissions`

### 15. Colonne "Createur" dans Roles [2026-02-09]

**Modification:** Remplacement de la colonne "Systeme" (Oui/Non) par "Createur":
- Affiche "Systeme" (badge orange) pour `is_system = true`
- Affiche le nom de l'utilisateur qui a cree le role pour `is_system = false`

**Backend:**
- Modifie `/app/modules/iam/schemas.py` - Ajout `created_by_name: str | None` dans `RoleResponse`
- Modifie `/app/modules/iam/router.py` - Endpoints `list_roles` et `get_role` recuperent le nom du createur depuis `iam_users`

**Frontend:**
- Modifie `/frontend/src/modules/admin/types.ts` - Ajout `created_by_name` dans interface `Role`
- Modifie `/frontend/src/modules/admin/index.tsx` - Colonne "Createur" avec logique d'affichage

### 16. Fix erreur "Cannot read properties of undefined" [2026-02-09]

**Probleme:** Erreur sur la page detail utilisateur quand `USER_STATUS_CONFIG[user.status]` retournait `undefined`.

**Solution:** Ajout d'un fallback dans `/frontend/src/modules/admin/index.tsx`:
```typescript
const statusConfig = USER_STATUS_CONFIG[user.status] || { label: user.status || 'Inconnu', color: 'gray' as const };
```

### 17. Gestion des Acces Modules par Utilisateur [2026-02-09]

**Fonctionnalite:** Interface complete pour configurer les permissions de chaque utilisateur par module et fonctionnalite.

**Backend:**
- Ajout de `CAPABILITIES_BY_MODULE` dans `/app/modules/iam/router.py` - dictionnaire de tous les modules avec leurs capabilities
- Nouvel endpoint `GET /v1/iam/capabilities/modules` - retourne toutes les capabilities groupees par module

**Frontend:**
- Nouvel onglet "Acces Modules" dans Administration (remplace l'ancien "Permissions")
- Composant `UserPermissionsModal` - modal de gestion des permissions par utilisateur
- Composant `UsersPermissionsView` - liste des utilisateurs avec bouton "Gerer" pour chaque
- Hooks: `useCapabilitiesByModule`, `useUserPermissions`, `useUpdateUserPermissions`

**Fonctionnalites de l'interface:**
- Recherche dans les modules/capabilities
- Deplier/Replier tous les modules
- Selectionner/Deselectionner toutes les permissions
- Selection par module entier (case a cocher indeterminee si partiel)
- Compteur de permissions selectionnees
- Sauvegarde dans la table `iam_user_permissions`

**Modules disponibles (27 modules, ~120 capabilities):**
cockpit, partners, contacts, invoicing, treasury, accounting, purchases, projects, hr, interventions, inventory, ecommerce, crm, production, quality, maintenance, pos, subscriptions, helpdesk, bi, compliance, web, marketplace, payments, mobile, admin, iam

### 18. Fix Endpoint capabilities/modules - Erreur 500 [2026-02-09]

**Probleme:** L'endpoint `GET /v1/iam/capabilities/modules` retournait une erreur 500:
```
Erreur configuration: service et current_user requis pour verification permissions
```

**Cause:** Le decorateur `@require_permission()` dans `/app/modules/iam/decorators.py` exige que les parametres `service` ET `current_user` soient presents dans la fonction decoree. L'endpoint n'avait que `current_user`.

**Solution:** Ajout du parametre `service` dans l'endpoint:
```python
@router.get("/capabilities/modules")
@require_permission("iam.permission.read")
async def get_capabilities_by_module(
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)  # AJOUTE
):
    return CAPABILITIES_BY_MODULE
```

**Note importante:** Tout endpoint utilisant `@require_permission()` DOIT avoir les deux parametres:
- `current_user: User = Depends(get_current_user)`
- `service: IAMService = Depends(get_service)`

### 19. Module Enrichissement - Autocomplete Entreprise [2026-02-10]

**Fonctionnalite:** Autocomplete sur le nom d'entreprise dans le formulaire fournisseur qui remplit automatiquement les champs (nom, SIRET, adresse, ville, code postal).

**Backend:**
- `/app/modules/enrichment/schemas.py` - `suggestions: list[dict[str, Any]]` au lieu de `list[AddressSuggestion]` pour preserver les champs entreprise
- `/app/modules/enrichment/service.py` - Appel API `recherche-entreprises.api.gouv.fr`

**Frontend:**
- `/frontend/src/modules/enrichment/components/CompanyAutocomplete.tsx` - Composant autocomplete entreprise
- `/frontend/src/modules/enrichment/types.ts` - Ajout champ `address` dans `EnrichedContactFields`
- `/frontend/src/modules/purchases/index.tsx` - Integration CompanyAutocomplete + handleCompanySelect

### 20. Code Fournisseur Auto-genere [2026-02-10]

**Probleme:** Le formulaire fournisseur exigeait un code (champ `required`) mais le backend le genere automatiquement.

**Solutions:**
1. Backend `/app/modules/purchases/schemas.py`:
   ```python
   code: Optional[str] = Field(default=None, max_length=50)  # Auto-genere si non fourni
   ```

2. Frontend `/frontend/src/modules/purchases/index.tsx`:
   - Champ code: `required` supprime, placeholder "Genere automatiquement"
   - `SUPPLIER_CREATE_FIELDS`: `required: false` pour code

### 21. Fix Hooks Purchases - Format Reponse API [2026-02-10]

**Probleme:** Les hooks `useSuppliers`, `useSupplier`, etc. faisaient `response.data` mais l'API retourne directement les donnees.

**Solution:** Pattern robuste dans tous les hooks:
```typescript
const data = (response as any)?.data ?? response ?? { items: [], total: 0, page: 1, pages: 0 };
```

**Hooks corriges:**
- `useSuppliers`, `useSupplier`, `useSuppliersLookup`
- `useCreateSupplier`, `useUpdateSupplier`

### 22. ClientFormPage avec Enrichissement [2026-02-10]

**Fonctionnalite:** Formulaire de creation/edition client avec auto-enrichissement comme les fournisseurs.

**Frontend:**
- `/frontend/src/modules/partners/index.tsx`:
  - Ajout `ClientFormPage` - page formulaire complete
  - Routes `/clients/new` et `/clients/:id/edit`
  - Integration `CompanyAutocomplete` pour recherche par nom d'entreprise
  - Integration `AddressAutocomplete` pour autocomplete adresse
  - Champs auto-remplis: nom, SIRET, adresse, code postal, ville
  - Code client auto-genere par le backend

**Backend:** Deja configure avec `CustomerCreateAuto` qui a `code: Optional[str]`

---

### 22. Analyse de Risque Entreprise - Pappers [2026-02-10]

**Probleme:** Besoin d'analyser le risque financier des clients/fournisseurs.

**Solution:** Implementation du provider Pappers pour l'analyse de risque.

**Backend:**
- `/app/modules/enrichment/providers/pappers.py` - Provider Pappers avec:
  - Lookup par SIREN/SIRET
  - Calcul score de risque (0-100)
  - Interpretation cotation Banque de France
  - Detection procedures collectives
  - Analyse de facteurs (anciennete, capital, etc.)
- `/app/modules/enrichment/models.py` - Ajout `LookupType.RISK`
- `/app/modules/enrichment/service.py` - Integration PappersProvider
- `/app/modules/enrichment/router.py` - Endpoint `GET /v1/enrichment/risk/{identifier}`
- `/app/modules/iam/router.py` - Ajout capabilities module enrichment:
  - `enrichment.risk_analysis` (donnees confidentielles)

**Frontend:**
- `/frontend/src/modules/enrichment/hooks/useRiskAnalysis.ts` - Hook React Query
- `/frontend/src/modules/enrichment/components/RiskAnalysis.tsx` - Composant d'affichage:
  - Score gauge (0-100)
  - Niveau de risque (low/medium/elevated/high)
  - Cotation Banque de France
  - Alertes et recommandations
  - Facteurs d'analyse detailles
- `/frontend/src/modules/enrichment/types.ts` - Types RiskAnalysis, RiskFactor
- `/frontend/src/modules/enrichment/api.ts` - Fonction `analyzeRisk()`

**Securite:**
- Endpoint protege par capability `enrichment.risk_analysis`
- Donnees confidentielles - acces restreint

**Usage:**
```tsx
import { RiskAnalysis } from '@/modules/enrichment';

// Dans une page parametres (acces restreint)
<RiskAnalysis
  siren="443061841"
  autoLoad={true}
  showDetails={true}
  onAnalysis={(analysis) => console.log(analysis)}
/>
```

### 23. Provider VIES - Validation TVA Europeenne [2026-02-13]

**Fonctionnalite:** Validation des numeros de TVA intracommunautaires via l'API VIES de la Commission Europeenne.

**Backend:**
- `/app/modules/enrichment/providers/vies.py` - **NOUVEAU** Provider VIES avec:
  - Validation format TVA par pays (27 pays UE + Irlande du Nord XI)
  - Appel API REST `ec.europa.eu/taxation_customs/vies/rest-api`
  - Parsing adresse intelligente par pays (codes postaux differents)
  - Mapping vers entite Contact (vat_number, vat_valid, address, etc.)
  - Cache 24h (donnees stables)
- `/app/modules/enrichment/models.py`:
  - Ajout `EnrichmentProvider.VIES`
  - Ajout `LookupType.VAT_NUMBER`
  - Rate limits: 20 req/min, 500 req/jour
- `/app/modules/enrichment/service.py`:
  - Import et enregistrement VIESProvider
  - Ajout `VAT_NUMBER` dans PROVIDER_REGISTRY et ENTITY_LOOKUP_MAPPING
- `/app/modules/enrichment/providers/__init__.py` - Export VIESProvider
- `/app/modules/enrichment/schemas.py` - Exemple vat_number dans documentation
- `/app/modules/enrichment/router.py` - Documentation mise a jour

**Frontend:**
- `/frontend/src/modules/enrichment/types.ts`:
  - Ajout `'vies'` dans EnrichmentProvider
  - Ajout `'vat_number'` dans LookupType
  - Ajout interface `EnrichedVatFields`
  - Ajout interface `VatLookupProps`
  - Ajout `vat_number`, `vat_valid`, `country_code` dans EnrichedContactFields

**Formats TVA supportes (exemples):**
| Pays | Format | Exemple |
|------|--------|---------|
| FR | 2 caracteres + 9 chiffres | FR40303265045 |
| DE | 9 chiffres | DE123456789 |
| BE | 0/1 + 9 chiffres | BE0123456789 |
| ES | lettre/chiffre + 7 chiffres + lettre/chiffre | ESX1234567X |
| IT | 11 chiffres | IT12345678901 |
| NL | 9 chiffres + B + 2 chiffres | NL123456789B01 |

**Usage API:**
```http
POST /v1/enrichment/lookup
{
  "lookup_type": "vat_number",
  "lookup_value": "FR40303265045",
  "entity_type": "contact"
}
```

**Response:**
```json
{
  "success": true,
  "enriched_fields": {
    "name": "GOOGLE FRANCE SARL",
    "company_name": "GOOGLE FRANCE SARL",
    "vat_number": "FR40303265045",
    "vat_valid": true,
    "address_line1": "8 RUE DE LONDRES",
    "postal_code": "75009",
    "city": "PARIS",
    "country_code": "FR",
    "country": "France"
  },
  "confidence": 1.0,
  "source": "vies"
}
```

### 24. Configuration Provider Enrichissement - Interface Admin [2026-02-14]

**Fonctionnalite:** Interface complete pour configurer les providers d'enrichissement par tenant.

**Backend:**
- `/app/modules/enrichment/models.py`:
  - Ajout enum `OPENCORPORATES`, `CREDITSAFE`, `KOMPANY` dans `EnrichmentProvider`
  - Nouveau modele `EnrichmentProviderConfig` avec champs:
    - `tenant_id`, `provider`, `is_enabled`, `is_primary`, `priority`
    - `api_key`, `api_secret`, `api_endpoint` (credentials)
    - `custom_requests_per_minute`, `custom_requests_per_day` (rate limits)
    - `config_data` (JSON), statistiques (`total_requests`, `total_errors`)
  - Dictionnaire `PROVIDER_INFO` avec metadata de chaque provider
- `/app/modules/enrichment/router.py` - Nouveaux endpoints admin:
  - `GET /v1/enrichment/admin/providers` - Liste tous les providers avec leur config
  - `POST /v1/enrichment/admin/providers` - Cree une config provider
  - `PATCH /v1/enrichment/admin/providers/{provider_code}` - Met a jour une config
  - `DELETE /v1/enrichment/admin/providers/{provider_code}` - Supprime une config
  - `POST /v1/enrichment/admin/providers/{provider_code}/test` - Teste la connexion
- `/app/modules/enrichment/schemas.py` - Nouveaux schemas:
  - `ProviderInfoResponse`, `ProviderConfigResponse`
  - `ProviderConfigCreateRequest`, `ProviderConfigUpdateRequest`
  - `ProviderTestResult`, `ProvidersListResponse`
- `/app/modules/enrichment/service.py`:
  - Methodes `_load_provider_config()`, `_is_provider_enabled()`, `_get_provider_api_key()`
  - Integration config dans initialisation des providers

**Frontend:**
- `/frontend/src/modules/admin/components/EnrichmentProvidersView.tsx` - **NOUVEAU** Composant complet:
  - Liste des providers avec cartes (nom, description, statut, stats)
  - Indicateurs: gratuit/payant, actif/inactif, primaire
  - Boutons: Activer/Desactiver, Configurer, Tester, Definir primaire
  - Modal de configuration avec:
    - Cle API, Secret API, Endpoint personnalise
    - Limites de requetes (par minute, par jour)
    - Configuration JSON additionnelle
- `/frontend/src/modules/admin/components/index.ts` - Export EnrichmentProvidersView
- `/frontend/src/modules/admin/index.tsx`:
  - Ajout `'enrichment'` dans type `View`
  - Ajout onglet "Enrichissement" dans menu admin
  - Rendu conditionnel `EnrichmentProvidersView`

**Migration:**
- `/alembic/versions/20260214_enrichment_provider_config.py`:
  - Table `enrichment_provider_config`
  - Index sur `tenant_id`, `is_enabled`, `is_primary`
  - Contrainte unique `(tenant_id, provider)`

### 25. Provider OpenCorporates [2026-02-14]

**Fonctionnalite:** Integration du registre mondial d'entreprises OpenCorporates (140+ pays).

**Backend:**
- `/app/modules/enrichment/providers/opencorporates.py` - **NOUVEAU** Provider:
  - API REST `api.opencorporates.com/v0.4`
  - Lookup par nom d'entreprise (`name`) ou numero (`company_number`)
  - Detection automatique juridiction France (SIRET/SIREN)
  - Mapping vers entite Contact
  - Cache 24h
  - Rate limits: 50 req/min gratuit, 500 req/jour
- `/app/modules/enrichment/providers/__init__.py` - Export OpenCorporatesProvider
- `/app/modules/enrichment/service.py`:
  - Import et enregistrement dans `PROVIDER_REGISTRY`
  - OpenCorporates comme fallback pour SIRET, SIREN, NAME, RISK

**Capabilities:**
| Lookup Type | Providers (ordre priorite) |
|-------------|---------------------------|
| SIRET | insee, opencorporates |
| SIREN | insee, opencorporates |
| NAME | insee, opencorporates |
| RISK | pappers, opencorporates |

### 26. Erreurs 403 Forbidden sur tous les endpoints [2026-02-14]

**Probleme:** Tous les endpoints API retournaient 403 Forbidden pour l'utilisateur SUPERADMIN:
```
/v1/commercial/documents → 403
/v1/purchases/summary → 403
/v1/treasury/summary → 403
/v1/admin/dashboard → 403
```

**Cause:** Le middleware RBAC dans `/app/modules/iam/rbac_matrix.py` avait `SUPER_ADMIN` (avec underscore) dans `LEGACY_ROLE_MAPPING`, mais l'utilisateur avait le role `SUPERADMIN` (sans underscore) stocke dans `UserRole` enum.

**Solution:** Ajout du mapping manquant dans `LEGACY_ROLE_MAPPING` (ligne 765):
```python
LEGACY_ROLE_MAPPING = {
    "SUPERADMIN": StandardRole.SUPER_ADMIN,  # Sans underscore (UserRole enum)
    "SUPER_ADMIN": StandardRole.SUPER_ADMIN,  # Avec underscore (legacy)
    "TENANT_ADMIN": StandardRole.ADMIN,
    # ...
}
```

**Verification:**
```bash
# Tous les endpoints retournent 200
/health → 200
/v1/iam/capabilities/modules → 200
/v1/commercial/documents → 200
/v1/admin/dashboard → 200
```

**Commit:** c1b0597

---

### 27. Deploiement Production azalscore.com - Reseau Docker [2026-02-14]

**Probleme:** Apres rebuild de l'API, nginx ne pouvait plus atteindre le backend.

**Cause:** L'API avait une nouvelle IP Docker (172.19.0.3) mais nginx avait cache l'ancienne (172.18.0.12).

**Solution:**
```bash
# Reconnecter API aux reseaux
docker network connect azalscore_azals_internal azals_api
docker network connect azalscore_azals_external azals_api

# Recharger nginx pour refresh DNS
docker exec azals_nginx nginx -s reload
```

**Verification deploiement:**
```bash
# Health check
curl https://azalscore.com/health

# Test endpoint admin (401 = OK, auth requise)
curl -H "X-Tenant-ID: masith" https://azalscore.com/v1/enrichment/admin/providers
```

**Etat final:**
| Composant | Status |
|-----------|--------|
| Frontend | OK |
| API Health | Healthy |
| Database | Connected (2.8ms) |
| Redis | Connected (1.1ms) |
| Nginx → API | Fixed |
| Enrichment Admin | 401 (normal sans token) |

---

## Taches en Attente

### TODO: Autocomplete Articles dans Devis/Commandes/Factures
- [x] Creer composant `ProductAutocomplete` pour recherche d'articles - FAIT (2026-02-13)
  - Backend: `/app/modules/inventory/router.py` endpoint `/products/autocomplete`
  - Backend: `/app/modules/inventory/service.py` methode `search_products_autocomplete`
  - Frontend: `/frontend/src/modules/inventory/components/ProductAutocomplete.tsx`
- [x] Integrer dans module invoicing - FAIT (2026-02-13)
  - `/frontend/src/modules/invoicing/components/LineEditor.tsx` - Editeur de ligne modal
  - Auto-remplir: description, prix unitaire, TVA, code article, unite
- [x] Utiliser LineEditor dans les vues de creation/edition de documents - FAIT (2026-02-13)
  - `/frontend/src/modules/invoicing/index.tsx` - LinesEditor refactorise
  - Modal LineEditorModal avec ProductAutocomplete
  - Boutons Edit/Delete par ligne
  - Fonctionne pour devis, commandes et factures

### TODO: Notations Credit Internationales
- [x] **Pappers** (France) - IMPLEMENTE (2026-02-10)
  - Cotation Banque de France
  - Procedures collectives
  - Score de risque AZALS (0-100)
  - Fallback vers INSEE si pas de cle API
- [x] **Configuration Provider Risque** - IMPLEMENTE (2026-02-14)
  - Interface admin pour configurer API keys: `/frontend/src/modules/admin/components/EnrichmentProvidersView.tsx`
  - Selection du provider principal (Pappers, OpenCorporates, Creditsafe, etc.)
  - Fallback automatique vers provider secondaire
  - Backend: `/app/modules/enrichment/models.py` (EnrichmentProviderConfig)
  - Backend: `/app/modules/enrichment/router.py` (endpoints /admin/providers)
  - Migration: `/alembic/versions/20260214_enrichment_provider_config.py`
  - Onglet "Enrichissement" dans Administration
- [x] **OpenCorporates** - IMPLEMENTE (2026-02-14)
  - Provider: `/app/modules/enrichment/providers/opencorporates.py`
  - Donnees de base entreprise (140+ pays)
  - Statut juridique
  - Recherche par nom ou numero d'entreprise
  - API gratuite limitee (500 req/mois) ou payante
- [x] **VIES** (gratuit) - Validation TVA intracommunautaire - IMPLEMENTE (2026-02-13)
  - Verification numero TVA europeen via API REST Commission Europeenne
  - Nom et adresse de l'entreprise
  - Formats TVA par pays (27 pays UE + XI)
  - Integration dans module enrichment
- [ ] **Creditsafe** (payant) - Notation credit internationale
  - Enum ajoute dans EnrichmentProvider
  - Provider a implementer quand cle API disponible
  - Score credit D&B, notation Moody's / S&P / Fitch
- [ ] **Kompany** (payant) - Registres europeens
  - Enum ajoute dans EnrichmentProvider
  - Provider a implementer quand cle API disponible
  - Documents officiels, comptes annuels

---

## Principe de Maintenance des Capabilities

**IMPORTANT:** A chaque creation ou modification de module/fonctionnalite, mettre a jour:

1. **Backend** - `/app/modules/iam/router.py`:
   - Ajouter/modifier les capabilities dans `CAPABILITIES_BY_MODULE`
   - Format:
   ```python
   "module_code": {
       "name": "Nom du Module",
       "icon": "IconName",  # Icone Lucide
       "capabilities": [
           {"code": "module.action", "name": "Nom lisible", "description": "Description"},
           # ...
       ]
   }
   ```

2. **Backend** - `/app/api/auth.py`:
   - Ajouter les nouvelles capabilities dans `ALL_CAPABILITIES`
   - Mettre a jour `role_capabilities` si necessaire pour les roles specifiques

3. **Frontend** - Verifier que les nouvelles capabilities sont utilisees dans les composants

---

## Configurations Importantes

### Utilisateur Admin Principal
- **Email:** contact@masith.fr
- **Tenant:** masith
- **Role:** SUPERADMIN

### Utilisateur Test
- **Email:** s.moreau83170@gmail.com
- **Tenant:** test
- **Role:** DIRIGEANT
- **Mot de passe:** password123 (doit etre change a la premiere connexion)

### Routes RBAC Authentifiees (sans verification permissions)
Dans `/app/modules/iam/rbac_middleware.py` - `AUTHENTICATED_ONLY_ROUTES`:
```python
r"^/v1/iam/users.*$",
r"^/v1/iam/roles.*$",
r"^/v1/iam/permissions.*$",
r"^/v1/tenants.*$",
r"^/v1/cockpit/.*$",
r"^/v1/admin/.*$",
```

---

## Commandes Utiles

### Verifier l'API
```bash
curl -s http://localhost/health | jq .
```

### Redemarrer l'API
```bash
docker compose restart api
```

### Voir les logs
```bash
docker logs azals_api --tail 100
```

### Reconstruire et redemarrer le frontend
```bash
cd /home/ubuntu/azalscore/frontend
npm run build
docker restart azals_frontend
```

### Copier un fichier modifie dans le container API
```bash
docker cp /home/ubuntu/azalscore/app/api/auth.py azals_api:/app/app/api/auth.py
docker restart azals_api
```

### Verifier un fichier dans le container
```bash
docker exec azals_api grep "PATTERN" /app/app/chemin/fichier.py
```

### Nettoyer un tenant orphelin
```bash
docker exec -i azals_postgres psql -U azals_user -d azals -c "
DO \$\$
DECLARE r RECORD;
BEGIN
    FOR r IN (SELECT table_name FROM information_schema.columns
              WHERE column_name = 'tenant_id' AND table_schema = 'public'
              AND table_name NOT IN ('trial_registrations'))
    LOOP
        EXECUTE format('DELETE FROM %I WHERE tenant_id = %L', r.table_name, 'TENANT_ID_ICI');
    END LOOP;
END \$\$;
"
```

### Mettre a jour un role utilisateur
```bash
docker exec -i azals_postgres psql -U azals_user -d azals -c "UPDATE users SET role = 'SUPERADMIN' WHERE email = 'EMAIL_ICI';"
```

### Verifier les reseaux Docker des containers
```bash
docker inspect azals_api --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}'
```

### Reconnecter un container a un reseau
```bash
docker network connect azalscore_azals_internal azals_api
```

### Rebuild et deployer le frontend
```bash
cd /home/ubuntu/azalscore/frontend
docker build -f Dockerfile.prod -t azalscore-frontend:0.5.4-tailwind .
docker stop azals_frontend && docker rm azals_frontend
docker run -d --name azals_frontend --network azalscore_azals_external azalscore-frontend:0.5.4-tailwind
docker exec azals_nginx nginx -s reload
```

### Lister les providers enrichissement
```bash
docker exec azals_api python -c "
from app.modules.enrichment.models import PROVIDER_INFO
for p, info in PROVIDER_INFO.items():
    print(f'{p.value}: {info[\"name\"]}')"
```

### Verifier la table enrichment_provider_config
```bash
docker exec azals_api python -c "
from app.core.database import SessionLocal
from app.modules.enrichment.models import EnrichmentProviderConfig
db = SessionLocal()
for c in db.query(EnrichmentProviderConfig).all():
    print(f'{c.tenant_id}/{c.provider.value}: enabled={c.is_enabled}')"
```

---

## Fichiers Modifies

### Backend (app/)
1. `/app/core/core_auth_middleware.py` - Ajout request.state.user
2. `/app/modules/iam/router.py` - UUID pour IDs, PUT permissions, created_by_name, **CAPABILITIES_BY_MODULE**, endpoint `/capabilities/modules`
3. `/app/modules/iam/schemas.py` - Ajout created_by_name dans RoleResponse
4. `/app/modules/tenants/router.py` - Logique list_tenants pour SUPERADMIN
5. `/app/modules/tenants/schemas.py` - UUID pour id, validators pour enums
6. `/app/modules/tenants/service_trial.py` - actor_email pour TenantService
7. `/app/api/auth.py` - SUPERADMIN dans role_capabilities, format reponse capabilities
8. `/app/api/admin.py` - **NOUVEAU** endpoint /v1/admin/dashboard
9. `/app/main.py` - Import et inclusion du router admin_dashboard
10. `/app/modules/enrichment/schemas.py` - suggestions, ProviderConfigResponse, ProviderTestResult, etc.
11. `/app/modules/enrichment/models.py` - EnrichmentProviderConfig, PROVIDER_INFO, nouveaux enums
12. `/app/modules/enrichment/router.py` - Endpoints admin /admin/providers (CRUD + test)
13. `/app/modules/enrichment/service.py` - Config loading, OpenCorporates integration
14. `/app/modules/enrichment/providers/opencorporates.py` - **NOUVEAU** Provider OpenCorporates
15. `/app/modules/enrichment/providers/__init__.py` - Export OpenCorporatesProvider
16. `/app/modules/purchases/schemas.py` - code: Optional[str] auto-genere
17. `/app/modules/inventory/models.py` - 11 champs ERP (tax_rate, is_sellable, etc.)
18. `/app/modules/iam/rbac_matrix.py` - Mapping SUPERADMIN dans LEGACY_ROLE_MAPPING
19. `/app/modules/treasury/service.py` - Ajout get_summary(), get_forecast()
20. `/app/modules/accounting/service.py` - Fix references modeles (AccountingJournalEntry, etc.)

### Frontend (frontend/src/)
1. `/modules/admin/index.tsx` - Hooks, gestion roles, Createur, **UserPermissionsModal**, **UsersPermissionsView**, onglet "Acces Modules", onglet "Enrichissement"
2. `/modules/admin/types.ts` - Ajout created_by_name dans interface Role
3. `/modules/admin/components/SequencesView.tsx` - Hooks corriges
4. `/modules/admin/components/EnrichmentProvidersView.tsx` - **NOUVEAU** Interface admin providers
5. `/modules/admin/components/index.ts` - Export EnrichmentProvidersView
6. `/ui-engine/simple/PermissionsManager.tsx` - Hooks corriges
7. `/core/capabilities/index.tsx` - Parsing robuste avec logging
8. `/modules/enrichment/` - **NOUVEAU MODULE** CompanyAutocomplete, AddressAutocomplete, SiretLookup, BarcodeLookup
9. `/modules/purchases/index.tsx` - Integration enrichissement, hooks corriges format reponse, code auto-genere

### Migrations (alembic/)
1. `/alembic/versions/20260214_enrichment_provider_config.py` - Table enrichment_provider_config
2. `/alembic/versions/20260214_product_erp_fields.py` - Champs ERP produits (11 colonnes)

---

## Tenants en Base

| tenant_id | name       | email                   | status | plan       |
|-----------|------------|-------------------------|--------|------------|
| masith    | SAS MASITH | contact@masith.fr       | ACTIVE | STARTER    |
| test      | test       | s.moreau83170@gmail.com | ACTIVE | ENTERPRISE |

---

## Systeme CSS - Tailwind v4

Le projet utilise **Tailwind CSS v4** pour generer les classes utilitaires CSS automatiquement.

### Configuration

1. **Fichiers de configuration:**
   - `/frontend/postcss.config.js` - Plugin PostCSS pour Tailwind
   - `/frontend/tailwind.config.js` - Configuration Tailwind (content paths)

2. **Import dans le CSS principal:**
   ```css
   /* /frontend/src/styles/main.css */
   @import "tailwindcss";
   ```

3. **Packages requis:**
   ```bash
   npm install -D tailwindcss @tailwindcss/postcss autoprefixer
   ```

### Fonctionnement

- Tailwind scanne tous les fichiers dans `src/**/*.{js,ts,jsx,tsx}`
- Il genere automatiquement les classes CSS utilisees (JIT - Just In Time)
- Les classes non utilisees ne sont PAS incluses dans le bundle final
- Compatible avec les classes existantes du design system AZALS

### Classes disponibles

Toutes les classes utilitaires Tailwind standard:
- Layout: `flex`, `grid`, `block`, `inline-flex`
- Spacing: `p-4`, `m-2`, `gap-3`, `space-x-2`
- Colors: `bg-blue-100`, `text-gray-500`, `border-green-500`
- Typography: `text-sm`, `font-medium`, `text-center`
- Borders: `rounded-lg`, `border`, `border-2`
- Effects: `shadow-lg`, `opacity-50`, `hover:bg-blue-600`

---

## Architecture Menu Frontend

### Deux systemes de menu coexistent:

1. **UnifiedLayout** (`/frontend/src/components/UnifiedLayout.tsx`)
   - Utilise par `main.tsx` via `UnifiedApp`
   - Menu defini dans `MENU_ITEMS` (tableau statique)
   - C'est le menu ACTIF en production
   - Pour ajouter un module: modifier `MENU_ITEMS` ET le type `ViewKey`

2. **DynamicMenu** (`/frontend/src/ui-engine/menu-dynamic/index.tsx`)
   - Importe par `MainLayout` dans `@ui/layout`
   - Menu defini dans `MENU_SECTIONS` avec structure hierarchique
   - N'est PAS utilise car l'app charge `UnifiedApp` et non `App.tsx`
   - Reserve pour future migration vers systeme de menu dynamique

### Pour ajouter un nouveau module au menu (COMPLET):

Il faut modifier **5 fichiers** pour qu'un module apparaisse dans le menu ET dans "Acces Modules":

#### 1. Menu ACTIF - `/frontend/src/components/UnifiedLayout.tsx` (OBLIGATOIRE)

C'est le menu utilise en production. Modifier:

```typescript
// Type ViewKey (ligne ~35)
export type ViewKey =
  | 'saisie'
  // ...existant
  | 'import-odoo' | 'import-axonaut'  // Ajouter les nouvelles cles
  | 'admin'
  | 'profile' | 'settings';

// MENU_ITEMS (ligne ~66)
const MENU_ITEMS: MenuItem[] = [
  // ...existant
  { key: 'import-odoo', label: 'Import Odoo', group: 'Import', capability: 'import.odoo.config' },
  { key: 'import-axonaut', label: 'Import Axonaut', group: 'Import', capability: 'import.axonaut.config' },
  { key: 'admin', label: 'Administration', group: 'Système', capability: 'admin.view' },
];
```

#### 2. Menu dynamique (optionnel) - `/frontend/src/ui-engine/menu-dynamic/index.tsx`

```typescript
// Ajouter l'icone dans ICON_MAP (ligne ~50)
import { Download, /* autres imports */ } from 'lucide-react';

const ICON_MAP = {
  // ...existant
  download: Download,
};

// Ajouter la section dans MENU_SECTIONS (avant 'admin')
{
  id: 'import',
  title: 'Import de Donnees',
  items: [
    {
      id: 'import-odoo',
      label: 'Import Odoo',
      icon: 'download',
      path: '/import/odoo',
      capability: 'import.odoo.config',  // DOIT correspondre au code dans CAPABILITIES_BY_MODULE
    },
    // ... autres items
  ],
},
```

#### 2. Capabilities utilisateur - `/app/api/auth.py`

```python
# Ajouter dans ALL_CAPABILITIES (ligne ~1040)
ALL_CAPABILITIES = [
    # ...existant
    # Import de donnees
    "import.config.create", "import.config.read", "import.config.update", "import.config.delete",
    "import.execute", "import.cancel",
    "import.odoo.config", "import.odoo.execute", "import.odoo.preview",
    # ... autres
]
```

#### 3. Interface "Acces Modules" - `/app/modules/iam/router.py`

```python
# Ajouter dans CAPABILITIES_BY_MODULE (ligne ~730)
CAPABILITIES_BY_MODULE = {
    # ...existant
    "import": {
        "name": "Import de Donnees",
        "icon": "Download",
        "capabilities": [
            {"code": "import.config.create", "name": "Créer config import", "description": "..."},
            {"code": "import.odoo.config", "name": "Configurer Odoo", "description": "..."},
            # ... autres
        ]
    },
}
```

#### 4. Permissions backend - `/app/modules/iam/permissions.py`

```python
# Ajouter le dictionnaire de permissions (si pas deja present)
IMPORT_PERMISSIONS = {
    "import.config.create": "Créer des configurations d'import",
    "import.config.read": "Voir les configurations d'import",
    # ... autres
}

# L'ajouter dans ALL_PERMISSIONS
ALL_PERMISSIONS = {
    # ...existant
    **IMPORT_PERMISSIONS,
}
```

#### 5. Deployer

```bash
./deploy-quick.sh all   # Rebuild frontend + restart API
```

Puis Ctrl+Shift+R dans le navigateur pour vider le cache.

### Exemple - Ajout Marceau IA (2026-02-09):

```typescript
// UnifiedLayout.tsx - Type ViewKey
| 'cockpit' | 'marceau'

// UnifiedLayout.tsx - MENU_ITEMS
{ key: 'marceau', label: 'Marceau IA', group: 'IA', capability: 'marceau.view' },
```

### Exemple - Ajout Import de Donnees (2026-02-14):

Fichiers modifies:
- `/frontend/src/ui-engine/menu-dynamic/index.tsx` - Section "Import de Donnees" avec 5 items
- `/app/api/auth.py` - 18 capabilities ajoutees dans ALL_CAPABILITIES
- `/app/modules/iam/router.py` - Module "import" dans CAPABILITIES_BY_MODULE avec 19 capabilities
- `/app/modules/iam/permissions.py` - IMPORT_PERMISSIONS (deja present)

---

## Principes de Developpement

### API Sans Version (URLs Stables)

**REGLE:** L'API AZALSCORE n'utilise PAS de prefixe de version (/v1, /v2, /v3).

**URLs:**
- ✅ Correct: `/commercial/customers`, `/accounting/summary`, `/iam/users`
- ❌ Incorrect: `/v1/commercial/customers`, `/v3/accounting/summary`

**Avantages:**
- URLs simples et stables
- Pas de migration frontend a chaque changement de version
- Moins de confusion pour les developpeurs

**Implementation:**
- Backend: Routers montes sans prefixe (`APIRouter()` sans `prefix`)
- Frontend: Appels API directs (`/commercial/customers`)
- Legacy: Routes essentielles (auth, cockpit) integrees au router principal

**Fichiers concernes:**
- `/app/api/v3/__init__.py` - Router principal sans prefixe
- `/app/main.py` - Montage direct des routers
- Frontend: Tous les fichiers `.ts/.tsx` utilisent des URLs sans version

**Date d'application:** 2026-02-15

---

### Reutilisabilite - Sous-Programmes
**REGLE:** Tout element repete doit faire l'objet d'un sous-programme (composant, hook, fonction, vue) appele au besoin.

**Exemples implementes:**
- `CompanyAutocomplete` - Recherche entreprise utilisable dans fournisseurs ET clients
- `AddressAutocomplete` - Autocomplete adresse reutilisable partout
- `SiretLookup` - Recherche SIRET/SIREN reutilisable
- `ClientFormPage` - Formulaire client reutilisable (partners module)
- `SupplierFormPage` - Formulaire fournisseur reutilisable (purchases module)

**A creer:**
- `ProductAutocomplete` - Recherche article pour lignes de documents
- `ContactAutocomplete` - Recherche contact pour formulaires

**Emplacement des composants reutilisables:**
- Enrichissement: `/frontend/src/modules/enrichment/`
- Formulaires partenaires: `/frontend/src/modules/partners/`
- Composants UI generiques: `/frontend/src/ui-engine/`

---

## Notes Importantes

### Synchronisation Container Docker
- Les fichiers Python sont montes en volume MAIS le container peut avoir une version en cache
- Apres modification d'un fichier `.py`, TOUJOURS verifier dans le container:
  ```bash
  docker exec azals_api cat /app/app/chemin/fichier.py | head -50
  ```
- Si necessaire, copier manuellement et redemarrer:
  ```bash
  docker cp fichier.py azals_api:/app/app/chemin/
  docker restart azals_api
  ```

### Format de reponse API
- Le frontend attend des reponses directes (pas d'enveloppe `data`)
- Exemple correct: `{ "items": [...], "total": 10 }` ou `[...]`
- Exemple incorrect: `{ "data": { "items": [...] } }`

### Capabilities et Roles
- Les roles definis dans `/app/api/auth.py` fonction `get_user_capabilities()`
- `SUPERADMIN`, `SUPER_ADMIN`, `DIRIGEANT`, `ADMIN` ont ALL_CAPABILITIES
- Le frontend verifie `admin.view` pour afficher le module Admin

---

## Documentation Technique

### Variables et Configuration

**IMPORTANT:** Avant de modifier la configuration ou les variables d'environnement, consulter:
- `/docs/architecture/VARIABLES.md` - **Guide complet des variables**
  - Variables d'environnement (obligatoires et optionnelles)
  - Constantes de configuration (app/core/config.py, app/ai/config.py)
  - Constantes de test
  - Inconsistances detectees et plan d'harmonisation
  - Conventions de nommage

### Fixtures de Test

**IMPORTANT:** Avant de modifier ou creer des tests, consulter:
- `/docs/guides/FIXTURES_STANDARD.md` - Guide de reference complet

**Principes cles:**
1. Toutes les fixtures de base sont dans `app/conftest.py` (global)
2. Les modules NE DOIVENT PAS redefinir `tenant_id`, `user_id`, `mock_saas_context` (autouse)
3. Chaque module DOIT definir `client(test_client)` et `auth_headers(tenant_id)` comme alias

**Fixtures globales disponibles:**
| Fixture | Type | Valeur |
|---------|------|--------|
| `tenant_id` | str | `"tenant-test-001"` |
| `user_id` | str (UUID) | `"12345678-1234-1234-1234-123456789001"` |
| `user_uuid` | UUID | UUID object |
| `db_session` | Session | SQLite in-memory |
| `test_client` | TestClient | Headers auto-injectes |
| `saas_context` | SaaSContext | Contexte ADMIN |

**Template conftest module:**
```python
@pytest.fixture
def client(test_client):
    return test_client

@pytest.fixture
def auth_headers(tenant_id):
    return {"Authorization": "Bearer test-token", "X-Tenant-ID": tenant_id}
```

---

### 28. Champs ERP Produits - Conformite Chorus Pro [2026-02-14]

**Contexte:** Ajout de champs au modele `inventory_products` pour assurer la compatibilite avec:
- Chorus Pro / Factur-X / EN 16931 (facturation electronique francaise)
- Axonaut, Odoo, Sellsy (ERP francais)

**Analyse comparative effectuee:**
- AXONAUT: product_code, name, price, tax_rate, type
- ODOO: default_code, sale_ok, purchase_ok, taxes_id, seller_ids
- SELLSY: tradename, unitAmount, taxrate, taxid, ecoTax
- CHORUS PRO: BT-152 (tax_rate), BT-151 (tax_id), BT-156 (customer_product_code), BT-158 (cpv_code)

**11 champs ajoutes a `inventory_products`:**

| Champ | Type | Description | Source |
|-------|------|-------------|--------|
| `trade_name` | String(255) | Nom commercial | Sellsy |
| `cpv_code` | String(20) | Code marches publics | EN 16931 BT-158 |
| `supplier_product_code` | String(100) | Reference fournisseur | Odoo |
| `customer_product_code` | String(100) | Reference client | EN 16931 BT-156 |
| `tax_rate` | Numeric(5,2) | Taux TVA vente % | EN 16931 BT-152 |
| `tax_id` | UUID | Reference taxe vente | EN 16931 BT-151 |
| `supplier_tax_rate` | Numeric(5,2) | Taux TVA achat % | Odoo |
| `supplier_tax_id` | UUID | Reference taxe achat | Odoo |
| `eco_tax` | Numeric(10,4) | Eco-contribution EUR | Sellsy |
| `is_sellable` | Boolean | Produit vendable | Odoo sale_ok |
| `is_purchasable` | Boolean | Produit achetable | Odoo purchase_ok |

**Fichiers modifies:**
- `/app/modules/inventory/models.py` - Ajout des 11 colonnes au modele Product
- `/alembic/versions/20260214_product_erp_fields.py` - Migration Alembic

**Migration:**
```
revision = 'product_erp_fields_001'
down_revision = 'enrichment_provider_config_001'
```

### 29. Fix Endpoints Treasury et Accounting [2026-02-14]

**Probleme:** Les endpoints `/v1/treasury/summary` et `/v1/accounting/summary` retournaient des erreurs 500.

**Causes:**
1. **Treasury:** La methode `get_summary()` n'existait pas dans `TreasuryService`
2. **Accounting:** References incorrectes aux modeles (`FiscalYear` au lieu de `AccountingFiscalYear`, `JournalEntry` au lieu de `AccountingJournalEntry`, etc.)

**Solutions appliquees:**

**Treasury (`/app/modules/treasury/service.py`):**
```python
def get_summary(self) -> TreasurySummary:
    """Retourne un resume de tresorerie vide (TODO: implementer avec vrais modeles)"""
    return TreasurySummary(
        total_balance=Decimal("0.00"),
        total_pending_in=Decimal("0.00"),
        total_pending_out=Decimal("0.00"),
        forecast_7d=Decimal("0.00"),
        forecast_30d=Decimal("0.00"),
        accounts=[]
    )

def get_forecast(self, days: int = 30) -> List[ForecastData]:
    """Retourne une liste vide (TODO: implementer)"""
    return []
```

**Accounting (`/app/modules/accounting/service.py`):**
- `FiscalYear` → `AccountingFiscalYear` (lignes 96, 115)
- `JournalEntry` → `AccountingJournalEntry` (lignes 387, 388, 636, 722)
- `JournalEntryLine` → `AccountingJournalEntryLine` (lignes 522-528, 627-633)

**Verification:**
```
[OK] /v1/treasury/summary    → 200
[OK] /v1/accounting/summary  → 200
```

**Commit:** 6541997

**Note:** Le module Treasury n'a pas encore de modeles de base de donnees (`BankAccount`, `BankTransaction`). Les methodes retournent des donnees vides en attendant l'implementation complete.

### 30. Module Odoo Import [2026-02-14]

**Objectif:** Creer un module d'import de donnees depuis Odoo (versions 8-18) pour permettre la migration des donnees existantes vers AZALSCORE.

**Fonctionnalites:**
- Configuration de connexion Odoo par tenant (URL, database, API key)
- Import des produits (`product.product` → `Product`)
- Import des contacts/clients (`res.partner` → `UnifiedContact`)
- Import des fournisseurs (`res.partner` avec `supplier_rank > 0`)
- Delta sync base sur `write_date` Odoo
- Historique complet des imports
- Previsualisation des donnees avant import
- Mapping personnalisable des champs

**Architecture:**
```
app/modules/odoo_import/
├── __init__.py          # Exports du module
├── models.py            # OdooConnectionConfig, OdooImportHistory, OdooFieldMapping
├── schemas.py           # Schemas Pydantic pour l'API
├── connector.py         # Client XML-RPC Odoo (versions 8-18)
├── mapper.py            # Mapping des champs Odoo → AZALSCORE
├── service.py           # OdooImportService (orchestration)
└── router.py            # Endpoints API REST
```

**Endpoints API:**
- `POST /api/v1/odoo/config` - Creer une configuration
- `GET /api/v1/odoo/config` - Lister les configurations
- `POST /api/v1/odoo/test` - Tester une connexion
- `POST /api/v1/odoo/import/products` - Importer les produits
- `POST /api/v1/odoo/import/contacts` - Importer les contacts
- `POST /api/v1/odoo/import/suppliers` - Importer les fournisseurs
- `POST /api/v1/odoo/import/full` - Synchronisation complete
- `GET /api/v1/odoo/history` - Historique des imports
- `POST /api/v1/odoo/preview` - Previsualiser les donnees

**Compatibilite Odoo:**
- Versions 8-13: Authentification username/password
- Versions 14-18: Authentification API key (recommandee)
- API XML-RPC (`/xmlrpc/2/common`, `/xmlrpc/2/object`)

**Fichiers crees:**
21. `/app/modules/odoo_import/__init__.py`
22. `/app/modules/odoo_import/models.py`
23. `/app/modules/odoo_import/schemas.py`
24. `/app/modules/odoo_import/connector.py`
25. `/app/modules/odoo_import/mapper.py`
26. `/app/modules/odoo_import/service.py`
27. `/app/modules/odoo_import/router.py`
28. `/alembic/versions/20260214_odoo_import.py`

**Fichiers modifies:**
- `/app/main.py` - Import et enregistrement du router

**Multi-tenant:** Isolation complete par `tenant_id` sur toutes les tables et requetes.

**Activation:** Menu Administration > Acces Modules > Import de donnees

**Note:** Ce module servira de base pour les futurs imports (Axonaut, Pennylane, Sage, Chorus, etc.)

---

## TODOLIST COMPLÈTE AZALSCORE — 123 TÂCHES

**Mise à jour:** 2026-02-15
**Référence:** `/home/ubuntu/azalscore/PROMPT_PHASE_CRITIQUE.md`

> **ALERTE:** Audit du 2026-02-15 révèle que 98.5% des endpoints backend (1090/1107) ne sont PAS utilisés par le frontend.
> Phase 0.5 ajoutée pour corriger cette situation.

---

### PHASE 0 — FONDATIONS TECHNIQUES (15 tâches) — BLOQUANT

| # | Tâche | Statut |
|---|-------|--------|
| #117 | Pipeline CI/CD Complet | ⬜ |
| #110 | Processus de Code Review | ⬜ |
| #109 | Analyse Statique de Code (SonarQube) | ⬜ |
| #113 | Environnement Staging Complet | ⬜ |
| #96 | Analyse Vulnérabilités Dépendances (SCA) | ⬜ |
| #97 | Audit Secrets et Credentials | ⬜ |
| #27 | Négocier et signer contrats partenaires | ⬜ |
| #28 | Validation juridique Finance Suite | ⬜ |
| #2 | Créer les modèles SQLAlchemy Finance Suite | ⬜ |
| #3 | Créer les schemas Pydantic Finance Suite | ⬜ |
| #11 | Créer la migration Alembic Finance Suite | ⬜ |
| #9 | Créer le router API Finance Suite | ⬜ |
| #10 | Créer le service orchestrateur Finance Suite | ⬜ |
| #21 | Implémenter la sécurité Finance Suite | ⬜ |
| #93 | Implémenter Validations et Workflows Approbation | ⬜ |

**Effort:** 5-6 semaines

---

### PHASE 0.5 — ACTIVATION FRONTEND BACKEND (7 tâches) — CRITIQUE [NOUVEAU]

> **Contexte:** 1090 endpoints backend existent mais ne sont PAS appelés par le frontend.

| # | Tâche | Endpoints | Statut |
|---|-------|-----------|--------|
| #118 | Créer frontend Country Packs France (FEC, DSN, TVA, RGPD) | 67 | ⬜ |
| #119 | Créer frontend eCommerce complet (Panier, Checkout, Coupons) | 60 | ⬜ |
| #120 | Créer frontend Helpdesk complet (Tickets, SLA, KB) | 60 | ⬜ |
| #121 | Créer frontend Field Service (GPS, Tournées, Check-in) | 53 | ⬜ |
| #122 | Créer frontend Compliance (Audits, Politiques, Incidents) | 52 | ⬜ |
| #123 | Créer frontend BI complet (Dashboards, Analytics, KPIs) | 49 | ⬜ |
| #124 | Consolider les routers backend (v1 → v2, supprimer doublons) | - | ⬜ |

**Impact:** Active 341 endpoints backend actuellement inutilisés.
**Effort:** 4-6 semaines

---

### PHASE 1 — CONFORMITÉ LÉGALE (9 tâches) — CRITIQUE

| # | Tâche | Priorité | Statut |
|---|-------|----------|--------|
| #49 | Facturation Électronique PDP | CRITIQUE | ⬜ |
| #52 | FEC conforme formats 2025 | CRITIQUE | ⬜ |
| #104 | Audit Conformité RGPD | CRITIQUE | ⬜ |
| #106 | Vérification Conformité NF525 (Caisse) | CRITIQUE | ⬜ |
| #50 | EDI-TVA automatique | HAUTE | ⬜ |
| #51 | Liasses Fiscales automatiques | HAUTE | ⬜ |
| #53 | Plan de Paie conforme France | HAUTE | ⬜ |
| #37 | Conformité Fiscale Avancée France | HAUTE | ⬜ |
| #108 | Vérification Conformité Normes AZALSCORE | HAUTE | ⬜ |

**Deadline:** Septembre 2026
**Effort:** 8-10 semaines

---

### PHASE 2 — FINANCE SUITE CORE (27 tâches) — HAUTE

| # | Tâche | Statut |
|---|-------|--------|
| #1 | Créer le module Finance Suite AZALSCORE | ⬜ |
| #4 | Implémenter le provider Swan (Banking) | ⬜ |
| #5 | Implémenter le provider NMI (Paiements) | ⬜ |
| #6 | Implémenter le provider Defacto (Affacturage) | ⬜ |
| #7 | Implémenter le provider Solaris (Crédit) | ⬜ |
| #8 | Implémenter les webhooks Finance Suite | ⬜ |
| #12 | Créer le frontend Finance Dashboard | ⬜ |
| #13 | Créer le frontend Banking (Swan) | ⬜ |
| #14 | Créer le frontend Payments (NMI) | ⬜ |
| #15 | Créer le frontend Tap to Pay | ⬜ |
| #16 | Créer le frontend Affacturage (Defacto) | ⬜ |
| #17 | Créer le frontend Crédit (Solaris) | ⬜ |
| #18 | Créer le frontend Settings Finance | ⬜ |
| #65 | Implémenter Cartes Virtuelles | ⬜ |
| #30 | Rapprochement Bancaire Automatique | ⬜ |
| #66 | Catégorisation Auto Opérations Bancaires | ⬜ |
| #67 | Prévisionnel Trésorerie avec Scénarios | ⬜ |
| #22 | Intégrer Finance Suite avec Comptabilité | ⬜ |
| #23 | Intégrer Finance Suite avec Facturation | ⬜ |
| #24 | Intégrer Finance Suite avec POS | ⬜ |
| #25 | Intégrer Finance Suite avec Trésorerie | ⬜ |
| #19 | Tests unitaires Finance Suite | ⬜ |
| #20 | Tests d'intégration Finance Suite | ⬜ |
| #105 | Audit Conformité PCI DSS | ⬜ |
| #98 | Audit Authentification et Autorisation | ⬜ |
| #94 | Audit Sécurité OWASP Top 10 | ⬜ |

**Effort:** 12-14 semaines

---

### PHASE 2.5 — TESTS & QUALITÉ (3 tâches) — HAUTE

| # | Tâche | Statut |
|---|-------|--------|
| #99 | Tests Unitaires - Couverture 80% | ⬜ |
| #100 | Tests d'Intégration API | ⬜ |
| #103 | Tests de Régression Automatisés | ⬜ |

**Effort:** 2-3 semaines

---

### PHASE 3 — MODULES MÉTIER (16 tâches) — HAUTE

| # | Tâche | Statut |
|---|-------|--------|
| #29 | OCR Factures Fournisseurs | ⬜ |
| #31 | Collaboration Comptable Temps Réel | ⬜ |
| #55 | Abonnements et Facturation Récurrente | ⬜ |
| #47 | Relances Clients Automatiques | ⬜ |
| #75 | Bons de Livraison | ⬜ |
| #78 | Gestion Lots et Numéros de Série | ⬜ |
| #76 | Contrôle Fabrication/Production | ⬜ |
| #77 | PLM (Product Lifecycle Management) | ⬜ |
| #38 | Suivi Temps et Feuilles d'Heures | ⬜ |
| #39 | Notes de Frais | ⬜ |
| #79 | Indemnités Kilométriques | ⬜ |
| #80 | Module Recrutement | ⬜ |
| #81 | Évaluations Employés | ⬜ |
| #82 | Gestion Parc Automobile | ⬜ |
| #36 | Multi-Sociétés et Consolidation | ⬜ |

**Effort:** 8-10 semaines

---

### PHASE 4 — INTERVENTIONS & MAINTENANCE (9 tâches) — MOYENNE

| # | Tâche | Statut |
|---|-------|--------|
| #32 | Gestion Interventions Terrain avec GPS | ⬜ |
| #33 | Planification Visuelle Techniciens | ⬜ |
| #61 | Optimisation Tournées et Routes | ⬜ |
| #64 | Photos dans Interventions | ⬜ |
| #34 | Maintenance Préventive GMAO | ⬜ |
| #35 | Gestion Équipements et Parc Matériel | ⬜ |
| #62 | Capteurs IoT intégrés | ⬜ |
| #63 | Maintenance Prédictive | ⬜ |
| #92 | Réalité Augmentée Maintenance | ⬜ |

**Effort:** 6-8 semaines

---

### PHASE 5 — CROISSANCE & E-COMMERCE (10 tâches) — MOYENNE

| # | Tâche | Statut |
|---|-------|--------|
| #54 | eCommerce intégré | ⬜ |
| #56 | Site Web Builder | ⬜ |
| #59 | POS Restaurant | ⬜ |
| #83 | Module Location/Leasing | ⬜ |
| #57 | Campagnes E-mail Marketing | ⬜ |
| #60 | Campagnes SMS Marketing | ⬜ |
| #58 | Marketing Automation | ⬜ |
| #68 | Marketing Social | ⬜ |
| #45 | Portail Client Self-Service | ⬜ |
| #73 | Segmentation Clients Intelligente | ⬜ |

**Effort:** 8-10 semaines

---

### PHASE 6 — COMMUNICATION & CRM (7 tâches) — NORMALE

| # | Tâche | Statut |
|---|-------|--------|
| #69 | WhatsApp Business | ⬜ |
| #70 | Live Chat Site Web | ⬜ |
| #84 | Discussion/Chat Interne | ⬜ |
| #71 | Extension LinkedIn | ⬜ |
| #72 | Extensions Gmail et Outlook | ⬜ |
| #74 | VOIP intégrée | ⬜ |
| #48 | Import Données Concurrents | ⬜ |

**Effort:** 4-6 semaines

---

### PHASE 7 — MOBILE & APPS (2 tâches) — NORMALE

| # | Tâche | Statut |
|---|-------|--------|
| #46 | App Mobile Native Complète (iOS/Android) | ⬜ |
| #26 | Créer l'app mobile Tap to Pay | ⬜ |

**Effort:** 6-8 semaines

---

### PHASE 8 — AVANCÉ & PERSONNALISATION (6 tâches) — BASSE

| # | Tâche | Statut |
|---|-------|--------|
| #42 | Personnalisation No-Code Formulaires | ⬜ |
| #43 | Automatisations et Workflows | ⬜ |
| #44 | Signature Électronique Intégrée | ⬜ |
| #40 | Tableau de Bord Dirigeant Intelligent | ⬜ |
| #111 | Documentation Technique Complète | ⬜ |
| #112 | Gestion de la Dette Technique | ⬜ |

**Effort:** 6 semaines

---

### PHASE 9 — OPTIONNEL (7 tâches) — OPTIONNEL

| # | Tâche | Statut |
|---|-------|--------|
| #85 | Base de Connaissances/Wiki | ⬜ |
| #86 | Rendez-vous en Ligne | ⬜ |
| #87 | Sondages et Enquêtes | ⬜ |
| #88 | Gestion Événements | ⬜ |
| #91 | Module eLearning | ⬜ |
| #89 | Module Blog | ⬜ |
| #90 | Module Forum | ⬜ |

**Effort:** 6 semaines (si ressources disponibles)

---

### PHASE 10 — PRÉ-PRODUCTION (7 tâches) — CRITIQUE

| # | Tâche | Priorité | Statut |
|---|-------|----------|--------|
| #95 | Tests de Pénétration (Pentest) | CRITIQUE | ⬜ |
| #115 | Monitoring et Alerting Complet | CRITIQUE | ⬜ |
| #114 | Plan de Rollback et Procédures | CRITIQUE | ⬜ |
| #101 | Tests End-to-End (E2E) | HAUTE | ⬜ |
| #102 | Tests de Charge et Performance | HAUTE | ⬜ |
| #116 | Tests de Disaster Recovery | HAUTE | ⬜ |
| #107 | Audit Accessibilité RGAA/WCAG | MOYENNE | ⬜ |

**Effort:** 4-6 semaines

---

### RÉCAPITULATIF

| Phase | Tâches | Effort | Priorité |
|-------|--------|--------|----------|
| 0 | 15 | 5-6 sem | BLOQUANT |
| 0.5 | 7 | 4-6 sem | CRITIQUE |
| 1 | 9 | 8-10 sem | CRITIQUE |
| 2 | 27 | 12-14 sem | HAUTE |
| 2.5 | 3 | 2-3 sem | HAUTE |
| 3 | 16 | 8-10 sem | HAUTE |
| 4 | 9 | 6-8 sem | MOYENNE |
| 5 | 10 | 8-10 sem | MOYENNE |
| 6 | 7 | 4-6 sem | NORMALE |
| 7 | 2 | 6-8 sem | NORMALE |
| 8 | 6 | 6 sem | BASSE |
| 9 | 7 | 6 sem | OPTIONNEL |
| 10 | 7 | 4-6 sem | CRITIQUE |
| **TOTAL** | **123** | **~80-100 sem** | |

---

### TIMELINE

```
2026
├── Février-Mars     │ PHASE 0   │ Fondations
├── Mars-Avril       │ PHASE 0.5 │ Activation Frontend [NOUVEAU]
├── Mai-Juillet      │ PHASE 1   │ Conformité Légale ← DEADLINE 09/2026
├── Août-Octobre     │ PHASE 2   │ Finance Suite
├── Novembre         │ PHASE 2.5 │ Tests & Qualité
├── Nov-Décembre     │ PHASE 10  │ Pré-Production V1
└── Décembre         │ 🚀 V1     │ MISE EN PRODUCTION V1

2027
├── Janvier-Mars     │ PHASE 3   │ Modules Métier
├── Février-Avril    │ PHASE 4   │ Interventions (parallèle)
├── Avril-Juin       │ PHASE 5   │ E-Commerce
├── Juin-Juillet     │ PHASE 10  │ Pré-Production V2
├── Juillet          │ 🚀 V2     │ MISE EN PRODUCTION V2
├── Août-Septembre   │ PHASE 6   │ Communication
├── Octobre-Novembre │ PHASE 7   │ Mobile
├── Décembre         │ PHASE 8   │ Avancé
└── Janvier 2028     │ PHASE 9   │ Optionnel
```

---

**Document de référence complet:** `/home/ubuntu/azalscore/PROMPT_PHASE_CRITIQUE.md`
