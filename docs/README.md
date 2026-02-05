# Documentation AZALSCORE

> Index de la documentation technique et fonctionnelle

**Date**: 2026-02-05
**Version**: 0.5.0-dev

## Structure

### [guides/](guides/)
Documentation pour demarrer et developper sur AZALSCORE.
- Demarrage rapide et setup environnement
- Conventions de code et standards
- Routines developpeur
- Plans d'implementation
- Tests et qualite

### [architecture/](architecture/)
Decisions techniques et patterns du projet.
- Architecture multi-tenant
- Patterns CORE SaaS v2
- Conformite et standards
- Variables et configuration

### [migration/](migration/)
Etat de la migration vers l'architecture v2.
- Checklist migration par module
- Code reviews et priorites
- Rapports d'avancement

### [audits/](audits/)
Rapports d'analyse et historique des sessions.
- Audits fonctionnels
- Rapports de session
- Analyses critiques
- Syntheses de corrections

### [sessions/](sessions/)
Historique des corrections et deploiements.
- Fixes et corrections
- Deployments
- Scope et verrous

### [modules/](modules/)
Documentation specifique par module metier.

### [runbooks/](runbooks/)
Procedures operationnelles et DR.

## Fichiers racine docs/

| Fichier | Description |
|---------|-------------|
| AUTHENTICATION.md | Guide authentification et JWT |
| HTTP_ERROR_HANDLING.md | Gestion des erreurs HTTP |
| AI_ORCHESTRATION_SYSTEM.md | Architecture IA (Theo/Guardian) |
| DR_PLAN.md | Plan de reprise d'activite |

## Conventions

- Tous les nouveaux documents vont dans le dossier approprie
- Nommage: `SUJET_DETAIL.md` en majuscules
- Date en en-tete si document versionne
- Liens relatifs entre documents
