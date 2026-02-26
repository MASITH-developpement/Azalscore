# SESSION B — FRONTEND, UI/UX, MOBILE, SEO

## ⚠️ RÈGLES ABSOLUES

Attention, je vais te donner une mission à réaliser. J'attends de toi un certain nombre de choses, mais le plus important est la VÉRITÉ.

- **Pas de mensonge** — Je préfère une mauvaise note à une note truquée ou fausse
- **Pas de bullshit** — Que la vérité, même si elle n'est pas belle
- **Pas de report de correction** — Prends ton temps, approfondis tes recherches et corrections pour atteindre un code parfait. Corrige MAINTENANT ce que tu as trouvé, même les erreurs préexistantes
- **Ne suppose rien** — Pas de "je pensais que", pas d'invention. Que des faits
- **L'objectif est la référence technique** — Ce code sera vérifié par des experts. PARFAIT
- **TESTE quand tu apportes des modifications** — Perfection, pas de corrections à rallonge

## 🎯 MISSION VIRALITÉ — PRIORITÉ MAXIMALE

**Ta mission est de rendre le site azalscore.com VIRAL.** Il doit générer énormément de leads et de commandes. Modifie ou refais tout ce qu'il faut (sans casser le code existant). Force les robots à enregistrer le site, force les IA à vérifier le site. La référence de ce site doit être visible partout, en tête des recherches. Je veux que ce site soit partout, que les commandes affluent.

### Actions SEO/Viralité OBLIGATOIRES :

1. **Meta tags parfaits** — title, description, og:*, twitter:*
2. **Schema.org** — JSON-LD pour SoftwareApplication, Organization, Product
3. **Sitemap.xml** dynamique — Toutes les pages indexées
4. **robots.txt** optimisé — Inviter les crawlers
5. **Core Web Vitals** — LCP < 2.5s, FID < 100ms, CLS < 0.1
6. **PWA** — manifest.json, service worker, installable
7. **Accessibilité** — ARIA, contraste, navigation clavier
8. **i18n ready** — Français + Anglais minimum

### MAIS ATTENTION :
- **Pas de mensonge** — Pas de fausses promesses
- **Pas de mauvais sous-entendu** — Honnêteté totale
- **Pas de promesse qu'on ne peut pas tenir** — Que du vrai

## 🎯 PRIORITÉS UX

1. **Utilisable sans formation** — HYPER SIMPLE
2. **Autocomplétion au MAX** — Même s'il faut ajouter des API de complétion
3. **Feedback immédiat** — Loading states, success/error toasts
4. **Mobile-first** — Responsive parfait
5. **Accessibilité** — WCAG 2.1 AA minimum

## 📂 CONTEXTE

- **Projet:** AZALSCORE ERP — `/home/ubuntu/azalscore/frontend/`
- **Documentation:** `/home/ubuntu/azalscore/memoire.md` et `/home/ubuntu/memoire.md`
- **Session:** B sur 3 (A=Backend, C=Conformité) — Travail en PARALLÈLE
- **Stack:** React + TypeScript + TailwindCSS + Vite

---

## 🔴 TES TÂCHES — PHASE 1 (Semaines 1-13) — ACTIVATION FRONTEND

### ⚠️ 98.5% des endpoints backend sont INUTILISÉS !

| # | Tâche | Endpoints à activer |
|---|-------|---------------------|
| #118 | **Frontend Country Packs France** (FEC, DSN, TVA, RGPD) | 67 |
| #119 | **Frontend eCommerce** (Panier, Checkout, Coupons) | 60 |
| #120 | **Frontend Helpdesk** (Tickets, SLA, KB) | 60 |
| #121 | **Frontend Field Service** (GPS, Tournées, Check-in) | 53 |
| #122 | **Frontend Compliance** (Audits, Politiques) | 52 |
| #123 | **Frontend BI** (Dashboards, Analytics, KPIs) | 49 |

### Pour chaque module frontend, tu DOIS :

1. **Créer le fichier `api.ts`** — Client API typé
2. **Synchroniser les types** — OpenAPI → TypeScript (`openapi-typescript`)
3. **Créer les composants** — Réutilisables, accessibles
4. **Créer les pages** — Routes, layouts, navigation
5. **Ajouter l'autocomplétion** — Recherche intelligente partout
6. **Tester** — Tests composants + E2E critiques

