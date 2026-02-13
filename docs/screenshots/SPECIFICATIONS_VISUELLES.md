# AZALSCORE - Specifications Visuelles
## Guide des Captures d'Ecran pour Documentation Commerciale

Ce document decrit precisement le contenu attendu de chaque capture d'ecran
pour le rapport de valorisation 200K.

---

## 01 - Cockpit Dashboard (Vue Complete)

**Fichier**: `01-cockpit-dashboard.png`
**Resolution**: 1280x900 (full page)

**Elements a capturer**:
```
+----------------------------------------------------------+
|  AZALSCORE          [Menu]    [Notifs]    [User: Admin]  |
+----------------------------------------------------------+
|                                                          |
|  +-- KPIs STRATEGIQUES ----------------------------------+
|  |  [Cash Runway]  [Profit Margin]  [Concentration]     |
|  |     8.5 mois       12.3%            28%              |
|  |                                                       |
|  |  [BFR]           [Productivite]                      |
|  |   45,200 EUR        156K EUR/ETP                     |
|  +-------------------------------------------------------+
|                                                          |
|  +-- ALERTES -----------+  +-- DECISIONS RECENTES ------+
|  |  ! Facture #123      |  |  2026-02-13 - Budget Q2   |
|  |    echeance demain   |  |  2026-02-10 - Recrutement |
|  |  ! Client ABC        |  |  2026-02-08 - Partenariat |
|  |    concentration     |  +----------------------------+
|  +----------------------+                                |
|                                                          |
|  +-- ACTIVITE RECENTE -----------------------------------+
|  |  [Devis #456 cree]  [Facture #123 validee]           |
|  |  [Client XYZ ajoute] [Commande #789 recue]           |
|  +-------------------------------------------------------+
+----------------------------------------------------------+
```

**Points d'attention**:
- Mettre en evidence les couleurs des KPIs (vert/orange/rouge)
- Donnees realistes et coherentes
- Interface en francais

---

## 02 - KPIs Strategiques (Zoom)

**Fichier**: `02-strategic-kpis.png`
**Resolution**: 1200x400 (section)

**Elements a capturer**:
```
+----------------------------------------------------------+
|  KPIs Strategiques                                        |
+----------------------------------------------------------+
|                                                          |
|  +-------------+  +-------------+  +------------------+  |
|  | CASH RUNWAY |  | PROFIT      |  | CONCENTRATION    |  |
|  |             |  | MARGIN      |  | CLIENT           |  |
|  |   8.5       |  |   12.3%     |  |    28%           |  |
|  |   mois      |  |             |  |                  |  |
|  | [VERT]      |  | [ORANGE]    |  | [VERT]           |  |
|  +-------------+  +-------------+  +------------------+  |
|                                                          |
|  +-------------+  +------------------+                   |
|  | BFR         |  | PRODUCTIVITE     |                   |
|  |             |  | EMPLOYE          |                   |
|  |  45,200 EUR |  |   156,000 EUR    |                   |
|  |             |  |   par ETP        |                   |
|  | [BLEU]      |  | [VERT]           |                   |
|  +-------------+  +------------------+                   |
+----------------------------------------------------------+
```

**Valeurs de demonstration recommandees**:
| KPI | Valeur | Couleur | Signification |
|-----|--------|---------|---------------|
| Cash Runway | 8.5 mois | Orange | Attention requise |
| Profit Margin | 12.3% | Vert | Bon pour services |
| Concentration | 28% | Vert | Bien diversifie |
| BFR | 45,200 EUR | Bleu | Neutre |
| Productivite | 156K EUR | Vert | Au-dessus moyenne |

---

## 03 - Panneau Alertes

**Fichier**: `03-cockpit-alerts.png`
**Resolution**: 400x500 (panel)

**Elements a capturer**:
```
+--------------------------------+
|  ALERTES (3)          [Voir +] |
+--------------------------------+
|                                |
|  [!] CRITIQUE                  |
|  Facture #2024-0156            |
|  Echeance: demain              |
|  Client: Dupont SA             |
|  Montant: 12,450 EUR           |
|  [Acquitter]                   |
+--------------------------------+
|  [!] ATTENTION                 |
|  Concentration client          |
|  ABC Corp represente 35%       |
|  du CA mensuel                 |
|  [Voir details]                |
+--------------------------------+
|  [i] INFO                      |
|  Objectif mensuel              |
|  85% atteint (127K/150K)       |
|  [Dashboard]                   |
+--------------------------------+
```

---

## 04 - Module BI

**Fichier**: `04-bi-module.png`
**Resolution**: 1280x720

**Elements a capturer**:
```
+----------------------------------------------------------+
|  Business Intelligence          [Nouveau]  [Mes rapports] |
+----------------------------------------------------------+
|  +-- Editeur SQL ----------------+  +-- Resultats ------+ |
|  | SELECT                        |  |                   | |
|  |   client_name,                |  | Client    | CA    | |
|  |   SUM(amount) as total_ca     |  |-----------|-------| |
|  | FROM invoices                 |  | Dupont SA | 45K   | |
|  | WHERE date >= '2026-01-01'    |  | ABC Corp  | 38K   | |
|  | GROUP BY client_name          |  | XYZ Ltd   | 32K   | |
|  | ORDER BY total_ca DESC        |  | Martin    | 28K   | |
|  | LIMIT 10;                     |  | Tech Plus | 25K   | |
|  |                               |  |                   | |
|  | [Executer]  [Sauvegarder]     |  +-------------------+ |
|  +-------------------------------+                        |
|                                                          |
|  +-- Visualisation --------------------------------------+ |
|  |  [Graphique barres: Top 10 clients par CA]            | |
|  |  ██████████ Dupont SA                                 | |
|  |  ████████ ABC Corp                                    | |
|  |  ██████ XYZ Ltd                                       | |
|  +-------------------------------------------------------+ |
+----------------------------------------------------------+
```

