# Checklist Modules Frontend AZALSCORE

## Verification des modules - A FAIRE A CHAQUE AJOUT DE MODULE

Quand on ajoute un nouveau module backend, il faut s'assurer qu'il est visible dans le frontend.

### 3 fichiers a verifier/modifier:

1. **`frontend/src/components/UnifiedLayout.tsx`**
   - Ajouter le `ViewKey` dans le type (ligne ~32)
   - Ajouter l'item dans `MENU_ITEMS` (ligne ~58)

2. **`frontend/src/UnifiedApp.tsx`**
   - Ajouter l'import lazy du module (ligne ~26)
   - Ajouter le `case` dans le `ViewRenderer` switch (ligne ~166)

3. **`frontend/src/routing/index.tsx`** (pour le mode ERP)
   - Ajouter l'import lazy du module (ligne ~17)
   - Ajouter la `<Route>` avec `CapabilityRoute` (ligne ~120+)

### Commandes de verification:

```bash
# Compter les modules backend
ls /home/ubuntu/azalscore/app/modules/ | wc -l

# Compter les modules frontend
ls /home/ubuntu/azalscore/frontend/src/modules/ | wc -l

# Verifier les ViewKey dans UnifiedLayout
grep "ViewKey" frontend/src/components/UnifiedLayout.tsx

# Verifier les MENU_ITEMS
grep -A 50 "MENU_ITEMS" frontend/src/components/UnifiedLayout.tsx | head -60

# Verifier les lazy imports dans UnifiedApp
grep "lazy.*import" frontend/src/UnifiedApp.tsx

# Verifier les routes
grep "Route path" frontend/src/routing/index.tsx
```

### Build et deploiement:

```bash
cd /home/ubuntu/azalscore/frontend

# 1. Verifier TypeScript
npx tsc --noEmit

# 2. Build
npm run build

# 3. Deployer vers les containers Docker
docker cp dist/. azals_nginx:/usr/share/nginx/html/
docker cp dist/. azals_frontend:/usr/share/nginx/html/

# 4. Recharger nginx
docker exec azals_nginx nginx -s reload
docker exec azals_frontend nginx -s reload
```

### Modules actuellement configures (2026-01-22):

**UnifiedApp (mode azalscore) - 27 modules:**
- saisie, gestion-devis, gestion-commandes, gestion-interventions, gestion-factures, gestion-paiements
- affaires
- crm, stock, achats, projets, rh, vehicules
- production, maintenance, quality
- pos, ecommerce, marketplace, subscriptions
- helpdesk, web, bi, compliance
- compta, tresorerie
- cockpit, admin

**Routing (mode ERP) - 26 routes:**
- cockpit, partners, invoicing, treasury, accounting, purchases, projects
- interventions, web, ecommerce, marketplace, payments, mobile, admin
- hr, crm, stock, production, maintenance, quality
- pos, subscriptions, helpdesk, bi, compliance
- break-glass, profile, settings