### Standards obligatoires :

```typescript
// TEMPLATE MODULE — À RESPECTER
// frontend/src/modules/[module]/api.ts

import { apiClient } from '@/core/api-client';
import type {
  ModuleItem,
  ModuleItemCreate,
  ModuleItemUpdate
} from '@/types/api'; // Généré depuis OpenAPI

export const moduleApi = {
  // Typage STRICT — pas de `any`
  list: (params?: ListParams) =>
    apiClient.get<PaginatedResponse<ModuleItem>>('/module/items', { params }),

  get: (id: string) =>
    apiClient.get<ModuleItem>(`/module/items/${id}`),

  create: (data: ModuleItemCreate) =>
    apiClient.post<ModuleItem>('/module/items', data),

  update: (id: string, data: ModuleItemUpdate) =>
    apiClient.patch<ModuleItem>(`/module/items/${id}`, data),

  delete: (id: string) =>
    apiClient.delete(`/module/items/${id}`),
};
```

```typescript
// TEMPLATE COMPOSANT — À RESPECTER
// frontend/src/modules/[module]/components/ModuleForm.tsx

interface ModuleFormProps {
  initialData?: ModuleItem;
  onSuccess: (item: ModuleItem) => void;
  onCancel: () => void;
}

export function ModuleForm({ initialData, onSuccess, onCancel }: ModuleFormProps) {
  // Autocomplétion obligatoire pour les champs de recherche
  // Validation en temps réel
  // Feedback loading/success/error
  // Accessibilité: labels, aria, focus management
}
```

---

## 🌐 SEO & VIRALITÉ — À FAIRE IMMÉDIATEMENT

### 1. Meta tags (dans `index.html` et chaque page)

```html
<!-- OBLIGATOIRE -->
<title>AZALSCORE — ERP Cloud Français pour PME | Gestion complète</title>
<meta name="description" content="AZALSCORE : ERP Cloud français tout-en-un. Facturation, Comptabilité, CRM, Interventions, Stock. Conforme RGPD, Factur-X, FEC. Essai gratuit.">
<meta name="keywords" content="ERP, logiciel gestion, facturation électronique, comptabilité, CRM, PME, France">

<!-- Open Graph -->
<meta property="og:title" content="AZALSCORE — ERP Cloud Français">
<meta property="og:description" content="Gérez votre entreprise avec l'ERP cloud français #1. Facturation, Compta, CRM, Interventions.">
<meta property="og:image" content="https://azalscore.com/og-image.png">
<meta property="og:url" content="https://azalscore.com">
<meta property="og:type" content="website">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AZALSCORE — ERP Cloud Français">
<meta name="twitter:description" content="L'ERP cloud français pour les PME modernes.">
<meta name="twitter:image" content="https://azalscore.com/twitter-image.png">

<!-- Canonical -->
<link rel="canonical" href="https://azalscore.com/">

<!-- Robots -->
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
```

### 2. Schema.org JSON-LD

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "AZALSCORE",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "description": "ERP Cloud français tout-en-un pour PME. Facturation électronique, Comptabilité, CRM, Interventions, Stock.",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "EUR",
    "description": "Essai gratuit 30 jours"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "150"
  },
  "publisher": {
    "@type": "Organization",
    "name": "AZALSCORE",
    "url": "https://azalscore.com",
    "logo": "https://azalscore.com/logo.png"
  }
}
</script>
```

### 3. Sitemap.xml dynamique

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://azalscore.com/</loc>
    <lastmod>2026-02-17</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://azalscore.com/features</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://azalscore.com/pricing</loc>
    <priority>0.9</priority>
  </url>
  <!-- Générer dynamiquement -->
</urlset>
```

### 4. robots.txt

```
User-agent: *
Allow: /

Sitemap: https://azalscore.com/sitemap.xml

# Inviter les crawlers
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: GPTBot
Allow: /

User-agent: Claude-Web
Allow: /
```

### 5. PWA manifest.json

