## Description

<!-- Decrivez brievement les changements apportes -->

## Type de changement

<!-- Cochez les cases appropriees -->

- [ ] Bug fix (correction non-breaking)
- [ ] New feature (nouvelle fonctionnalite non-breaking)
- [ ] Breaking change (fix ou feature qui casse la compatibilite)
- [ ] Refactoring (pas de changement fonctionnel)
- [ ] Documentation
- [ ] Configuration / DevOps
- [ ] Security fix

## Modules affectes

<!-- Listez les modules modifies -->

- [ ] Core (`app/core/`)
- [ ] IAM / Security (`app/modules/iam/`, `guardian/`)
- [ ] Accounting / Finance (`app/modules/accounting/`, `treasury/`)
- [ ] Commercial / CRM (`app/modules/commercial/`, `contacts/`)
- [ ] Operations (`app/modules/inventory/`, `production/`)
- [ ] AI (`app/modules/ai_assistant/`, `marceau/`)
- [ ] Frontend (`frontend/`)
- [ ] Other: <!-- specifier -->

## Checklist securite

<!-- OBLIGATOIRE pour tout code touchant la securite ou les donnees -->

- [ ] Pas de secrets/credentials hardcodes
- [ ] Validation des entrees utilisateur
- [ ] Queries SQL parametrees (pas de concatenation)
- [ ] Tenant isolation verifiee
- [ ] Permissions/RBAC correctement appliquees
- [ ] Logs sensibles masques (pas de passwords, tokens)
- [ ] CORS configure correctement
- [ ] Rate limiting en place (si endpoint public)

## Tests

<!-- Decrivez les tests effectues -->

- [ ] Tests unitaires ajoutes/mis a jour
- [ ] Tests d'integration ajoutes/mis a jour
- [ ] Tests manuels effectues
- [ ] Coverage maintenu >= 70%

## Documentation

- [ ] README mis a jour si necessaire
- [ ] Docstrings ajoutees aux fonctions publiques
- [ ] CHANGELOG mis a jour
- [ ] API docs (OpenAPI) a jour

## Migration de base de donnees

- [ ] Pas de migration necessaire
- [ ] Migration Alembic creee
- [ ] Migration testee (upgrade + downgrade)
- [ ] Migration reversible

## Captures d'ecran (si UI)

<!-- Ajoutez des captures si pertinent -->

## Notes pour les reviewers

<!-- Indiquez les points d'attention particuliers -->

## Issue liee

<!-- Lien vers l'issue GitHub/Jira -->

Closes #

---

### Checklist finale

- [ ] Code conforme aux standards (ruff, black, isort)
- [ ] Pas de warnings dans les logs
- [ ] PR de taille raisonnable (< 500 lignes idealement)
- [ ] Commits atomiques avec messages clairs
- [ ] Branch a jour avec `develop`
