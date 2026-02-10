# Changelog

All notable changes to AZALSCORE are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
