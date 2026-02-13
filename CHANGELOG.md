# Changelog

All notable changes to AZALSCORE are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-02-13

### Mission 200K - Ameliorations Decisionnelles

Cette version enrichit significativement les capacites decisionnelles d'AZALSCORE
avec de nouveaux KPIs strategiques, un systeme d'audit UI, et des services SEO.

### Added

#### Cockpit - 5 Nouveaux KPIs Strategiques
- **Cash Runway**: Mois de tresorerie disponible avec seuils d'alerte
  - `GET /v1/cockpit/helpers/cash-runway`
- **Profit Margin**: Marge nette % avec benchmark sectoriel
  - `GET /v1/cockpit/helpers/profit-margin`
- **Customer Concentration**: Dependance aux top 3 clients (risque > 50%)
  - `GET /v1/cockpit/helpers/customer-concentration`
- **Working Capital (BFR)**: Besoin en fonds de roulement
  - `GET /v1/cockpit/helpers/working-capital`
- **Employee Productivity**: CA par employe ETP
  - `GET /v1/cockpit/helpers/employee-productivity`
- **All Strategic**: Endpoint unifie
  - `GET /v1/cockpit/helpers/all-strategic`

#### Frontend Cockpit
- Composant `StrategicKPICard` pour affichage des KPIs
- Hook `useStrategicKPIs` avec TanStack Query
- Section KPIs strategiques dans le dashboard
- Styles CSS avec indicateurs de statut colores
- Design responsive mobile-first

#### Audit - UIEvents Tracking
- Modele `UIEvent` pour tracking interactions utilisateur
- Table `ui_events` avec migration Alembic
- `POST /v1/audit/ui-events` - Batch storage
- `GET /v1/audit/ui-events/stats` - Statistiques

#### SEO Service (Module Marceau)
- `generate_article()`: Generation articles SEO optimises
- `publish_wordpress()`: Publication WordPress REST API
- `optimize_meta()`: Optimisation meta tags
- `analyze_rankings()`: Analyse classements mots-cles

#### Transformers Registry
- **text/slugify**: Generation slugs URL-friendly
  - Normalisation unicode (accents francais)
  - Troncature intelligente, separateur configurable
  - 17 tests unitaires (100% pass)

### Documentation
- `docs/business/VALEUR_DECISIONNELLE.md`: Valorisation 200k EUR
- `CHANGELOG.md`: Mise a jour complete

### Fixed
- Renommage `metadata` -> `event_data` dans UIEvent (conflit SQLAlchemy)
- Import corrige dans tests slugify
- Correction syntaxe `{{` -> `{` dans 48 fichiers tests validators
- Correction imports relatifs -> absolus dans tous les tests validators
- **299 tests registry passent** (144 validators + 155 transformers)

---

## [0.5.0-dev] - 2026-02-05

### Added
- **Business Health Checks** (`/health/business/*`)
  - Module health verification for 8 critical modules
  - Database connectivity check
  - Registry manifest counting
  - Complete system diagnostic endpoint

- **E2E Test Suite** (25+ tests)
  - Authentication flows (login, logout)
  - Module navigation tests (purchases, treasury, accounting, invoicing, partners, CRM, stock, HR, interventions)
  - Regression detection (spinners, blank pages, console errors)
  - Form validation and modal behavior tests

- **Shared IA Components** (`@ui/components/shared-ia`)
  - IAPanelHeader, IAScoreCircle, InsightList, SuggestedActionList
  - Migrated all 30 IATab modules to use shared components
  - Reduced code duplication by ~1000 lines

### Changed
- **Documentation reorganized**
  - Moved 98 markdown files from root to `/docs` structure
  - Created organized subdirectories: audits, migration, guides, architecture, sessions
  - Updated README.md with concise project overview

- **Version unified** to 0.5.0-dev across all components
  - pyproject.toml
  - app/core/version.py
  - frontend/package.json

- **Playwright configuration** updated
  - Correct port (5173)
  - 3 parallel workers
  - Webkit browser support
  - Proper timeouts

### Fixed
- **Interventions customer creation** - Added missing 'code' field to CLIENT_CREATE_FIELDS (422 validation error)
- **Frontend race conditions** - Auth state and navigation fixes
- **Infinite spinners** - Eliminated on Devis/Facturation route

## [0.4.0] - 2026-01-30

### Added
- Interventions module with 7-state machine
- Guardian auto-healing system
- Theo AI assistant voice support
- Production observability (Grafana dashboards)

### Changed
- CORE SaaS v2 migration (38/39 modules)
- Multi-tenant isolation improvements

## [0.3.0] - 2026-01-20

### Added
- Complete accounting module
- Treasury management
- Purchases workflow
- CRM T0 implementation

### Changed
- UUID migration for all models
- RBAC matrix implementation

---

For detailed migration guides, see `/docs/migration/`.
For audit reports, see `/docs/audits/`.
