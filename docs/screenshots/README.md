# AZALSCORE - Screenshots Documentation

Ce dossier contient les captures d'ecran de l'application AZALSCORE
pour la documentation commerciale et le rapport de valorisation.

## Generation des Screenshots

```bash
# Depuis la racine du projet
./scripts/generate-screenshots.sh

# Ou manuellement
cd frontend
npx playwright test screenshots-docs.spec.ts --project=chromium
```

## Liste des Captures

| Fichier | Description | Usage |
|---------|-------------|-------|
| `01-cockpit-dashboard.png` | Vue complete du cockpit decisional | Page d'accueil rapport |
| `02-strategic-kpis.png` | Section KPIs strategiques | Highlight decisional |
| `03-cockpit-alerts.png` | Panneau d'alertes intelligentes | Fonctionnalite cle |
| `04-bi-module.png` | Module BI avec editeur SQL | Differentiation |
| `05-crm-pipeline.png` | Pipeline commercial CRM | Module metier |
| `06-ventes-module.png` | Gestion devis/factures | Module metier |
| `07-achats-module.png` | Gestion achats | Module metier |
| `08-mobile-cockpit.png` | Vue mobile responsive | Mobilite |
| `09-tablet-cockpit.png` | Vue tablette responsive | Mobilite |
| `10-login-page.png` | Page de connexion | Design moderne |

## Specifications Techniques

- **Resolution desktop**: 1280x720
- **Resolution mobile**: 375x812 (iPhone X)
- **Resolution tablette**: 768x1024 (iPad)
- **Format**: PNG
- **Navigateur**: Chromium (Playwright)

## KPIs Strategiques a Mettre en Evidence

1. **Cash Runway** - Tresorerie restante en mois
2. **Profit Margin** - Marge nette %
3. **Customer Concentration** - Risque dependance clients
4. **Working Capital (BFR)** - Besoin fonds roulement
5. **Employee Productivity** - CA par employe

## Notes pour la Presentation

- Les screenshots doivent montrer des donnees realistes (pas de "Lorem ipsum")
- Privilegier des chiffres business credibles
- Mettre en evidence les indicateurs de couleur (vert/orange/rouge)
- Montrer l'interface en francais

---

*Derniere mise a jour: 2026-02-13*
