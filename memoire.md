# AZALSCORE - Memoire de Session

## Derniere mise a jour: 2026-02-10

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

---

## Taches en Attente

### TODO: Autocomplete Articles dans Devis/Commandes/Factures
- [ ] Creer composant `ProductAutocomplete` pour recherche d'articles
- [ ] Integrer dans lignes de devis (`/invoicing/quotes`)
- [ ] Integrer dans lignes de commande (`/invoicing/orders`)
- [ ] Integrer dans lignes de facture (`/invoicing/invoices`)
- [ ] Auto-remplir: description, prix unitaire, TVA, code article

### TODO: Notations Credit Internationales
- [x] **Pappers** (France) - IMPLEMENTE (2026-02-10)
  - Cotation Banque de France
  - Procedures collectives
  - Score de risque AZALS (0-100)
  - Fallback vers INSEE si pas de cle API
- [ ] **Configuration Provider Risque** - Permettre de choisir le provider
  - Interface admin pour configurer API keys
  - Selection du provider principal (Pappers, Creditsafe, etc.)
  - Fallback automatique vers provider secondaire
- [ ] **OpenCorporates** - Registres mondiaux (API gratuite limitee)
  - Donnees de base entreprise
  - Statut juridique
- [ ] **Creditsafe / Coface** (payant) - Notation credit internationale
  - Score credit D&B
  - Notation Moody's / S&P / Fitch
- [ ] **VIES** (gratuit) - Validation TVA intracommunautaire
  - Verification numero TVA europeen
  - Nom et adresse de l'entreprise
- [ ] **Kompany** (payant) - Registres europeens
  - Documents officiels
  - Comptes annuels

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
10. `/app/modules/enrichment/schemas.py` - suggestions: list[dict[str, Any]] pour entreprises
11. `/app/modules/purchases/schemas.py` - code: Optional[str] auto-genere

### Frontend (frontend/src/)
1. `/modules/admin/index.tsx` - Hooks, gestion roles, Createur, **UserPermissionsModal**, **UsersPermissionsView**, onglet "Acces Modules"
2. `/modules/admin/types.ts` - Ajout created_by_name dans interface Role
3. `/modules/admin/components/SequencesView.tsx` - Hooks corriges
4. `/ui-engine/simple/PermissionsManager.tsx` - Hooks corriges
5. `/core/capabilities/index.tsx` - Parsing robuste avec logging
6. `/modules/enrichment/` - **NOUVEAU MODULE** CompanyAutocomplete, AddressAutocomplete, SiretLookup, BarcodeLookup
7. `/modules/purchases/index.tsx` - Integration enrichissement, hooks corriges format reponse, code auto-genere

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

### Pour ajouter un nouveau module au menu:

1. Modifier `/frontend/src/components/UnifiedLayout.tsx`:
   - Ajouter la cle dans le type `ViewKey`
   - Ajouter l'entree dans `MENU_ITEMS` avec label, group et capability

2. (Optionnel) Modifier `/frontend/src/ui-engine/menu-dynamic/index.tsx`:
   - Ajouter l'icone dans `ICON_MAP`
   - Ajouter l'entree dans `MENU_SECTIONS`

### Exemple - Ajout Marceau IA (2026-02-09):

```typescript
// UnifiedLayout.tsx - Type ViewKey
| 'cockpit' | 'marceau'

// UnifiedLayout.tsx - MENU_ITEMS
{ key: 'marceau', label: 'Marceau IA', group: 'IA', capability: 'marceau.view' },
```

---

## Principes de Developpement

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