---

## 05 - CRM Pipeline

**Fichier**: `05-crm-pipeline.png`
**Resolution**: 1280x720

**Elements a capturer**:
```
+----------------------------------------------------------+
|  CRM - Pipeline Commercial      [+ Nouveau]  [Filtres]    |
+----------------------------------------------------------+
|                                                          |
|  PROSPECT     | QUALIFIE    | PROPOSITION | NEGOCIATION  |
|  (5 - 45K)    | (3 - 78K)   | (2 - 120K)  | (1 - 85K)    |
+----------------------------------------------------------+
|  +----------+ | +----------+ | +----------+ | +----------+|
|  | Tech Pro | | | Dupont   | | | Martin   | | | ABC Corp ||
|  | 15K EUR  | | | 35K EUR  | | | 75K EUR  | | | 85K EUR  ||
|  | J-3      | | | J+2      | | | J+5      | | | J+10     ||
|  +----------+ | +----------+ | +----------+ | +----------+|
|  | Innov SA | | | XYZ Ltd  | | | Retail+  | |            |
|  | 12K EUR  | | | 28K EUR  | | | 45K EUR  | |            |
|  | J-1      | | | J+7      | | |          | |            |
|  +----------+ | +----------+ | +----------+ |            |
|  | ...      | | | Future   | |            | |            |
+----------------------------------------------------------+
|  Total Pipeline: 328,000 EUR   Taux conversion: 32%      |
+----------------------------------------------------------+
```

---

## 06 - Module Ventes

**Fichier**: `06-ventes-module.png`
**Resolution**: 1280x720

**Elements a capturer**:
- Liste des devis/factures recentes
- Statuts colores (brouillon, envoye, paye)
- Montants et dates
- Actions rapides (voir, dupliquer, transformer)

---

## 07 - Module Achats

**Fichier**: `07-achats-module.png`
**Resolution**: 1280x720

**Elements a capturer**:
- Liste des commandes fournisseurs
- Statuts de reception
- Montants engages

---

## 08 - Vue Mobile

**Fichier**: `08-mobile-cockpit.png`
**Resolution**: 375x812 (iPhone X)

**Elements a capturer**:
```
+------------------+
| AZALSCORE   [=]  |
+------------------+
|                  |
| KPIs Strategiques|
| +------+ +------+|
| |8.5   | |12.3% ||
| |mois  | |      ||
| +------+ +------+|
| +------+ +------+|
| |28%   | |45K   ||
| |      | |EUR   ||
| +------+ +------+|
|                  |
| Alertes (3)      |
| +---------------+|
| | ! Facture     ||
| |   echeance    ||
| +---------------+|
|                  |
+------------------+
| [Home] [+] [Menu]|
+------------------+
```

---

## 09 - Vue Tablette

**Fichier**: `09-tablet-cockpit.png`
**Resolution**: 768x1024 (iPad)

**Elements a capturer**:
- Layout 2 colonnes pour KPIs
- Alertes en sidebar
- Navigation simplifiee

---

## 10 - Page Login

**Fichier**: `10-login-page.png`
**Resolution**: 1280x720

**Elements a capturer**:
```
+----------------------------------------------------------+
|                                                          |
|                    [Logo AZALSCORE]                      |
|                                                          |
|              Connectez-vous a votre espace               |
|                                                          |
|              +----------------------------+              |
|              | Email                      |              |
|              | admin@entreprise.com       |              |
|              +----------------------------+              |
|              | Mot de passe               |              |
|              | ************************   |              |
|              +----------------------------+              |
|              [        Se connecter        ]              |
|                                                          |
|              [ ] Se souvenir de moi                      |
|              Mot de passe oublie ?                       |
|                                                          |
|              --------------------------------            |
|              ERP Decisionnel pour PME                    |
|              Version 0.6.0                               |
+----------------------------------------------------------+
```

---

## Instructions de Generation

### Methode 1: Script Automatise

```bash
# Configurer les variables
export TEST_USER_EMAIL="admin@entreprise.com"
export TEST_USER_PASSWORD="motdepasse"
export BASE_URL="https://azalscore.com"

# Executer
./scripts/generate-screenshots.sh
```

### Methode 2: Playwright Direct

```bash
cd frontend
npx playwright test screenshots-docs.spec.ts --project=chromium
```

### Methode 3: Capture Manuelle

1. Se connecter a https://azalscore.com
2. Naviguer vers chaque ecran
3. Utiliser l'outil de capture du navigateur (F12 > Device Mode)
4. Sauvegarder dans `docs/screenshots/`

---

## Checklist Finale

- [ ] 01-cockpit-dashboard.png (1280x900)
- [ ] 02-strategic-kpis.png (1200x400)
- [ ] 03-cockpit-alerts.png (400x500)
- [ ] 04-bi-module.png (1280x720)
- [ ] 05-crm-pipeline.png (1280x720)
- [ ] 06-ventes-module.png (1280x720)
- [ ] 07-achats-module.png (1280x720)
- [ ] 08-mobile-cockpit.png (375x812)
- [ ] 09-tablet-cockpit.png (768x1024)
- [ ] 10-login-page.png (1280x720)

---

*Document genere le 2026-02-13*