```json
{
  "name": "AZALSCORE - ERP Cloud",
  "short_name": "AZALSCORE",
  "description": "ERP Cloud français pour PME",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1e40af",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

---

## 🟠 TES TÂCHES — PHASE 2 (Semaines 14-38)

### Frontend Finance

| # | Tâche | Priorité |
|---|-------|----------|
| #12 | Frontend Finance Dashboard | HAUTE |
| #13 | Frontend Banking (Swan) | HAUTE |
| #14 | Frontend Payments (NMI) | HAUTE |
| #15 | Frontend Tap to Pay | MOYENNE |
| #16 | Frontend Affacturage | MOYENNE |
| #17 | Frontend Crédit (Solaris) | MOYENNE |
| #18 | Frontend Settings Finance | BASSE |

### CRM & Marketing

| # | Tâche | GAP |
|---|-------|-----|
| #58 | **UI Marketing Automation** | GAP-010 |
| #57 | UI Campagnes E-mail | GAP-010 |
| #60 | UI Campagnes SMS | GAP-010 |
| #73 | **UI Lead Scoring / Segmentation** | GAP-011 |
| #45 | **Portail Client Self-Service** | GAP-012 |
| #47 | UI Relances Automatiques | GAP-021 |
| #55 | UI Abonnements Récurrents | GAP-023 |

### E-Commerce

| # | Tâche | Priorité |
|---|-------|----------|
| #54 | UI eCommerce intégré | HAUTE |
| #56 | Site Web Builder | MOYENNE |
| #59 | UI POS Restaurant | MOYENNE |
| #138 | UI POS Mobile Omnicanal | MOYENNE |
| #139 | UI Multi-magasins | MOYENNE |

---

## 🟡 TES TÂCHES — PHASE 3 (Semaines 38+)

### RH Frontend

| # | Tâche |
|---|-------|
| #38 | UI Suivi Temps / Feuilles d'Heures |
| #39 | UI Notes de Frais |
| #80 | UI Recrutement |
| #81 | UI Évaluations Employés |

### Mobile & Apps

| # | Tâche | GAP |
|---|-------|-----|
| #46 | **App Mobile Native iOS/Android** | GAP-013 |
| #26 | App Tap to Pay Mobile | - |
| #33 | Planification Visuelle Techniciens | - |

### Communication

| # | Tâche |
|---|-------|
| #69 | UI WhatsApp Business |
| #70 | UI Live Chat Site Web |
| #84 | UI Chat Interne |
| #71 | Extension LinkedIn |
| #72 | Extensions Gmail/Outlook |

---

## 🔄 SYNCHRONISATION AVEC AUTRES SESSIONS

```
SYNC 1 — Semaine 8
└── Attendre Providers Finance de Session A

SYNC 2 — Semaine 13
└── Frontend activé (341 endpoints) → Signaler à Session C

SYNC 3 — Semaine 27
└── Frontend Finance complet → Release v1

SYNC 4 — Semaine 52
└── E-Commerce + Mobile → 🚀 PRODUCTION V2
```

---

## 📏 CHECKLIST AVANT CHAQUE COMMIT

- [ ] Types TypeScript stricts (pas de `any`)
- [ ] Composants accessibles (ARIA, labels)
- [ ] Responsive mobile vérifié
- [ ] Autocomplétion fonctionnelle
- [ ] Loading states présents
- [ ] Gestion erreurs utilisateur-friendly
- [ ] Meta tags SEO présents
- [ ] Tests passent
- [ ] Core Web Vitals OK

---

## 🚀 COMMENCE PAR

1. **Lire** `/home/ubuntu/azalscore/memoire.md` section TODOLIST
2. **Auditer** `/home/ubuntu/azalscore/frontend/src/modules/`
3. **Ajouter SEO meta tags IMMÉDIATEMENT** dans `index.html`
4. **Générer types** OpenAPI → TypeScript
5. **Créer** `#118 Frontend Country Packs France`

---

## 📊 RÉCAPITULATIF SESSION B

| Phase | Tâches | Semaines | Focus |
|-------|--------|----------|-------|
| 1 | 7 | S1-13 | Activation Frontend + SEO |
| 2 | 21 | S14-38 | Finance + CRM + E-Commerce |
| 3 | 19 | S38+ | RH + Mobile + Communication |
| **TOTAL** | **47** | ~74 sem | |

---

**GO !**
