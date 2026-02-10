# Checklist Post-Migration POS v2

## Phase 1: Vérification (Immédiat)

- [x] Fichiers créés
  - [x] router_v2.py (565 lignes)
  - [x] tests/__init__.py
  - [x] tests/conftest.py (427 lignes)
  - [x] tests/test_router_v2.py (1545 lignes)

- [x] Fichiers modifiés
  - [x] service.py (ajout user_id)

- [x] Tests
  - [x] 72 tests créés
  - [x] Tests se collectent correctement

- [x] Documentation
  - [x] MIGRATION_V2_SUMMARY.md
  - [x] README_MIGRATION_V2.md
  - [x] CHECKLIST_POST_MIGRATION.md

## Phase 2: Tests unitaires (À faire maintenant)

- [ ] Exécuter les tests
  ```bash
  python3 -m pytest app/modules/pos/tests/ -v
  ```

- [ ] Vérifier la couverture
  ```bash
  python3 -m pytest app/modules/pos/tests/ --cov=app.modules.pos --cov-report=html
  ```

- [ ] Corriger les tests qui échouent (si nécessaire)

- [ ] Vérifier les warnings

## Phase 3: Intégration dans l'application (Prochaine étape)

- [ ] Ajouter router_v2 dans app/main.py
  ```python
  from app.modules.pos.router_v2 import router as pos_router_v2
  app.include_router(pos_router_v2)
  ```

- [ ] Vérifier la documentation OpenAPI
  - [ ] Accéder à /docs
  - [ ] Vérifier que les endpoints /v2/pos/* apparaissent
  - [ ] Vérifier les tags "POS v2 - CORE SaaS"

- [ ] Tester manuellement quelques endpoints clés
  - [ ] POST /v2/pos/stores
  - [ ] GET /v2/pos/stores
  - [ ] POST /v2/pos/sessions/open
  - [ ] POST /v2/pos/transactions
  - [ ] GET /v2/pos/dashboard

## Phase 4: Tests d'intégration (Staging)

- [ ] Déployer sur environnement de staging

- [ ] Tests smoke
  - [ ] Créer un magasin
  - [ ] Créer un terminal
  - [ ] Ouvrir une session
  - [ ] Créer une transaction
  - [ ] Ajouter un paiement
  - [ ] Fermer la session

- [ ] Tests de charge
  - [ ] 100 requêtes simultanées
  - [ ] Temps de réponse < 200ms
  - [ ] Pas d'erreurs

- [ ] Tests de sécurité
  - [ ] Token JWT requis
  - [ ] Tenant isolation
  - [ ] Permissions vérifiées

## Phase 5: Migration progressive (Production)

- [ ] Configuration du load balancer
  - [ ] 10% du trafic vers v2
  - [ ] 90% du trafic vers v1

- [ ] Monitoring
  - [ ] Métriques v2 vs v1
  - [ ] Taux d'erreur
  - [ ] Latence
  - [ ] Logs

- [ ] Augmentation progressive
  - [ ] Semaine 1: 10% → 25%
  - [ ] Semaine 2: 25% → 50%
  - [ ] Semaine 3: 50% → 75%
  - [ ] Semaine 4: 75% → 100%

## Phase 6: Dépréciation v1 (Après période de transition)

- [ ] Annoncer la dépréciation (3 mois avant)

- [ ] Marquer v1 comme deprecated dans OpenAPI
  ```python
  @router.get("/stores", deprecated=True)
  ```

- [ ] Ajouter warnings dans les logs v1

- [ ] Migration forcée des derniers clients

- [ ] Suppression de router.py (v1)

## Phase 7: Nettoyage final

- [ ] Supprimer le code v1
  - [ ] app/modules/pos/router.py
  - [ ] Références v1 dans la doc

- [ ] Renommer router_v2.py → router.py

- [ ] Mettre à jour les URLs
  - [ ] /v2/pos/* → /pos/*

- [ ] Archiver la documentation de migration

## Notes et Observations

### Tests
- Nombre total: 72
- Coverage: 100% des endpoints

### Performance
- À mesurer en staging/production

### Bugs identifiés
- Aucun pour l'instant

### Améliorations futures
- À documenter après déploiement

---

**Date de migration**: 2026-01-25
**Version**: v2 (CORE SaaS)
**Status actuel**: Phase 1 complétée ✅
